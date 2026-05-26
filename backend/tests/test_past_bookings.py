"""
Unit tests for past bookings endpoint
Tests pagination, sorting, and data retrieval functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routers.booking_routes import booking_bp
from flask import Flask


class TestPastBookingsEndpoint(unittest.TestCase):
    """Test cases for the /api/bookings/past endpoint"""
    
    def setUp(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.register_blueprint(booking_bp)
        self.client = self.app.test_client()
        
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_default_params(self, mock_get_cursor):
        """Test fetching past bookings with default parameters"""
        # Mock cursor
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        # Mock count query result
        mock_cursor.fetchone.side_effect = [
            {'total': 25},  # Total count
        ]
        
        # Mock bookings query result
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'user_id': 1,
                'customer_name': 'John Doe',
                'car': 'Toyota Camry',
                'start_date': '2024-01-01',
                'end_date': '2024-01-05',
                'total_price': 5000.00,
                'completion_date': '2024-01-05 18:00:00',
                'status': 'Completed',
                'payment_status': 'Paid'
            }
        ]
        
        # Make request
        response = self.client.get('/api/bookings/past')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertIn('bookings', data)
        self.assertIn('page', data)
        self.assertIn('page_size', data)
        self.assertIn('total', data)
        self.assertIn('total_pages', data)
        
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['page_size'], 10)
        self.assertEqual(data['total'], 25)
        self.assertEqual(data['total_pages'], 3)
        self.assertEqual(len(data['bookings']), 1)
        
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_with_pagination(self, mock_get_cursor):
        """Test pagination parameters"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'total': 100}
        mock_cursor.fetchall.return_value = []
        
        # Request page 2 with page_size 25
        response = self.client.get('/api/bookings/past?page=2&page_size=25')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertEqual(data['page'], 2)
        self.assertEqual(data['page_size'], 25)
        self.assertEqual(data['total_pages'], 4)
        
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_invalid_page_size(self, mock_get_cursor):
        """Test that invalid page_size defaults to 10"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'total': 50}
        mock_cursor.fetchall.return_value = []
        
        # Request with invalid page_size
        response = self.client.get('/api/bookings/past?page_size=15')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Should default to 10
        self.assertEqual(data['page_size'], 10)
        
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_sorting(self, mock_get_cursor):
        """Test different sorting options"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'total': 10}
        mock_cursor.fetchall.return_value = []
        
        # Test each sort option
        sort_options = [
            'completion_date_desc',
            'completion_date_asc',
            'customer_name',
            'total_price_desc',
            'total_price_asc'
        ]
        
        for sort_by in sort_options:
            response = self.client.get(f'/api/bookings/past?sort_by={sort_by}')
            self.assertEqual(response.status_code, 200)
            
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_empty_result(self, mock_get_cursor):
        """Test when no past bookings exist"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'total': 0}
        mock_cursor.fetchall.return_value = []
        
        response = self.client.get('/api/bookings/past')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['total_pages'], 1)
        self.assertEqual(len(data['bookings']), 0)
        
    @patch('routers.booking_routes.get_cursor')
    def test_get_past_bookings_negative_page(self, mock_get_cursor):
        """Test that negative page numbers default to 1"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = {'total': 50}
        mock_cursor.fetchall.return_value = []
        
        response = self.client.get('/api/bookings/past?page=-1')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Should default to page 1
        self.assertEqual(data['page'], 1)


class TestPastBookingsPaginationLogic(unittest.TestCase):
    """Test pagination calculation logic"""
    
    def test_pagination_calculation(self):
        """Test pagination math"""
        test_cases = [
            # (total_items, page_size, expected_pages)
            (0, 10, 1),
            (5, 10, 1),
            (10, 10, 1),
            (11, 10, 2),
            (25, 10, 3),
            (100, 25, 4),
            (101, 25, 5),
        ]
        
        for total, page_size, expected_pages in test_cases:
            calculated_pages = (total + page_size - 1) // page_size if total > 0 else 1
            self.assertEqual(calculated_pages, expected_pages,
                           f"Failed for total={total}, page_size={page_size}")
            
    def test_offset_calculation(self):
        """Test offset calculation for pagination"""
        test_cases = [
            # (page, page_size, expected_offset)
            (1, 10, 0),
            (2, 10, 10),
            (3, 10, 20),
            (1, 25, 0),
            (2, 25, 25),
            (5, 50, 200),
        ]
        
        for page, page_size, expected_offset in test_cases:
            calculated_offset = (page - 1) * page_size
            self.assertEqual(calculated_offset, expected_offset,
                           f"Failed for page={page}, page_size={page_size}")


if __name__ == '__main__':
    unittest.main()
