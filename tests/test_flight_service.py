import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock
from services import FlightQueryService


class TestFlightQueryService:

    def test_search_flights(self):
        mock_flight_repo = Mock()
        mock_flight_repo.get_available_flights.return_value = [
            {'flight_no': 'CA123', 'airline': '国航'}
        ]

        service = FlightQueryService(mock_flight_repo)
        results = service.search_flights(departure='北京', arrival='上海', date='2025-05-20')

        assert len(results) == 1
        assert results[0]['flight_no'] == 'CA123'
        mock_flight_repo.get_available_flights.assert_called_once_with('北京', '上海', '2025-05-20')

    def test_get_flight_detail(self):
        mock_flight_repo = Mock()
        mock_flight_repo.get_flight_by_id.return_value = {'flight_id': 1, 'flight_no': 'CA123'}

        service = FlightQueryService(mock_flight_repo)
        result = service.get_flight_detail(1)

        assert result['flight_no'] == 'CA123'
        mock_flight_repo.get_flight_by_id.assert_called_once_with(1)

    def test_get_flight_detail_not_found(self):
        mock_flight_repo = Mock()
        mock_flight_repo.get_flight_by_id.return_value = None

        service = FlightQueryService(mock_flight_repo)
        result = service.get_flight_detail(999)

        assert result is None