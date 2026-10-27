<!-- ============================================================================== -->
<!-- 🏛️ VASUDHA REAL ESTATE (वसुधा) — OFFICIAL REPOSITORY README -->
<!-- ============================================================================== -->

<div align="center">

# 🏛️ VASUDHA REAL ESTATE (वसुधा)
### ⚡ *AI-Powered Ahmedabad Property Valuation & 5-Year Capital Forecasting Platform*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="Scikit-Learn" />
  <img src="https://img.shields.io/badge/MongoDB-Hybrid-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/Accuracy-R%C2%B2%2099.7%25-00c853?style=for-the-badge" alt="Accuracy" />
</p>

</div>

---

## 📖 Overview

**Vasudha Real Estate (वसुधा)** is an enterprise-grade AI/ML property valuation and investment intelligence platform engineered specifically for **Ahmedabad, Gujarat, India**. 

It empowers home buyers, real estate investors, and developers with:
- Instant property valuations calculated from multi-factor regression models ($R^2 = 0.997$).
- **5-Year Compounding Capital Appreciation Forecasts** based on historical micro-market CAGRs (2020–2026+).
- Real-time **Locality Comparison Radar** across 29+ prime Ahmedabad corridors.
- Secure **Email OTP verification**, **Mortgage EMI calculation**, and **PDF / Email Report Dispatch**.

---

## ✨ Key Features & Capabilities

<table>
  <tr>
    <td width="50%">
      <h3>🤖 AI Property Valuation Engine</h3>
      <ul>
        <li><b>High-Precision ML:</b> Log-Linear Fixed-Effects Regression achieving <b>R² = 0.997</b>.</li>
        <li><b>Flexible Area Units:</b> Support for both <b>Sq. Yards (Gaj)</b> and <b>Sq. Feet</b>.</li>
        <li><b>Property Multipliers:</b> Dynamic weighting for Apartments, Tenements, Duplexes, and Commercial units.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📈 5-Year Capital Forecasts</h3>
      <ul>
        <li><b>Multi-Year Compounding ROI:</b> Year-by-year value projections through 2031.</li>
        <li><b>Locality CAGR Modeling:</b> Uses real observed appreciation rates per corridor (6.2% to 15.8%).</li>
        <li><b>Total Appreciation Breakdown:</b> Estimated net capital gains and annualized ROI.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>⚖️ Micro-Market Benchmarking</h3>
      <ul>
        <li><b>Side-by-Side Comparison:</b> Compare up to 4 localities simultaneously.</li>
        <li><b>Luxury Leaderboard:</b> SBR, Bodakdev, Ambli, and Science City rate index.</li>
        <li><b>Price Trend Visualizer:</b> Interactive charts displaying 2020–2026 historical rates.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🛡️ Enterprise Security & Database</h3>
      <ul>
        <li><b>Hybrid DB Architecture:</b> Primary <b>MongoDB</b> with zero-downtime <b>SQLite</b> failover.</li>
        <li><b>Live OTP Authentication:</b> SMTP email OTP delivery for registration and password resets.</li>
        <li><b>OWASP Protection:</b> Hashed passwords (`Werkzeug`), sanitized SQL/Mongo inputs, CSRF defenses.</li>
      </ul>
    </td>
  <tr>
    <td width="50%">
      <h3>🏢 Developer Showcase & e-Brochure Launchpad</h3>
      <ul>
        <li><b>RERA Verified Showcase:</b> Featured developments across Godrej, Adani, Shivalik, Iscon, Ganesh Housing, Goyal & Sun Builders.</li>
        <li><b>Interactive Digital e-Brochures:</b> 3D architectural floor plans, specs, amenities, and AUDA milestone schedules.</li>
        <li><b>AI Contextual Budget Match:</b> Dynamic builder recommendations triggered inside valuation results based on calculated budget.</li>
        <li><b>Self-Service Sponsor Portal:</b> Builders can submit new schemes and calculate targeted buyer reach.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🎙️ Voice AI Broker & 2031 Time Heatmap</h3>
      <ul>
        <li><b>Multilingual Voice Assistant:</b> Web Speech AI recognition supporting <b>English, Hindi & Gujarati</b> with voice response.</li>
        <li><b>Ahmedabad 2031 Time Machine:</b> Interactive slider (2020–2031) with <b>Metro Phase-2, Bullet Train & GIFT City</b> impact layers.</li>
        <li><b>AI Deal Barometer:</b> Live test comparing any listing asking price against ML fair price and <b>Gujarat Govt Jantri rates</b>.</li>
        <li><b>Stamp Duty Due-Diligence:</b> Exact AMC/AUDA Stamp Duty (4.9% Female / 5.9% Male) and 1% Registration fee breakdown.</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🗺️ Ahmedabad Locality Coverage (29+ Micro-Markets)

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║  Sindhu Bhavan Road (SBR)  •  Bodakdev      •  Ambli        •  Thaltej       •  Satellite    ║
║  SG Highway Corridors      •  Prahlad Nagar •  Science City •  Vastrapur     •  Shela        ║
║  South Bopal               •  Bopal         •  Vaishnodevi  •  Shilaj        •  Gota         ║
║  Motera                    •  Chandkheda    •  Jagatpur     •  Tragad        •  Zundal       ║
║  Chandlodiya               •  Paldi         •  Ellisbridge  •  Navrangpura   •  Maninagar    ║
║  Nikol                     •  Naroda        •  Vatva        •  Odhav         •  Isanpur      ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([👤 Buyer / Investor / Admin])
    
    subgraph Client_Layer ["🖥️ Presentation Layer"]
        FlaskUI["Flask Web App & REST API (frontend.py)"]
    end
    
    subgraph Engine_Layer ["🧠 Core Logic & ML Engine"]
        BackendCore["Business Logic & Auth (backend.py)"]
        MLModel["Log-Linear Regression Model (ml_model.py)"]
        CAGREngine["5-Year Compounding Forecaster"]
        EmailDispatcher["SMTP Live OTP Engine"]
    end
    
    subgraph Storage_Layer ["💾 Hybrid Persistence Layer"]
        MongoDB[("🍃 MongoDB (Primary)")]
        SQLite[("🗄️ SQLite (Auto-Failover)")]
    end
    
    User -->|Interacts| Client_Layer
    Client_Layer -->|REST / JSON| Engine_Layer
    Engine_Layer -->|Queries / Persists| Storage_Layer
    Storage_Layer -.->|Fallback to SQLite if Mongo Offline| SQLite
```

---

## 💻 Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,flask,scikitlearn,mongodb,mysql,js,html,css,vscode,postman" />
</p>

| Layer | Technologies |
| :--- | :--- |
| **Backend & APIs** | Python 3.10+, Flask 3.0+, Werkzeug Security, Gunicorn |
| **Machine Learning** | Scikit-Learn (Log-Linear Fixed Effects), NumPy, Pandas, Joblib |
| **Interactive UI** | Vanilla HTML5 / Modern CSS3 (Cinzel & Outfit typography), JavaScript |
| **Databases** | MongoDB (PyMongo) + SQLite3 (Native Auto-Failover) |
| **Authentication** | SMTP Live Email OTP, SHA-256 / Werkzeug password hashing |

---

## 🚀 Quick Start Guide

### 1. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
*(Optionally configure your SMTP email settings in `.env` for live OTP delivery).*

### 3. Run the Application

* **Option A — Web Application (Flask + REST API):**
  ```bash
  python frontend.py
  # Open http://127.0.0.1:5000 in your browser
  ```

* **Option B — Windows 1-Click Launcher:**
  Simply double-click [`run_app.bat`](file:///c:/Users/ompat/Desktop/VASUDHA%20REAL%20ESTATE%20PRICE%20PREDICTION/VASUDHA%20REAL%20ESTATE%20PRICE%20PREDICTION/run_app.bat)!

---

## 🧪 Automated Testing

The platform includes an automated unit & integration test suite verifying authentication, OTP dispatch, valuation calculations, and database failover:

```bash
python test_vasudha.py
```
```
----------------------------------------------------------------------
Ran 12 tests in 0.514s

OK (12/12 Tests Passing)
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `POST` | `/api/predict` | Calculate instant property valuation & 5-year forecast |
| `GET` | `/api/localities` | Retrieve full list of Ahmedabad localities and base rates |
| `POST` | `/api/compare` | Multi-locality benchmark and appreciation comparison |
| `POST` | `/api/auth/register` | Start user registration & send 6-digit email OTP |
| `POST` | `/api/auth/verify-otp` | Verify registration OTP and activate account |
| `POST` | `/api/auth/login` | Authenticate user credentials & create session |
| `POST` | `/api/auth/forgot-password` | Initiate password reset & dispatch reset OTP |
| `POST` | `/api/share-valuation` | Send comprehensive property report directly via Email |

---

## 👨‍💻 Author

<div align="center">

### **Om Patel**
*Full Stack & AI Developer | Machine Learning Enthusiast*

<p align="center">
  <a href="mailto:ompatel94929@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white"/></a>
</p>

</div>

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
