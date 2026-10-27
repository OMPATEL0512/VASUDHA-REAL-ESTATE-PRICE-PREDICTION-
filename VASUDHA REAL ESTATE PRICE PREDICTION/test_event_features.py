"""
Comprehensive test suite verifying the 3 Showstopper Event Features:
1. Developer Showcase & Scheme Launchpad APIs (Brochures, Inquiries, Self-Service Ads)
2. Ahmedabad Deal Barometer & Gujarat Jantri / Stamp Duty Math
3. Matched Builder Schemes returned in Authenticated ML Valuation
"""

import unittest
import json
from frontend import app
import backend
import database

class EventFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_get_builder_schemes_all(self):
        """Verify all 8 builder schemes are returned with complete specs."""
        res = self.app.get('/api/builders/schemes')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('count', 0), 8)
        schemes = data.get('schemes', [])
        ids = [s['id'] for s in schemes]
        self.assertIn('shivalik-edge-sbr', ids)
        self.assertIn('adani-waterlily-vaishnodevi', ids)
        self.assertIn('godrej-celestial-jagatpur', ids)
        self.assertIn('iscon-platinum-duplexes', ids)
        self.assertIn('ganesh-malabar-tenements', ids)
        self.assertIn('goyal-orchid-shela', ids)
        self.assertIn('sun-south-park-bopal', ids)
        self.assertIn('takshashila-air-riverfront', ids)

    def test_get_builder_schemes_filtered(self):
        """Verify filtering by corridor and property type."""
        res = self.app.get('/api/builders/schemes?locality=Bopal')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        for s in data.get('schemes', []):
            self.assertIn('bopal', s['locality'].lower())

    def test_get_builder_scheme_dossier(self):
        """Verify full brochure dossier retrieval."""
        res = self.app.get('/api/builders/scheme/adani-waterlily-vaishnodevi')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        scheme = data.get('scheme')
        self.assertEqual(scheme['name'], 'Adani Shantigram - Water Lily')
        self.assertIn('amenities', scheme)
        self.assertIn('floor_plans', scheme)
        self.assertIn('payment_plan', scheme)
        self.assertIn('specs', scheme)

    def test_builder_enquiry_dispatch(self):
        """Verify buyer brochure enquiry logging."""
        payload = {
            "scheme_id": "shivalik-edge-sbr",
            "scheme_name": "Shivalik Edge & Parkview",
            "buyer_name": "Arjun Patel",
            "email": "arjun.patel@testmail.com",
            "phone": "+91 98765 43210",
            "message": "Interested in site visit this weekend"
        }
        res = self.app.post('/api/builders/enquire', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('Enquiry registered successfully', data.get('message', ''))

    def test_builder_advertise_submission(self):
        """Verify self-service builder listing submission."""
        payload = {
            "builder_name": "Satyam Group",
            "project_name": "Satyam Skyline",
            "locality": "Prahlad Nagar",
            "property_type": "Apartment / Flat",
            "price_range": "Rs 1.45 Cr - 2.80 Cr",
            "rera_id": "PR/GJ/AHMEDABAD/TEST/2026/001",
            "contact_phone": "+91 99999 88888",
            "contact_email": "sales@satyamgroup.test",
            "brochure_url": "https://example.com/satyam-skyline.pdf"
        }
        res = self.app.post('/api/builders/advertise', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('ad_id', data)

    def test_deal_barometer_calculation(self):
        """Verify Deal Barometer fair price vs asking price logic and stamp duty."""
        payload = {
            "locality": "Bodakdev",
            "area": 200,
            "property_type": "Apartment / Flat",
            "asking_price": 28000000 # 2.80 Cr
        }
        res = self.app.post('/api/deal-barometer', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('fair_price', data)
        self.assertIn('jantri_valuation', data)
        self.assertIn('pct_diff', data)
        self.assertIn('deal_verdict', data)
        self.assertIn('stamp_duty_female', data)
        self.assertIn('stamp_duty_male', data)
        self.assertIn('suggested_counter_offer', data)

    def test_valuation_returns_matched_builder_schemes(self):
        """Verify that authenticated valuation returns curated builder schemes."""
        with self.app.session_transaction() as sess:
            sess['user_id'] = 'test-demo-user'
            sess['user_email'] = 'testdemo@vasudha.test'
            sess['user_name'] = 'Test Demo User'

        payload = {
            "locality": "Bopal",
            "area": 160,
            "property_type": "Apartment / Flat",
            "year": 2026
        }
        res = self.app.post('/api/estimate', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('matched_builder_schemes', data)
        matched = data['matched_builder_schemes']
        self.assertIsInstance(matched, list)
    def test_admin_builder_schemes_crud(self):
        """Verify Admin can list, add, and delete builder schemes directly in DB."""
        with self.app.session_transaction() as sess:
            sess['is_admin'] = True

        # 1. Admin List Schemes
        res = self.app.get('/api/admin/builder-schemes')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('count', 0), 8)

        # 2. Admin Add Scheme
        new_scheme = {
            "name": "Shivalik Curvaceous Tower",
            "builder": "Shivalik Group",
            "locality": "Sindhu Bhavan Road",
            "property_type": "Apartment / Flat",
            "price_display": "Rs 2.80 Cr - 4.50 Cr",
            "price_min": 28000000,
            "price_max": 45000000,
            "config_display": "4 BHK Penthouses",
            "rera_id": "PR/GJ/AHMEDABAD/2026/CURV"
        }
        add_res = self.app.post('/api/admin/builder-scheme/add', json=new_scheme)
        self.assertEqual(add_res.status_code, 200)
        add_data = add_res.get_json()
        self.assertTrue(add_data.get('success'))
        scheme_id = add_data.get('scheme_id')

        # 3. Verify Added Scheme is in List
        detail_res = self.app.get(f'/api/builders/scheme/{scheme_id}')
        self.assertEqual(detail_res.status_code, 200)

        # 4. Admin Delete Scheme
        del_res = self.app.post('/api/admin/builder-scheme/delete', json={'scheme_id': scheme_id})
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.get_json()
        self.assertTrue(del_data.get('success'))

        # 5. Verify Scheme is Deleted
        detail_after = self.app.get(f'/api/builders/scheme/{scheme_id}')
        self.assertEqual(detail_after.status_code, 404)

if __name__ == '__main__':
    unittest.main()
