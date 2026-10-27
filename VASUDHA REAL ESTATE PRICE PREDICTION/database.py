"""
Vasudha Real Estate — Database Layer (MongoDB & SQLite Hybrid Engine)
Seamlessly connects to MongoDB (default) with automatic fallback to SQLite.
Handles schema/index definition, CRUD operations for users, localities,
and multi-year historical trend points.
"""

import os
import sys
import re
import sqlite3
import json
from datetime import datetime, timezone

def re_escape(s):
    """Safely escape strings for regex queries."""
    return re.escape(str(s or ""))

# Optional PyMongo import with graceful degradation
try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration & Engine Detection
# ---------------------------------------------------------------------------
DB_ENGINE_CONFIG = os.environ.get("DB_ENGINE", "mongodb").strip().lower()
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/").strip()
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "vasudha_real_estate").strip()
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "vasudha.db")

_mongo_client = None
_mongo_db = None
_active_engine = None  # "mongodb" or "sqlite"


def get_mongo_db():
    """Return MongoDB database handle if available and connected."""
    global _mongo_client, _mongo_db, _active_engine
    if not PYMONGO_AVAILABLE:
        return None

    if _mongo_db is not None:
        return _mongo_db

    try:
        # Connect with a 2-second timeout to avoid blocking on startup
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
        # Test connection with a ping
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[MONGO_DB_NAME]
        _active_engine = "mongodb"
        return _mongo_db
    except Exception as e:
        print(f"[Database Notice] MongoDB connection to '{MONGO_URI}' not active ({e}). Using SQLite fallback.")
        _mongo_client = None
        _mongo_db = None
        _active_engine = "sqlite"
        return None


def is_mongodb_active():
    """Check if MongoDB is actively selected and connected."""
    if DB_ENGINE_CONFIG == "sqlite":
        return False
    return get_mongo_db() is not None


def get_active_engine_name():
    """Return friendly name of currently active database engine."""
    if is_mongodb_active():
        return f"MongoDB ({MONGO_DB_NAME} @ {MONGO_URI})"
    return f"SQLite ({SQLITE_DB_PATH})"


# ---------------------------------------------------------------------------
# SQLite Helpers
# ---------------------------------------------------------------------------

def get_sqlite_connection():
    """Return a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_sqlite_tables():
    """Initialize SQLite database tables as fallback/backup."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            surname TEXT,
            age INTEGER,
            phone TEXT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    # Deduplicate existing legacy rows if any before creating unique index
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone 
            ON users(phone) 
            WHERE phone IS NOT NULL AND phone != '';
        """)
    except sqlite3.IntegrityError:
        # If existing test records have duplicate phones, keep the latest one per phone
        cursor.execute("""
            DELETE FROM users 
            WHERE id NOT IN (
                SELECT MAX(id) FROM users GROUP BY phone
            ) AND phone IS NOT NULL AND phone != '';
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone 
            ON users(phone) 
            WHERE phone IS NOT NULL AND phone != '';
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS localities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            zone TEXT NOT NULL,
            tier TEXT NOT NULL,
            rate_per_sqyd REAL NOT NULL,
            rate_per_sqft REAL NOT NULL,
            yoy_percent REAL,
            projected_5yr REAL,
            note TEXT,
            landmarks TEXT,
            schools_hospitals TEXT,
            transit TEXT,
            livability_score REAL,
            data_source TEXT,
            price_explanation_en TEXT,
            price_explanation_hi TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            locality_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            rate_per_sqft REAL NOT NULL,
            rate_per_sqyd REAL NOT NULL,
            source TEXT,
            UNIQUE(locality_name, year)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS builder_enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT,
            scheme_name TEXT,
            buyer_name TEXT,
            phone TEXT,
            email TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS builder_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            builder_name TEXT,
            project_name TEXT,
            locality TEXT,
            property_type TEXT,
            price_range TEXT,
            rera_id TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            brochure_url TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS builder_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            builder TEXT NOT NULL,
            builder_tagline TEXT,
            locality TEXT NOT NULL,
            zone TEXT,
            property_type TEXT NOT NULL,
            tag TEXT,
            badge_color TEXT,
            rera_id TEXT,
            price_min REAL,
            price_max REAL,
            price_display TEXT,
            config_display TEXT,
            area_range TEXT,
            possession TEXT,
            units_available INTEGER,
            summary TEXT,
            amenities TEXT,
            specs TEXT,
            floor_plans TEXT,
            payment_plan TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            site_address TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# MongoDB Indexes & Auto-Migration
# ---------------------------------------------------------------------------

def _get_next_sequence(sequence_name):
    """Generate atomic auto-increment integer ID in MongoDB."""
    db = get_mongo_db()
    if db is None:
        return 1
    counter = db["counters"].find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return counter["seq"]


def _init_mongo_indexes():
    """Initialize MongoDB collections, indexes, and unique constraints."""
    db = get_mongo_db()
    if db is None:
        return

    # 1. Users indexes
    db["users"].create_index([("email", ASCENDING)], unique=True)
    db["users"].create_index([("username", ASCENDING)], unique=True)
    db["users"].create_index([("phone", ASCENDING)], unique=True, sparse=True)
    db["users"].create_index([("id", ASCENDING)], unique=True)

    # 2. Localities index
    db["localities"].create_index([("name", ASCENDING)], unique=True)
    db["localities"].create_index([("zone", ASCENDING)])

    # 3. Historical Trends compound index
    db["historical_trends"].create_index(
        [("locality_name", ASCENDING), ("year", ASCENDING)],
        unique=True
    )

    # 4. Price Explanations index
    db["price_explanations"].create_index([("locality_name", ASCENDING)], unique=True)


def migrate_sqlite_to_mongodb(verbose=True):
    """Migrate all data from SQLite database file into MongoDB."""
    db = get_mongo_db()
    if db is None:
        if verbose:
            print("[Migration Error] Cannot migrate: MongoDB is not connected.")
        return False

    if not os.path.exists(SQLITE_DB_PATH):
        if verbose:
            print(f"[Migration Notice] No SQLite file found at {SQLITE_DB_PATH}.")
        return False

    _init_mongo_indexes()

    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # Migrate Users
        cursor.execute("SELECT * FROM users ORDER BY id ASC")
        users = [dict(r) for r in cursor.fetchall()]
        user_migrated = 0
        max_user_id = 0
        for u in users:
            uid = int(u["id"])
            if uid > max_user_id:
                max_user_id = uid
            existing = db["users"].find_one({"$or": [{"email": u["email"].lower().strip()}, {"username": u["username"].strip()}]})
            if not existing:
                doc = {
                    "id": uid,
                    "first_name": u.get("first_name", ""),
                    "surname": u.get("surname", ""),
                    "age": u.get("age"),
                    "phone": u.get("phone", ""),
                    "email": u["email"].lower().strip(),
                    "username": u["username"].strip(),
                    "password_hash": u["password_hash"],
                    "created_at": u.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    "updated_at": u.get("updated_at") or datetime.now(timezone.utc).isoformat()
                }
                db["users"].insert_one(doc)
                user_migrated += 1

        # Synchronize counter sequence for users
        if max_user_id > 0:
            db["counters"].update_one(
                {"_id": "user_id"},
                {"$set": {"seq": max_user_id}},
                upsert=True
            )

        # Migrate Localities
        cursor.execute("SELECT * FROM localities")
        locs = [dict(r) for r in cursor.fetchall()]
        loc_migrated = 0
        for l in locs:
            name = l["name"].strip()
            db["localities"].update_one(
                {"name": name},
                {"$set": {
                    "name": name,
                    "zone": l.get("zone", ""),
                    "tier": l.get("tier", ""),
                    "rate_per_sqyd": float(l.get("rate_per_sqyd", 0)),
                    "rate_per_sqft": float(l.get("rate_per_sqft", 0)),
                    "yoy_percent": float(l["yoy_percent"]) if l.get("yoy_percent") is not None else None,
                    "projected_5yr": float(l["projected_5yr"]) if l.get("projected_5yr") is not None else None,
                    "note": l.get("note", ""),
                    "landmarks": l.get("landmarks", ""),
                    "schools_hospitals": l.get("schools_hospitals", ""),
                    "transit": l.get("transit", ""),
                    "livability_score": float(l["livability_score"]) if l.get("livability_score") is not None else None,
                    "data_source": l.get("data_source", ""),
                    "updated_at": l.get("updated_at") or datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            loc_migrated += 1

        # Migrate Historical Trends
        cursor.execute("SELECT * FROM historical_trends")
        trends = [dict(r) for r in cursor.fetchall()]
        trend_migrated = 0
        for t in trends:
            loc_name = t["locality_name"].strip()
            year = int(t["year"])
            db["historical_trends"].update_one(
                {"locality_name": loc_name, "year": year},
                {"$set": {
                    "locality_name": loc_name,
                    "year": year,
                    "rate_per_sqft": float(t.get("rate_per_sqft", 0)),
                    "rate_per_sqyd": float(t.get("rate_per_sqyd", 0)),
                    "source": t.get("source", "")
                }},
                upsert=True
            )
            trend_migrated += 1

        conn.close()
        if verbose:
            print(f"[MongoDB Migration Complete] {user_migrated} new users, {loc_migrated} localities, {trend_migrated} trends synchronized to MongoDB.")
        return True
    except Exception as e:
        if verbose:
            print(f"[Migration Error] Failed to migrate SQLite to MongoDB: {e}")
        return False


def sync_price_explanations_to_mongodb():
    """Sync all bilingual price explanations from backend catalog to MongoDB collection."""
    if not is_mongodb_active():
        return
    db = get_mongo_db()
    if db is None:
        return
    try:
        import backend
        now = datetime.now(timezone.utc).isoformat()
        for loc_name, data in getattr(backend, "LOCALITY_PRICE_EXPLANATIONS", {}).items():
            db["price_explanations"].update_one(
                {"locality_name": loc_name},
                {"$set": {
                    "locality_name": loc_name,
                    "explanation_en": data.get("explanation_en", ""),
                    "explanation_hi": data.get("explanation_hi", ""),
                    "price_drivers": data.get("price_drivers", []),
                    "updated_at": now
                }},
                upsert=True
            )
            # Also update into localities collection
            db["localities"].update_one(
                {"name": loc_name},
                {"$set": {
                    "price_explanation_en": data.get("explanation_en", ""),
                    "price_explanation_hi": data.get("explanation_hi", ""),
                    "price_drivers": data.get("price_drivers", []),
                    "updated_at": now
                }}
            )
    except Exception as e:
        print(f"[MongoDB Sync Notice] Price explanation sync skipped: {e}")


def get_price_explanation(locality_name):
    """Retrieve bilingual price explanation from MongoDB (or SQLite)."""
    clean = (locality_name or "").strip()
    if not clean:
        return None

    if is_mongodb_active():
        db = get_mongo_db()
        doc = db["price_explanations"].find_one({"locality_name": {"$regex": f"^{re_escape(clean)}$", "$options": "i"}})
        if doc:
            return _sanitize_mongo_doc(doc)

    return None


def init_db():
    """Initialize database tables, MongoDB collections, indexes, and initial data."""
    # Always ensure SQLite schema exists as fallback
    _init_sqlite_tables()

    if is_mongodb_active():
        db = get_mongo_db()
        _init_mongo_indexes()

        # Check if MongoDB is empty and sync from SQLite if available
        user_count = db["users"].count_documents({})
        loc_count = db["localities"].count_documents({})

        if loc_count == 0:
            if os.path.exists(SQLITE_DB_PATH):
                migrate_sqlite_to_mongodb(verbose=False)
            else:
                # Fallback to seeder if sqlite db is not present
                try:
                    import seed_data
                    seed_data.seed()
                except Exception:
                    pass

        # Sync bilingual price explanations to MongoDB
        sync_price_explanations_to_mongodb()
        seed_builder_schemes_if_empty()

        print(f"[Database Active] Connected to MongoDB database '{MONGO_DB_NAME}' at {MONGO_URI}")
    else:
        try:
            conn = get_sqlite_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM localities")
            loc_cnt = cur.fetchone()[0]
            conn.close()
            if loc_cnt == 0:
                print("[Database Notice] SQLite database empty. Auto-seeding initial dataset...")
                import seed_data
                seed_data.seed()
        except Exception as se:
            print(f"[Database Warning] Auto-seed check notice: {se}")
        seed_builder_schemes_if_empty()
        print(f"[Database Active] Connected to SQLite database at {SQLITE_DB_PATH}")


# ---------------------------------------------------------------------------
# User CRUD Operations
# ---------------------------------------------------------------------------

def create_user(first_name, surname, age, phone, email, username, password_hash):
    """Insert a new registered user into active database (MongoDB or SQLite)."""
    clean_email = email.lower().strip()
    clean_username = username.strip()
    now = datetime.now(timezone.utc).isoformat()

    if is_mongodb_active():
        db = get_mongo_db()
        try:
            # Check unique constraint proactively
            if db["users"].find_one({"email": clean_email}):
                return {"success": False, "error": "An account with this email already exists."}
            clean_phone = re.sub(r"[\s\-\+]", "", str(phone or "")).strip()
            if clean_phone and db["users"].find_one({"phone": clean_phone}):
                return {"success": False, "error": "This phone number is already registered."}
            if db["users"].find_one({"email": clean_email}):
                return {"success": False, "error": "An account with this email already exists."}
            if db["users"].find_one({"username": {"$regex": f"^{re_escape(clean_username)}$", "$options": "i"}}):
                return {"success": False, "error": "This username is already taken."}

            user_id = _get_next_sequence("user_id")
            doc = {
                "id": user_id,
                "first_name": first_name.strip(),
                "surname": surname.strip(),
                "age": int(age) if age else None,
                "phone": clean_phone,
                "email": clean_email,
                "username": clean_username,
                "password_hash": password_hash,
                "created_at": now,
                "updated_at": now
            }
            db["users"].insert_one(doc)
            return {"success": True, "user_id": user_id}
        except DuplicateKeyError as e:
            err_str = str(e)
            if "phone" in err_str:
                return {"success": False, "error": "This phone number is already registered."}
            elif "email" in err_str:
                return {"success": False, "error": "An account with this email already exists."}
            elif "username" in err_str:
                return {"success": False, "error": "This username is already taken."}
            return {"success": False, "error": "User already exists with given credentials."}
        except Exception as e:
            return {"success": False, "error": f"Database error: {str(e)}"}

    # SQLite Fallback
    clean_phone = re.sub(r"[\s\-\+]", "", str(phone or "")).strip()
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (first_name, surname, age, phone, email, username, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, surname, age, clean_phone, clean_email, clean_username, password_hash, now, now))
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError as e:
        err_msg = str(e)
        if "users.phone" in err_msg or "UNIQUE constraint failed: users.phone" in err_msg:
            return {"success": False, "error": "This phone number is already registered."}
        elif "users.email" in err_msg or "UNIQUE constraint failed: users.email" in err_msg:
            return {"success": False, "error": "An account with this email already exists."}
        elif "users.username" in err_msg or "UNIQUE constraint failed: users.username" in err_msg:
            return {"success": False, "error": "This username is already taken."}
        return {"success": False, "error": "User already exists with given credentials."}
    finally:
        conn.close()


def _sanitize_mongo_doc(doc):
    """Convert Mongo document to standard dict, ensuring id field is populated."""
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        if "id" not in d or d["id"] is None:
            d["id"] = str(d["_id"])
        del d["_id"]
    return d


def re_escape(s):
    """Escape regex characters safely."""
    import re
    return re.escape(s)


def get_user_by_email(email):
    """Retrieve user record by email."""
    if not email:
        return None
    clean_email = email.lower().strip()

    if is_mongodb_active():
        db = get_mongo_db()
        doc = db["users"].find_one({"email": clean_email})
        return _sanitize_mongo_doc(doc)

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean_email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username):
    """Retrieve user record by username."""
    if not username:
        return None
    clean_username = username.strip()

    if is_mongodb_active():
        db = get_mongo_db()
        doc = db["users"].find_one({"username": {"$regex": f"^{re_escape(clean_username)}$", "$options": "i"}})
        return _sanitize_mongo_doc(doc)

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean_username.lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    """Retrieve user record by user_id (int or string)."""
    if user_id is None:
        return None

    if is_mongodb_active():
        db = get_mongo_db()
        # Try finding by numeric id first, then fallback
        try:
            uid_int = int(user_id)
            doc = db["users"].find_one({"id": uid_int})
            if doc:
                return _sanitize_mongo_doc(doc)
        except (ValueError, TypeError):
            pass
        doc = db["users"].find_one({"id": user_id})
        return _sanitize_mongo_doc(doc)

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(email, new_password_hash):
    """Update password hash for a user during password reset."""
    clean_email = email.lower().strip()
    now = datetime.now(timezone.utc).isoformat()

    if is_mongodb_active():
        db = get_mongo_db()
        res = db["users"].update_one(
            {"email": clean_email},
            {"$set": {"password_hash": new_password_hash, "updated_at": now}}
        )
        return res.modified_count > 0 or res.matched_count > 0

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET password_hash = ?, updated_at = ?
        WHERE LOWER(email) = ?
    """, (new_password_hash, now, clean_email))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def email_or_username_exists(email, username, phone=None):
    """Check if email, username, or phone is already taken."""
    return check_user_credentials_exist(email, username, phone)


def check_user_credentials_exist(email, username, phone=None):
    """Check if email, username, or phone is already registered in DB."""
    import re
    clean_email = email.lower().strip() if email else ""
    clean_username = username.strip() if username else ""
    clean_phone = re.sub(r"[\s\-\+]", "", str(phone or "")).strip() if phone else ""

    if is_mongodb_active():
        db = get_mongo_db()
        if clean_phone:
            phone_match = db["users"].find_one({"phone": clean_phone})
            if phone_match:
                return "This phone number is already registered."
        if clean_email:
            email_match = db["users"].find_one({"email": clean_email})
            if email_match:
                return "An account with this email already exists."
        if clean_username:
            user_match = db["users"].find_one({"username": {"$regex": f"^{re_escape(clean_username)}$", "$options": "i"}})
            if user_match:
                return "This username is already taken."
        return None

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    if clean_phone:
        cursor.execute("""
            SELECT email, username, phone FROM users
            WHERE LOWER(email) = ? OR LOWER(username) = ? OR phone = ?
        """, (clean_email, clean_username.lower(), clean_phone))
    else:
        cursor.execute("""
            SELECT email, username, phone FROM users
            WHERE LOWER(email) = ? OR LOWER(username) = ?
        """, (clean_email, clean_username.lower()))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        if clean_phone and row["phone"] == clean_phone:
            return "This phone number is already registered."
        if row["email"] and row["email"].lower() == clean_email:
            return "An account with this email already exists."
        if row["username"] and row["username"].lower() == clean_username.lower():
            return "This username is already taken."
    return None


def get_all_users():
    """Retrieve list of all registered users (excluding sensitive password hashes)."""
    if is_mongodb_active():
        db = get_mongo_db()
        cursor = db["users"].find({}, {"password_hash": 0}).sort("id", DESCENDING)
        users = []
        for doc in cursor:
            users.append(_sanitize_mongo_doc(doc))
        return users

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, first_name, surname, age, phone, email, username, created_at, updated_at
        FROM users
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    """Delete a user account by user_id."""
    if is_mongodb_active():
        db = get_mongo_db()
        try:
            uid_int = int(user_id)
            res = db["users"].delete_one({"id": uid_int})
            if res.deleted_count > 0:
                return True
        except (ValueError, TypeError):
            pass
        res = db["users"].delete_one({"id": user_id})
        return res.deleted_count > 0

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def count_users():
    """Return total number of registered users."""
    if is_mongodb_active():
        db = get_mongo_db()
        return db["users"].count_documents({})

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    row = cursor.fetchone()
    conn.close()
    return row["count"] if row else 0


# ---------------------------------------------------------------------------
# Locality CRUD Operations
# ---------------------------------------------------------------------------

def update_locality_price(name, rate_per_sqft, rate_per_sqyd=None, yoy_percent=None,
                          projected_5yr=None, livability_score=None):
    """Manually update pricing and metrics for a specific locality."""
    clean_name = name.strip()
    now = datetime.now(timezone.utc).isoformat()

    if rate_per_sqyd is None:
        rate_per_sqyd = round(float(rate_per_sqft) * 9.0, 2)

    if is_mongodb_active():
        db = get_mongo_db()
        update_fields = {
            "rate_per_sqft": float(rate_per_sqft),
            "rate_per_sqyd": float(rate_per_sqyd),
            "updated_at": now
        }
        if yoy_percent is not None:
            update_fields["yoy_percent"] = float(yoy_percent)
        if projected_5yr is not None:
            update_fields["projected_5yr"] = float(projected_5yr)
        if livability_score is not None:
            update_fields["livability_score"] = float(livability_score)

        res = db["localities"].update_one(
            {"name": {"$regex": f"^{re_escape(clean_name)}$", "$options": "i"}},
            {"$set": update_fields}
        )
        return res.modified_count > 0 or res.matched_count > 0

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    updates = ["rate_per_sqft = ?", "rate_per_sqyd = ?", "updated_at = ?"]
    params = [float(rate_per_sqft), float(rate_per_sqyd), now]

    if yoy_percent is not None:
        updates.append("yoy_percent = ?")
        params.append(float(yoy_percent))
    if projected_5yr is not None:
        updates.append("projected_5yr = ?")
        params.append(float(projected_5yr))
    if livability_score is not None:
        updates.append("livability_score = ?")
        params.append(float(livability_score))

    params.append(clean_name.lower())
    query = f"UPDATE localities SET {', '.join(updates)} WHERE LOWER(name) = ?"

    cursor.execute(query, tuple(params))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0


def upsert_locality(name, zone, tier, rate_per_sqyd, rate_per_sqft, yoy_percent,
                    projected_5yr, note, landmarks, schools_hospitals, transit,
                    livability_score, data_source, price_explanation_en=None, price_explanation_hi=None):
    """Insert or update locality details in active database."""
    clean_name = name.strip()
    now = datetime.now(timezone.utc).isoformat()

    if is_mongodb_active():
        db = get_mongo_db()
        doc_data = {
            "name": clean_name,
            "zone": zone,
            "tier": tier,
            "rate_per_sqyd": float(rate_per_sqyd),
            "rate_per_sqft": float(rate_per_sqft),
            "yoy_percent": float(yoy_percent) if yoy_percent is not None else None,
            "projected_5yr": float(projected_5yr) if projected_5yr is not None else None,
            "note": note,
            "landmarks": landmarks,
            "schools_hospitals": schools_hospitals,
            "transit": transit,
            "livability_score": float(livability_score) if livability_score is not None else None,
            "data_source": data_source,
            "price_explanation_en": price_explanation_en,
            "price_explanation_hi": price_explanation_hi,
            "updated_at": now
        }
        db["localities"].update_one(
            {"name": {"$regex": f"^{re_escape(clean_name)}$", "$options": "i"}},
            {"$set": doc_data},
            upsert=True
        )
        return

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO localities (
            name, zone, tier, rate_per_sqyd, rate_per_sqft, yoy_percent,
            projected_5yr, note, landmarks, schools_hospitals, transit,
            livability_score, data_source, price_explanation_en, price_explanation_hi, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            zone=excluded.zone,
            tier=excluded.tier,
            rate_per_sqyd=excluded.rate_per_sqyd,
            rate_per_sqft=excluded.rate_per_sqft,
            yoy_percent=excluded.yoy_percent,
            projected_5yr=excluded.projected_5yr,
            note=excluded.note,
            landmarks=excluded.landmarks,
            schools_hospitals=excluded.schools_hospitals,
            transit=excluded.transit,
            livability_score=excluded.livability_score,
            data_source=excluded.data_source,
            price_explanation_en=coalesce(excluded.price_explanation_en, localities.price_explanation_en),
            price_explanation_hi=coalesce(excluded.price_explanation_hi, localities.price_explanation_hi),
            updated_at=excluded.updated_at
    """, (
        clean_name, zone, tier, rate_per_sqyd, rate_per_sqft, yoy_percent,
        projected_5yr, note, landmarks, schools_hospitals, transit,
        livability_score, data_source, price_explanation_en, price_explanation_hi, now
    ))
    conn.commit()
    conn.close()


def get_all_localities(zone_filter=None):
    """Get list of all localities sorted by name or filtered by zone."""
    if is_mongodb_active():
        db = get_mongo_db()
        query = {}
        if zone_filter:
            query["zone"] = {"$regex": f"^{re_escape(zone_filter.strip())}$", "$options": "i"}
        cursor = db["localities"].find(query).sort("name", ASCENDING)
        return [_sanitize_mongo_doc(doc) for doc in cursor]

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    if zone_filter:
        cursor.execute("SELECT * FROM localities WHERE LOWER(zone) = ? ORDER BY name ASC", (zone_filter.lower().strip(),))
    else:
        cursor.execute("SELECT * FROM localities ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_locality_by_name(name):
    """Get single locality with rich information."""
    if not name:
        return None
    clean_name = name.strip()

    if is_mongodb_active():
        db = get_mongo_db()
        doc = db["localities"].find_one({"name": {"$regex": f"^{re_escape(clean_name)}$", "$options": "i"}})
        return _sanitize_mongo_doc(doc)

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM localities WHERE LOWER(name) = ?", (clean_name.lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Historical Trends CRUD Operations
# ---------------------------------------------------------------------------

def add_historical_trend(locality_name, year, rate_per_sqft, rate_per_sqyd, source):
    """Insert or replace historical trend point."""
    clean_name = locality_name.strip()
    year_int = int(year)

    if is_mongodb_active():
        db = get_mongo_db()
        db["historical_trends"].update_one(
            {"locality_name": {"$regex": f"^{re_escape(clean_name)}$", "$options": "i"}, "year": year_int},
            {"$set": {
                "locality_name": clean_name,
                "year": year_int,
                "rate_per_sqft": float(rate_per_sqft),
                "rate_per_sqyd": float(rate_per_sqyd),
                "source": source
            }},
            upsert=True
        )
        return

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historical_trends (locality_name, year, rate_per_sqft, rate_per_sqyd, source)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(locality_name, year) DO UPDATE SET
            rate_per_sqft=excluded.rate_per_sqft,
            rate_per_sqyd=excluded.rate_per_sqyd,
            source=excluded.source
    """, (clean_name, year_int, rate_per_sqft, rate_per_sqyd, source))
    conn.commit()
    conn.close()


def get_historical_trends(locality_name):
    """Get all historical trend points for a given locality ordered by year."""
    if not locality_name:
        return []
    clean_name = locality_name.strip()

    if is_mongodb_active():
        db = get_mongo_db()
        cursor = db["historical_trends"].find(
            {"locality_name": {"$regex": f"^{re_escape(clean_name)}$", "$options": "i"}}
        ).sort("year", ASCENDING)
        return [{"year": doc["year"], "rate_per_sqft": doc["rate_per_sqft"], "rate_per_sqyd": doc["rate_per_sqyd"], "source": doc.get("source", "")} for doc in cursor]

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, rate_per_sqft, rate_per_sqyd, source
        FROM historical_trends
        WHERE LOWER(locality_name) = ?
        ORDER BY year ASC
    """, (clean_name.lower(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_builder_enquiry(scheme_id, scheme_name, buyer_name, phone, email, message):
    """Save user enquiry for a builder scheme brochure or consultation."""
    created_at = datetime.now(timezone.utc).isoformat()
    if is_mongodb_active():
        db = get_mongo_db()
        db["builder_enquiries"].insert_one({
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "buyer_name": buyer_name,
            "phone": phone,
            "email": email,
            "message": message,
            "created_at": created_at
        })
        return {"success": True, "message": "Enquiry registered successfully."}

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO builder_enquiries (scheme_id, scheme_name, buyer_name, phone, email, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (scheme_id, scheme_name, buyer_name, phone, email, message, created_at))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Enquiry registered successfully."}


def save_builder_ad(builder_name, project_name, locality, property_type, price_range, rera_id, contact_phone, contact_email, brochure_url=""):
    """Register a new builder ad / sponsorship application."""
    created_at = datetime.now(timezone.utc).isoformat()
    if is_mongodb_active():
        db = get_mongo_db()
        doc = {
            "builder_name": builder_name,
            "project_name": project_name,
            "locality": locality,
            "property_type": property_type,
            "price_range": price_range,
            "rera_id": rera_id,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
            "brochure_url": brochure_url,
            "status": "active",
            "created_at": created_at
        }
        res = db["builder_ads"].insert_one(doc)
        return {"success": True, "message": "Project listing submitted successfully!", "ad_id": str(res.inserted_id)}

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO builder_ads (builder_name, project_name, locality, property_type, price_range, rera_id, contact_phone, contact_email, brochure_url, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (builder_name, project_name, locality, property_type, price_range, rera_id, contact_phone, contact_email, brochure_url, created_at))
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "message": "Project listing submitted successfully!", "ad_id": ad_id}


def get_builder_ads():
    """Retrieve all approved active builder project listings."""
    if is_mongodb_active():
        db = get_mongo_db()
        cursor = db["builder_ads"].find({"status": "active"}).sort("created_at", -1)
        return [dict(doc, id=str(doc.get("_id"))) for doc in cursor]

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM builder_ads WHERE status = 'active' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_database_status():
    """Return dictionary with database status and record statistics."""
    active_engine = "MongoDB" if is_mongodb_active() else "SQLite"
    total_users = count_users()
    total_locs = len(get_all_localities())
    
    return {
        "engine": active_engine,
        "is_mongodb": is_mongodb_active(),
        "mongo_uri": MONGO_URI if is_mongodb_active() else None,
        "mongo_db_name": MONGO_DB_NAME if is_mongodb_active() else None,
        "sqlite_path": SQLITE_DB_PATH,
        "total_users": total_users,
        "total_localities": total_locs
    }




# ===========================================================================
# DEVELOPER SHOWCASE & SCHEMES (Hybrid SQLite & MongoDB)
# ===========================================================================

INITIAL_BUILDER_SCHEMES = [
    {
        "id": "godrej-celestial-jagatpur",
        "name": "Godrej Celestial & Green Vistas",
        "builder": "Godrej Properties Ltd.",
        "builder_tagline": "India's Most Trusted Developer",
        "locality": "Jagatpur",
        "zone": "North",
        "property_type": "Apartment / Flat",
        "tag": "Featured Green Township",
        "badge_color": "#10B981",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA08912/050124",
        "price_min": 6800000,
        "price_max": 11500000,
        "price_display": "₹68 L – ₹1.15 Cr",
        "config_display": "2 & 3 BHK Resort Residences",
        "area_range": "110 – 185 Sq. Yds",
        "possession": "Dec 2026 (Under Construction)",
        "units_available": 14,
        "summary": "Master-planned forest-themed township adjacent to SG Highway featuring 70% open green landscapes, oxygen pavilions, and a 25,000 sq.ft luxury clubhouse.",
        "amenities": [
            "Olympic-Size Infinity Pool",
            "Forest Walkways & Yoga Lawn",
            "Electric Vehicle (EV) Rapid Charging Stations",
            "Indoor Badminton & Squash Courts",
            "Kids Adventure Creche & Senior Citizen Plaza"
        ],
        "specs": {
            "flooring": "Vitrified Italian-finish tiles in living & dining",
            "kitchen": "Granite platform with stainless steel sink & piped gas line",
            "structure": "Earthquake-resistant RCC shear-wall construction",
            "security": "3-Tier smart biometric access & 24/7 CCTV surveillance"
        },
        "floor_plans": [
            {"type": "2 BHK Elegance", "carpet_area": "685 sq.ft", "builtup_sqyd": "112 sq.yd", "price_from": "₹68.0 Lakhs"},
            {"type": "3 BHK Grandeur", "carpet_area": "980 sq.ft", "builtup_sqyd": "158 sq.yd", "price_from": "₹94.5 Lakhs"},
            {"type": "3 BHK Royal Deck", "carpet_area": "1140 sq.ft", "builtup_sqyd": "182 sq.yd", "price_from": "₹1.12 Crore"}
        ],
        "payment_plan": [
            {"milestone": "At Booking / Token", "percentage": "10%"},
            {"milestone": "On Plinth Completion", "percentage": "20%"},
            {"milestone": "On Superstructure Slabs (Equal Installments)", "percentage": "50%"},
            {"milestone": "On Possession & Key Handover", "percentage": "20%"}
        ],
        "contact_phone": "+91 98250 88901",
        "contact_email": "sales.celestial@godrejahmedabad.com",
        "site_address": "Near Godrej Garden City, SG Highway Corridor, Jagatpur, Ahmedabad"
    },
    {
        "id": "adani-waterlily-vaishnodevi",
        "name": "Adani Shantigram - Water Lily",
        "builder": "Adani Realty",
        "builder_tagline": "Gujarat's Premier Mega-Township",
        "locality": "Vaishnodevi",
        "zone": "North",
        "property_type": "Apartment / Flat",
        "tag": "Lakefront Ultra-Luxury",
        "badge_color": "#C9922E",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA09433/120324",
        "price_min": 14500000,
        "price_max": 31000000,
        "price_display": "₹1.45 Cr – ₹3.10 Cr",
        "config_display": "3 & 4 BHK Lakefront High-Rise",
        "area_range": "180 – 340 Sq. Yds",
        "possession": "Ready to Move / Select Towers 2026",
        "units_available": 8,
        "summary": "Surrounded by a scenic 7-acre musical lake in Shantigram, offering panoramic sunset decks, private elevators, and a 9-hole golf course privileges.",
        "amenities": [
            "7-Acre Serene Lakefront Promenade",
            "9-Hole Executive Golf Course Access",
            "The Belvedere Private Members Club",
            "Helipad & EV Fleet Charging Hub",
            "Full Home Automation (IoT Enabled)"
        ],
        "specs": {
            "flooring": "Imported Marble in living room, wooden laminates in master suite",
            "kitchen": "German modular fittings with hob, chimney & granite counter",
            "structure": "Seismic Zone IV earthquake-engineered frame",
            "security": "Video door phone, RFID boom barrier & facial recognition"
        },
        "floor_plans": [
            {"type": "3 BHK Lakeview", "carpet_area": "1280 sq.ft", "builtup_sqyd": "195 sq.yd", "price_from": "₹1.45 Crore"},
            {"type": "4 BHK Horizon Villa", "carpet_area": "1920 sq.ft", "builtup_sqyd": "290 sq.yd", "price_from": "₹2.25 Crore"},
            {"type": "4.5 BHK Sky Penthouse", "carpet_area": "2650 sq.ft", "builtup_sqyd": "360 sq.yd", "price_from": "₹3.10 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Booking Advance", "percentage": "10%"},
            {"milestone": "Agreement for Sale", "percentage": "15%"},
            {"milestone": "Construction Milestones", "percentage": "60%"},
            {"milestone": "Occupancy Certificate / Handover", "percentage": "15%"}
        ],
        "contact_phone": "+91 97129 44321",
        "contact_email": "waterlily@adanirealty.com",
        "site_address": "Adani Shantigram, Near Vaishnodevi Circle, SG Highway, Ahmedabad"
    },
    {
        "id": "shivalik-edge-sbr",
        "name": "Shivalik Edge & Parkview",
        "builder": "Shivalik Group",
        "builder_tagline": "Architects of Ahmedabad Skyline",
        "locality": "Sindhu Bhavan Road",
        "zone": "West",
        "property_type": "Apartment / Flat",
        "tag": "SBR Golden Boulevard",
        "badge_color": "#F5D77F",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA07890/190824",
        "price_min": 24000000,
        "price_max": 58000000,
        "price_display": "₹2.40 Cr – ₹5.80 Cr",
        "config_display": "4 & 5 BHK Sky Mansions",
        "area_range": "240 – 520 Sq. Yds",
        "possession": "Dec 2026",
        "units_available": 5,
        "summary": "Ahmedabad's most iconic luxury address on Sindhu Bhavan Road. Single apartment per floor layout with 12-foot clear ceiling heights and panoramic skyline vistas.",
        "amenities": [
            "Private Elevator to Exclusive Floor Foyer",
            "Temperature-Controlled Heated Sky Pool",
            "Cigar Lounge & Private Screening Theatre",
            "Dedicated Valet & Concierge Desk",
            "3 Reserved Basement Car Parks per Unit"
        ],
        "specs": {
            "flooring": "Dyna Italian Statuario Marble throughout",
            "kitchen": "Italian bespoke modular kitchen with central island",
            "structure": "Post-tensioned slab construction with zero beam drops",
            "security": "Military-grade biometric access & IP camera matrix"
        },
        "floor_plans": [
            {"type": "4 BHK Royal Floor", "carpet_area": "2400 sq.ft", "builtup_sqyd": "310 sq.yd", "price_from": "₹2.40 Crore"},
            {"type": "5 BHK Sky Mansion", "carpet_area": "3450 sq.ft", "builtup_sqyd": "440 sq.yd", "price_from": "₹3.90 Crore"},
            {"type": "Duplex Penthouse Deck", "carpet_area": "4800 sq.ft", "builtup_sqyd": "590 sq.yd", "price_from": "₹5.80 Crore"}
        ],
        "payment_plan": [
            {"milestone": "EOI & Booking", "percentage": "10%"},
            {"milestone": "Foundation & Basement", "percentage": "20%"},
            {"milestone": "Floor Slab Milestones", "percentage": "50%"},
            {"milestone": "Finishing & Handover", "percentage": "20%"}
        ],
        "contact_phone": "+91 99090 12345",
        "contact_email": "edge@shivalikgroup.com",
        "site_address": "Off Sindhu Bhavan Road, Bodakdev-SBR Extension, Ahmedabad"
    },
    {
        "id": "iscon-platinum-duplexes",
        "name": "Iscon Platinum Luxury Duplexes & Villas",
        "builder": "JP Iscon Group",
        "builder_tagline": "Bespoke Landed Living",
        "locality": "Bopal",
        "zone": "West",
        "property_type": "Tenement / Duplex",
        "tag": "Independent Tenement Villas",
        "badge_color": "#38BDF8",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA05411/140424",
        "price_min": 18500000,
        "price_max": 38000000,
        "price_display": "₹1.85 Cr – ₹3.80 Cr",
        "config_display": "3 & 4 BHK Independent Duplex Villas",
        "area_range": "160 – 320 Sq. Yds",
        "possession": "Ready to Move (Limited Inventory)",
        "units_available": 6,
        "summary": "Exclusive gated community of independent duplex tenements with private landscaped lawns, terrace entertainment decks, and complete freehold land ownership.",
        "amenities": [
            "Private Terrace Jacuzzi & Barbecue Deck",
            "Individual Private Front Lawn & Porch",
            "Gated Community with 24/7 Security Patrol",
            "Community Clubhouse & Swimming Pool",
            "Solar Panel Pre-Installed on Every Rooftop"
        ],
        "specs": {
            "flooring": "Premium double-charged vitrified flooring & teakwood main doors",
            "kitchen": "Quartz platform with designer dado tiles",
            "structure": "Independent load-bearing RCC structure with dedicated foundation",
            "security": "Compound wall with infrared perimeter beam intrusion system"
        },
        "floor_plans": [
            {"type": "3 BHK Courtyard Tenement", "carpet_area": "1650 sq.ft", "builtup_sqyd": "180 sq.yd", "price_from": "₹1.85 Crore"},
            {"type": "4 BHK Grand Duplex Villa", "carpet_area": "2400 sq.ft", "builtup_sqyd": "250 sq.yd", "price_from": "₹2.65 Crore"},
            {"type": "4 BHK Sovereign Villa (Corner Plot)", "carpet_area": "3100 sq.ft", "builtup_sqyd": "320 sq.yd", "price_from": "₹3.80 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Token & Allotment", "percentage": "15%"},
            {"milestone": "Registry / Agreement", "percentage": "25%"},
            {"milestone": "Bank Finance Disbursement", "percentage": "50%"},
            {"milestone": "Possession & Title Handover", "percentage": "10%"}
        ],
        "contact_phone": "+91 98795 66778",
        "contact_email": "villas@iscongroup.com",
        "site_address": "Ambli-Bopal Road, Near Bopal Lake, Ahmedabad"
    },
    {
        "id": "ganesh-malabar-tenements",
        "name": "Ganesh Malabar Retreat & Tenements",
        "builder": "Ganesh Housing Corporation Ltd.",
        "builder_tagline": "Legacy of Quality Homes Since 1969",
        "locality": "Gota",
        "zone": "North",
        "property_type": "Tenement / Duplex",
        "tag": "Freehold Row Houses",
        "badge_color": "#38BDF8",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA08129/090924",
        "price_min": 9500000,
        "price_max": 16500000,
        "price_display": "₹95 L – ₹1.65 Cr",
        "config_display": "3 BHK Modern Tenements & Row Houses",
        "area_range": "125 – 195 Sq. Yds",
        "possession": "Mid 2026",
        "units_available": 11,
        "summary": "Affordable luxury row houses and tenements with private backyards, covered car porch, and dedicated terrace rights in Gota near Gujarat High Court.",
        "amenities": [
            "Private Covered Car Parking Porch",
            "Private Garden Backyard & Sit-out",
            "Rooftop Terrace with Pergola Space",
            "Children Play Park & Walking Jogging Track",
            "24/7 Water Supply with Underground Storage"
        ],
        "specs": {
            "flooring": "Vitrified tiles across all rooms",
            "kitchen": "Polished granite counter with stainless steel sink",
            "structure": "RCC frame structure designed for G+1 and G+2 options",
            "security": "Gated campus with CCTV monitoring and security cabin"
        },
        "floor_plans": [
            {"type": "3 BHK Comfort Row House", "carpet_area": "1250 sq.ft", "builtup_sqyd": "135 sq.yd", "price_from": "₹95.0 Lakhs"},
            {"type": "3 BHK Royal Tenement", "carpet_area": "1550 sq.ft", "builtup_sqyd": "165 sq.yd", "price_from": "₹1.25 Crore"},
            {"type": "4 BHK Signature Duplex", "carpet_area": "1900 sq.ft", "builtup_sqyd": "195 sq.yd", "price_from": "₹1.65 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Token Amount", "percentage": "10%"},
            {"milestone": "Slab Level Progress", "percentage": "60%"},
            {"milestone": "Plaster & Finishing", "percentage": "20%"},
            {"milestone": "Key Handover", "percentage": "10%"}
        ],
        "contact_phone": "+91 99241 55667",
        "contact_email": "malabar@ganeshhousing.com",
        "site_address": "Near Godrej Garden City Road, Gota-Jagatpur Belt, Ahmedabad"
    },
    {
        "id": "goyal-orchid-shela",
        "name": "Goyal Orchid Whitefield",
        "builder": "Goyal & Co. (Construction) Pvt. Ltd.",
        "builder_tagline": "50+ Years of Architectural Integrity",
        "locality": "Shela",
        "zone": "West",
        "property_type": "Apartment / Flat",
        "tag": "High Capital ROI Corridor",
        "badge_color": "#C9922E",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA07119/111124",
        "price_min": 10500000,
        "price_max": 16800000,
        "price_display": "₹1.05 Cr – ₹1.68 Cr",
        "config_display": "3 BHK Master Residences",
        "area_range": "140 – 210 Sq. Yds",
        "possession": "March 2026",
        "units_available": 9,
        "summary": "Sophisticated residential landmark right next to Club O7 in Shela. Designed with three-side open ventilation, sky balconies, and zero wasted corridor spaces.",
        "amenities": [
            "Proximity to Club O7 & SP Ring Road",
            "Double-Height Grand Entrance Lobby",
            "Rooftop Astro-Deck & Yoga Pavilion",
            "Indoor Games Arcade & Banquet Facility",
            "100% DG Power Backup for Common Areas"
        ],
        "specs": {
            "flooring": "Large format 800x1600mm glazed vitrified tiles",
            "kitchen": "Granite platform with provision for dishwasher & water purifier",
            "structure": "Earthquake resistant RCC framework",
            "security": "Intercom connected to security gate & fire detection system"
        },
        "floor_plans": [
            {"type": "3 BHK Compact Luxe", "carpet_area": "995 sq.ft", "builtup_sqyd": "145 sq.yd", "price_from": "₹1.05 Crore"},
            {"type": "3 BHK Ultra Spacia", "carpet_area": "1250 sq.ft", "builtup_sqyd": "178 sq.yd", "price_from": "₹1.35 Crore"},
            {"type": "3.5 BHK Sky Terrace Suite", "carpet_area": "1450 sq.ft", "builtup_sqyd": "205 sq.yd", "price_from": "₹1.68 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Booking Agreement", "percentage": "10%"},
            {"milestone": "Foundation & Basement Slabs", "percentage": "25%"},
            {"milestone": "Superstructure Installments", "percentage": "45%"},
            {"milestone": "Possession & Registration", "percentage": "20%"}
        ],
        "contact_phone": "+91 98251 77334",
        "contact_email": "shela@goyalco.com",
        "site_address": "Near Club O7, Off SP Ring Road, Shela, Ahmedabad"
    },
    {
        "id": "sun-south-park-bopal",
        "name": "Sun South Park & Ray",
        "builder": "Sun Builders Group",
        "builder_tagline": "Redefining Urban Living in Gujarat",
        "locality": "South Bopal",
        "zone": "West",
        "property_type": "Apartment / Flat",
        "tag": "Bestseller Family Community",
        "badge_color": "#10B981",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA06541/220224",
        "price_min": 7200000,
        "price_max": 12800000,
        "price_display": "₹72 L – ₹1.28 Cr",
        "config_display": "2 & 3 BHK Urban Condos",
        "area_range": "115 – 175 Sq. Yds",
        "possession": "Ready to Move & Nearing Possession",
        "units_available": 12,
        "summary": "Centrally located in South Bopal walking distance from SOBO Center. Excellent community with lush botanical gardens, sports facilities, and high rental yield.",
        "amenities": [
            "Walking Distance to SOBO Center & TRP Mall",
            "Full-Fledged Gym & Aerobics Studio",
            "Cricket Net Pitch & Multi-Sport Court",
            "Children's Themed Splash Pool",
            "Basement Stilt Parking with Dedicated Car Wash Bay"
        ],
        "specs": {
            "flooring": "Premium vitrified tiles in all bedrooms",
            "kitchen": "Granite platform with stainless sink & dry balcony",
            "structure": "Solid RCC frame with fly-ash acoustic bricks",
            "security": "24/7 Security guard patrol & automatic elevator rescue"
        },
        "floor_plans": [
            {"type": "2 BHK Urban", "carpet_area": "710 sq.ft", "builtup_sqyd": "118 sq.yd", "price_from": "₹72.0 Lakhs"},
            {"type": "3 BHK Comfort", "carpet_area": "960 sq.ft", "builtup_sqyd": "150 sq.yd", "price_from": "₹96.5 Lakhs"},
            {"type": "3 BHK Signature", "carpet_area": "1180 sq.ft", "builtup_sqyd": "172 sq.yd", "price_from": "₹1.28 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Booking Token", "percentage": "10%"},
            {"milestone": "Sale Agreement", "percentage": "15%"},
            {"milestone": "Bank Disbursal / Milestones", "percentage": "65%"},
            {"milestone": "Possession", "percentage": "10%"}
        ],
        "contact_phone": "+91 97277 88990",
        "contact_email": "southpark@sunbuilders.in",
        "site_address": "SOBO Center Road, South Bopal, Ahmedabad"
    },
    {
        "id": "takshashila-air-riverfront",
        "name": "Takshashila Air - Riverfront Tower",
        "builder": "Takshashila Realties",
        "builder_tagline": "Prestige Heritage Real Estate",
        "locality": "Ellisbridge",
        "zone": "Central",
        "property_type": "Commercial / Penthouse",
        "tag": "Riverfront Iconic Landmark",
        "badge_color": "#C9922E",
        "rera_id": "PR/GJ/AHMEDABAD/AHMEDABAD CITY/AUDA/RAA04322/280124",
        "price_min": 18000000,
        "price_max": 65000000,
        "price_display": "₹1.80 Cr – ₹6.50 Cr",
        "config_display": "Commercial Corporate Suites & Sky Penthouses",
        "area_range": "130 – 480 Sq. Yds",
        "possession": "Dec 2026",
        "units_available": 4,
        "summary": "Ahmedabad's landmark 25-storey high-rise overlooking the Sabarmati Riverfront and Atal Bridge. Combines grade-A financial corporate offices with exclusive sky penthouses.",
        "amenities": [
            "Unobstructed Sabarmati Riverfront Panoramic Views",
            "High-Speed Destination-Controlled Elevators",
            "Double-Glazed Low-E Glass Acoustic Facade",
            "Rooftop Helipad & Sky Lounge Executive Club",
            "Multi-Level Automated Mechanical Parking"
        ],
        "specs": {
            "flooring": "Bare-shell office floor plates & marble penthouse finishes",
            "kitchen": "Pantry provision with central water filtration",
            "structure": "Wind tunnel tested steel-composite and high-strength concrete",
            "security": "Airport-standard security scanning & visitor turnstiles"
        },
        "floor_plans": [
            {"type": "Grade-A Corporate Suite", "carpet_area": "1100 sq.ft", "builtup_sqyd": "145 sq.yd", "price_from": "₹1.80 Crore"},
            {"type": "Financial Floor Wing", "carpet_area": "2500 sq.ft", "builtup_sqyd": "320 sq.yd", "price_from": "₹3.90 Crore"},
            {"type": "Presidential River Sky Penthouse", "carpet_area": "4200 sq.ft", "builtup_sqyd": "520 sq.yd", "price_from": "₹6.50 Crore"}
        ],
        "payment_plan": [
            {"milestone": "Booking Advance", "percentage": "15%"},
            {"milestone": "Basement Infrastructure", "percentage": "25%"},
            {"milestone": "Tower Slabs & Curtain Wall Facade", "percentage": "40%"},
            {"milestone": "Possession & Fit-Out Handover", "percentage": "20%"}
        ],
        "contact_phone": "+91 98980 11223",
        "contact_email": "air@takshashila.in",
        "site_address": "Sabarmati Riverfront West, Near Ellisbridge, Ahmedabad"
    }
]


def seed_builder_schemes_if_empty():
    """Ensure initial verified builder schemes are seeded in SQLite and MongoDB."""
    # 1. SQLite check & seed
    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM builder_schemes")
        count = cur.fetchone()[0]
        if count == 0:
            for s in INITIAL_BUILDER_SCHEMES:
                cur.execute("""
                    INSERT OR IGNORE INTO builder_schemes (
                        scheme_id, name, builder, builder_tagline, locality, zone,
                        property_type, tag, badge_color, rera_id, price_min, price_max,
                        price_display, config_display, area_range, possession, units_available,
                        summary, amenities, specs, floor_plans, payment_plan,
                        contact_phone, contact_email, site_address, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                """, (
                    s["id"], s["name"], s["builder"], s.get("builder_tagline", ""),
                    s["locality"], s.get("zone", "West"), s["property_type"],
                    s.get("tag", "Verified Project"), s.get("badge_color", "#C9922E"),
                    s.get("rera_id", ""), s.get("price_min", 0), s.get("price_max", 0),
                    s.get("price_display", ""), s.get("config_display", ""),
                    s.get("area_range", ""), s.get("possession", ""), s.get("units_available", 10),
                    s.get("summary", ""), json.dumps(s.get("amenities", [])),
                    json.dumps(s.get("specs", {})), json.dumps(s.get("floor_plans", [])),
                    json.dumps(s.get("payment_plan", [])), s.get("contact_phone", ""),
                    s.get("contact_email", ""), s.get("site_address", ""),
                    datetime.now(timezone.utc).isoformat()
                ))
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Seeding SQLite builder_schemes: {e}")

    # 2. MongoDB check & seed
    if is_mongodb_active():
        try:
            db = get_mongo_db()
            m_count = db["builder_schemes"].count_documents({})
            if m_count == 0:
                for s in INITIAL_BUILDER_SCHEMES:
                    doc = dict(s)
                    doc["scheme_id"] = s["id"]
                    doc["status"] = "active"
                    doc["created_at"] = datetime.now(timezone.utc).isoformat()
                    db["builder_schemes"].insert_one(doc)
        except Exception as e:
            print(f"[Database Error] Seeding MongoDB builder_schemes: {e}")


def get_all_builder_schemes(locality=None, property_type=None, budget=None):
    """Retrieve all active builder schemes from MongoDB / SQLite."""
    schemes = []
    if is_mongodb_active():
        db = get_mongo_db()
        cursor = db["builder_schemes"].find({"status": "active"}).sort("created_at", 1)
        for doc in cursor:
            d = dict(doc)
            d["id"] = d.get("scheme_id", str(d.get("_id")))
            d.pop("_id", None)
            schemes.append(d)
    else:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM builder_schemes WHERE status = 'active' ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            d = dict(r)
            d["id"] = d.get("scheme_id") or str(d.get("id"))
            for f in ["amenities", "floor_plans", "payment_plan"]:
                if isinstance(d.get(f), str):
                    try:
                        d[f] = json.loads(d[f])
                    except Exception:
                        d[f] = []
            if isinstance(d.get("specs"), str):
                try:
                    d["specs"] = json.loads(d["specs"])
                except Exception:
                    d["specs"] = {}
            schemes.append(d)

    # Also fetch user-submitted approved builder ads
    db_ads = get_builder_ads()
    for ad in db_ads:
        schemes.append({
            "id": f"ad-{ad.get('id', 'custom')}",
            "name": ad.get("project_name", "Featured Scheme"),
            "builder": ad.get("builder_name", "Promoted Developer"),
            "builder_tagline": "RERA Registered Partner",
            "locality": ad.get("locality", "Ahmedabad"),
            "zone": "Prime",
            "property_type": ad.get("property_type", "Apartment / Flat"),
            "tag": "Featured Builder Partner",
            "badge_color": "#C9922E",
            "rera_id": ad.get("rera_id", "RERA Verification"),
            "price_min": 5000000,
            "price_max": 25000000,
            "price_display": ad.get("price_range", "Price on Request"),
            "config_display": "2, 3 & 4 BHK Units",
            "area_range": "120 – 250 Sq. Yds",
            "possession": "Under Construction",
            "units_available": 10,
            "summary": f"Promoted development in {ad.get('locality', 'Ahmedabad')} with modern lifestyle amenities and direct arterial highway access.",
            "amenities": ["Clubhouse & Gym", "24/7 Security", "EV Charging", "Children Play Area"],
            "specs": {"structure": "RCC Engineered", "security": "24/7 CCTV"},
            "floor_plans": [{"type": "Standard Configuration", "carpet_area": "1150 sq.ft", "builtup_sqyd": "160 sq.yd", "price_from": ad.get("price_range", "Inquire")}],
            "payment_plan": [{"milestone": "Booking", "percentage": "10%"}, {"milestone": "Milestones", "percentage": "90%"}],
            "contact_phone": ad.get("contact_phone", "+91 98250 00000"),
            "contact_email": ad.get("contact_email", "sales@vasudharealestate.com"),
            "site_address": f"{ad.get('locality', 'Ahmedabad')}, Gujarat"
        })

    if locality and locality.lower() != "all":
        schemes = [s for s in schemes if locality.lower() in s["locality"].lower()]

    if property_type and property_type.lower() != "all":
        p_clean = property_type.lower()
        if "flat" in p_clean or "apartment" in p_clean:
            schemes = [s for s in schemes if "apartment" in s["property_type"].lower() or "flat" in s["property_type"].lower()]
        elif "tenement" in p_clean or "duplex" in p_clean:
            schemes = [s for s in schemes if "tenement" in s["property_type"].lower() or "duplex" in s["property_type"].lower()]
        elif "commercial" in p_clean:
            schemes = [s for s in schemes if "commercial" in s["property_type"].lower() or "penthouse" in s["property_type"].lower()]

    return schemes


def get_builder_scheme_by_id(scheme_id):
    """Retrieve full scheme dossier by ID from DB."""
    all_schemes = get_all_builder_schemes()
    for s in all_schemes:
        if str(s.get("id")) == str(scheme_id) or str(s.get("scheme_id")) == str(scheme_id):
            return s
    return None


def add_builder_scheme(data):
    """Insert a new builder scheme into SQLite and MongoDB."""
    name = (data.get("name") or data.get("project_name") or "New Project").strip()
    scheme_id = data.get("scheme_id") or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    created_at = datetime.now(timezone.utc).isoformat()
    
    amenities = data.get("amenities") or ["Clubhouse & Gym", "24/7 Security", "EV Charging", "Children Play Area"]
    specs = data.get("specs") or {"structure": "RCC Framework", "security": "24/7 Security"}
    floor_plans = data.get("floor_plans") or [{"type": "Standard Configuration", "carpet_area": "1100 sq.ft", "builtup_sqyd": "150 sq.yd", "price_from": data.get("price_display", "On Request")}]
    payment_plan = data.get("payment_plan") or [{"milestone": "Booking", "percentage": "10%"}, {"milestone": "Construction Milestones", "percentage": "70%"}, {"milestone": "Possession", "percentage": "20%"}]
    
    # 1. Insert into SQLite
    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO builder_schemes (
            scheme_id, name, builder, builder_tagline, locality, zone,
            property_type, tag, badge_color, rera_id, price_min, price_max,
            price_display, config_display, area_range, possession, units_available,
            summary, amenities, specs, floor_plans, payment_plan,
            contact_phone, contact_email, site_address, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (
        scheme_id, name, data.get("builder", "Premier Developer"), data.get("builder_tagline", "RERA Registered"),
        data.get("locality", "Ahmedabad"), data.get("zone", "West"), data.get("property_type", "Apartment / Flat"),
        data.get("tag", "Featured Scheme"), data.get("badge_color", "#C9922E"), data.get("rera_id", ""),
        float(data.get("price_min", 6000000)), float(data.get("price_max", 15000000)),
        data.get("price_display", "₹60 L - ₹1.5 Cr"), data.get("config_display", "2 & 3 BHK"),
        data.get("area_range", "120 - 200 Sq. Yds"), data.get("possession", "Dec 2026"),
        int(data.get("units_available", 10)), data.get("summary", ""),
        json.dumps(amenities), json.dumps(specs), json.dumps(floor_plans), json.dumps(payment_plan),
        data.get("contact_phone", "+91 98250 00000"), data.get("contact_email", ""),
        data.get("site_address", f"{data.get('locality', 'Ahmedabad')}, Gujarat"), created_at
    ))
    conn.commit()
    conn.close()

    # 2. Insert into MongoDB if active
    if is_mongodb_active():
        db = get_mongo_db()
        m_doc = {
            "id": scheme_id,
            "scheme_id": scheme_id,
            "name": name,
            "builder": data.get("builder", "Premier Developer"),
            "builder_tagline": data.get("builder_tagline", "RERA Registered"),
            "locality": data.get("locality", "Ahmedabad"),
            "zone": data.get("zone", "West"),
            "property_type": data.get("property_type", "Apartment / Flat"),
            "tag": data.get("tag", "Featured Scheme"),
            "badge_color": data.get("badge_color", "#C9922E"),
            "rera_id": data.get("rera_id", ""),
            "price_min": float(data.get("price_min", 6000000)),
            "price_max": float(data.get("price_max", 15000000)),
            "price_display": data.get("price_display", "₹60 L - ₹1.5 Cr"),
            "config_display": data.get("config_display", "2 & 3 BHK"),
            "area_range": data.get("area_range", "120 - 200 Sq. Yds"),
            "possession": data.get("possession", "Dec 2026"),
            "units_available": int(data.get("units_available", 10)),
            "summary": data.get("summary", ""),
            "amenities": amenities,
            "specs": specs,
            "floor_plans": floor_plans,
            "payment_plan": payment_plan,
            "contact_phone": data.get("contact_phone", "+91 98250 00000"),
            "contact_email": data.get("contact_email", ""),
            "site_address": data.get("site_address", f"{data.get('locality', 'Ahmedabad')}, Gujarat"),
            "status": "active",
            "created_at": created_at
        }
        db["builder_schemes"].insert_one(m_doc)

    return {"success": True, "scheme_id": scheme_id, "message": f"Builder scheme '{name}' saved successfully in SQLite and MongoDB."}


def delete_builder_scheme(scheme_id):
    """Delete or deactivate a builder scheme from SQLite and MongoDB."""
    target_id = str(scheme_id).strip()
    
    # 1. SQLite deletion
    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM builder_schemes WHERE scheme_id = ? OR id = ?", (target_id, target_id))
    # Also if it's an ad
    if target_id.startswith("ad-"):
        ad_id = target_id.replace("ad-", "")
        cur.execute("DELETE FROM builder_ads WHERE id = ?", (ad_id,))
    conn.commit()
    conn.close()

    # 2. MongoDB deletion if active
    if is_mongodb_active():
        db = get_mongo_db()
        db["builder_schemes"].delete_many({"$or": [{"scheme_id": target_id}, {"id": target_id}]})
        if target_id.startswith("ad-"):
            from bson import ObjectId
            try:
                db["builder_ads"].delete_one({"_id": ObjectId(target_id.replace("ad-", ""))})
            except Exception:
                pass

    return {"success": True, "message": f"Scheme '{target_id}' successfully removed from database."}


if __name__ == "__main__":
    init_db()
    status = get_database_status()
    print("=" * 60)
    print(" Vasudha Real Estate — Database Diagnostic")
    print("=" * 60)
    print(f" Active Engine:    {status['engine']}")
    if status['is_mongodb']:
        print(f" MongoDB URI:      {status['mongo_uri']}")
        print(f" Database Name:    {status['mongo_db_name']}")
    else:
        print(f" SQLite File:      {status['sqlite_path']}")
    print(f" Total Users:      {status['total_users']}")
    print(f" Total Localities: {status['total_localities']}")
    print("=" * 60)
