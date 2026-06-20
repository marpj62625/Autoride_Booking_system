import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routers.conflict_routes import conflict_bp
from flask import Flask

class TestBookingExtensionsAndConflicts(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(conflict_bp)
        self.client = self.app.test_client()

    @patch('routers.conflict_routes.get_cursor')
    def test_get_my_affected_bookings(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            {
                'id': 101,
                'user_id': 1,
                'vehicle_id': 50,
                'start_date': '2026-06-25',
                'end_date': '2026-06-28',
                'conflict_record_id': 1,
                'resolution_status': 'Pending',
                'resolution_deadline': '2026-06-23 12:00:00',
                'brand': 'Toyota',
                'model': 'Vios',
                'plate_number': 'ABC 123',
                'vehicle_image': 'vios.jpg'
            }
        ]
        
        response = self.client.get('/api/conflicts/my-affected-bookings?user_id=1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], 101)

    @patch('routers.conflict_routes.get_alternative_vehicles')
    def test_get_conflict_alternatives_with_results(self, mock_get_alternatives):
        mock_get_alternatives.return_value = [
            {
                "vehicle_id": 51,
                "brand": "Toyota",
                "model": "Vios",
                "daily_rate": 2000.0,
                "vehicle_type": "Sedan",
                "tier": 1,
                "tier_label": "Perfect Match",
                "price_diff": 0.0
            }
        ]
        
        response = self.client.get('/api/conflicts/1/alternatives')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['alternatives_available'])
        self.assertEqual(len(data['alternatives']), 1)

    @patch('routers.conflict_routes.get_alternative_vehicles')
    def test_get_conflict_alternatives_no_match(self, mock_get_alternatives):
        # Empty alternatives test the "No Match 🚫" constraint
        mock_get_alternatives.return_value = []
        
        response = self.client.get('/api/conflicts/1/alternatives')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['alternatives_available'])
        self.assertEqual(len(data['alternatives']), 0)
        self.assertEqual(data['message'], "No alternative vehicles available")

    @patch('routers.conflict_routes.resolve_conflict_alternative')
    def test_select_alternative_success(self, mock_resolve):
        mock_resolve.return_value = True
        
        response = self.client.post('/api/conflicts/1/select-alternative', json={
            "selected_vehicle_id": 51
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], "Vehicle successfully swapped. Conflict resolved.")

    @patch('routers.conflict_routes.resolve_conflict_refund')
    def test_request_conflict_refund(self, mock_resolve):
        mock_resolve.return_value = True
        
        response = self.client.post('/api/conflicts/1/refund')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], "Booking cancelled. Full refund will be processed immediately.")

if __name__ == '__main__':
    unittest.main()
