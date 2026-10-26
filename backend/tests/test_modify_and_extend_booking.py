import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TestModifyAndExtendBooking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.ctx.pop()

    @patch('notifications.notification_service.notify_user')
    @patch('app.commit_db')
    @patch('app.get_cursor')
    def test_modify_confirmed_booking_success(self, mock_get_cursor, mock_commit, mock_notify):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        # Mock current booking
        mock_cursor.fetchone.side_effect = [
            # 1. Fetch current booking
            {
                'id': 100,
                'total_price': 5000.0,
                'daily_rate': 2000.0,
                'status': 'Confirmed',
                'amount_paid': 2000.0,
                'payment_status': 'Partially Paid',
                'addon_price': 500.0,
                'insurance_price': 500.0,
                'old_start': '2026-11-01',
                'old_end': '2026-11-03',
                'old_start_time': '09:00',
                'old_end_time': '09:00',
                'vehicle_id': 10,
                'user_id': 1
            },
            # 2. max_booking_duration_days
            {'value': '30'},
            # 3. overlap check (no overlap)
            None,
            # 4. long_term_discount_days
            {'value': '7'},
            # 5. long_term_discount_percent
            {'value': '10'}
        ]
        # Blackout dates check
        mock_cursor.fetchall.return_value = []

        response = self.client.post('/api/modify-booking', json={
            'booking_id': 100,
            'start_date': '2026-11-02',
            'start_time': '10:00',
            'end_date': '2026-11-05',
            'end_time': '10:00'
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('successfully modified', data['message'])
        self.assertEqual(data['new_days'], 3)
        self.assertEqual(data['start_date'], '2026-11-02')
        self.assertEqual(data['start_time'], '10:00')
        self.assertEqual(data['end_date'], '2026-11-05')
        self.assertEqual(data['end_time'], '10:00')

    @patch('notifications.notification_service.notify_user')
    @patch('app.commit_db')
    @patch('app.get_cursor')
    def test_extend_ongoing_booking_locks_start_schedule(self, mock_get_cursor, mock_commit, mock_notify):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        # Mock ongoing booking
        mock_cursor.fetchone.side_effect = [
            # 1. Fetch current booking
            {
                'id': 101,
                'total_price': 4000.0,
                'daily_rate': 2000.0,
                'status': 'Ongoing',
                'amount_paid': 4000.0,
                'payment_status': 'Paid',
                'addon_price': 0.0,
                'insurance_price': 0.0,
                'old_start': '2026-11-01',
                'old_end': '2026-11-03',
                'old_start_time': '08:00',
                'old_end_time': '08:00',
                'vehicle_id': 10,
                'user_id': 2
            },
            # 2. max_booking_duration_days
            {'value': '30'},
            # 3. overlap check
            None,
            # 4. long_term_discount_days
            {'value': '7'},
            # 5. long_term_discount_percent
            {'value': '10'}
        ]
        mock_cursor.fetchall.return_value = []

        # Client attempts to change start_date & start_time during extension, but ongoing must lock it
        response = self.client.post('/api/extend-booking', json={
            'booking_id': 101,
            'start_date': '2026-11-02', # Should be ignored / locked to 2026-11-01
            'start_time': '12:00',       # Should be ignored / locked to 08:00
            'end_date': '2026-11-05',
            'end_time': '08:00'
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('extended', data['message'])
        self.assertEqual(data['start_date'], '2026-11-01') # Original start preserved
        self.assertEqual(data['start_time'], '08:00')      # Original start time preserved
        self.assertEqual(data['end_date'], '2026-11-05')
        self.assertEqual(data['end_time'], '08:00')
        self.assertEqual(data['new_days'], 4)

    @patch('app.get_cursor')
    def test_reject_extension_earlier_than_current_return(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            'id': 102,
            'total_price': 4000.0,
            'daily_rate': 2000.0,
            'status': 'Picked Up',
            'amount_paid': 4000.0,
            'payment_status': 'Paid',
            'addon_price': 0.0,
            'insurance_price': 0.0,
            'old_start': '2026-11-01',
            'old_end': '2026-11-05',
            'old_start_time': '08:00',
            'old_end_time': '12:00',
            'vehicle_id': 10,
            'user_id': 3
        }

        response = self.client.post('/api/modify-booking', json={
            'booking_id': 102,
            'end_date': '2026-11-04',
            'end_time': '10:00'
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('cannot be earlier than current scheduled return', data['error'])

    @patch('app.get_cursor')
    def test_reject_end_before_start(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            'id': 103,
            'total_price': 2000.0,
            'daily_rate': 2000.0,
            'status': 'Confirmed',
            'amount_paid': 0.0,
            'payment_status': 'Unpaid',
            'addon_price': 0.0,
            'insurance_price': 0.0,
            'old_start': '2026-11-05',
            'old_end': '2026-11-06',
            'old_start_time': '10:00',
            'old_end_time': '10:00',
            'vehicle_id': 10,
            'user_id': 4
        }

        response = self.client.post('/api/modify-booking', json={
            'booking_id': 103,
            'start_date': '2026-11-05',
            'start_time': '15:00',
            'end_date': '2026-11-05',
            'end_time': '14:00'
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Return date and time must be after pickup date and time', data['error'])

    @patch('app.get_cursor')
    def test_overlap_conflict_rejected(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Fetch current booking
            {
                'id': 104,
                'total_price': 2000.0,
                'daily_rate': 2000.0,
                'status': 'Confirmed',
                'amount_paid': 0.0,
                'payment_status': 'Unpaid',
                'addon_price': 0.0,
                'insurance_price': 0.0,
                'old_start': '2026-11-01',
                'old_end': '2026-11-02',
                'old_start_time': '09:00',
                'old_end_time': '09:00',
                'vehicle_id': 10,
                'user_id': 5
            },
            # 2. max_booking_duration_days
            {'value': '30'},
            # 3. overlap query finds an overlapping booking
            {
                'id': 205,
                'start_date': '2026-11-03',
                'end_date': '2026-11-05',
                'start_time': '10:00',
                'end_time': '10:00',
                'status': 'Confirmed',
                'next_available': '2026-11-06'
            }
        ]
        mock_cursor.fetchall.return_value = []

        response = self.client.post('/api/modify-booking', json={
            'booking_id': 104,
            'start_date': '2026-11-02',
            'start_time': '09:00',
            'end_date': '2026-11-04',
            'end_time': '09:00'
        })

        self.assertEqual(response.status_code, 409)
        data = response.get_json()
        self.assertIn('occupied by booking #205', data['error'])

    @patch('app.get_cursor')
    def test_preview_mode_returns_pricing_without_updating_db(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            # 1. Fetch current booking
            {
                'id': 105,
                'total_price': 2000.0,
                'daily_rate': 1500.0,
                'status': 'Confirmed',
                'amount_paid': 1000.0,
                'payment_status': 'Partially Paid',
                'addon_price': 200.0,
                'insurance_price': 300.0,
                'old_start': '2026-11-01',
                'old_end': '2026-11-02',
                'old_start_time': '08:00',
                'old_end_time': '08:00',
                'vehicle_id': 12,
                'user_id': 6
            },
            # 2. max_booking_duration_days
            {'value': '30'},
            # 3. overlap check
            None,
            # 4. long_term_discount_days
            {'value': '7'},
            # 5. long_term_discount_percent
            {'value': '10'}
        ]
        mock_cursor.fetchall.return_value = []

        response = self.client.post('/api/modify-booking', json={
            'booking_id': 105,
            'start_date': '2026-11-01',
            'start_time': '08:00',
            'end_date': '2026-11-04',
            'end_time': '08:00',
            'preview': True
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['new_days'], 3)
        self.assertEqual(data['new_base_price'], 4500.0)
        self.assertEqual(data['new_addon_price'], 600.0)
        self.assertEqual(data['new_insurance_price'], 900.0)
        self.assertEqual(data['new_total'], 6000.0)
        self.assertEqual(data['new_balance'], 5000.0)

if __name__ == '__main__':
    unittest.main()
