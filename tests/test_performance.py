import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from db_operations import DBOperator
from services import FlightQueryService, BookingService


class TestPerformance:
    """性能基准测试"""

    @pytest.fixture
    def db(self):
        return DBOperator()

    def test_flight_query_performance(self, db, benchmark):
        service = FlightQueryService(db)

        rows = db.execute_query(
            "SELECT departure_airport, arrival_airport, DATE(departure_time) as date FROM Flight LIMIT 1")
        if not rows:
            pytest.skip("没有可用航班")

        row = rows[0]
        departure = row['departure_airport']
        arrival = row['arrival_airport']
        date = str(row['date'])

        print(f"\n使用查询条件: 出发地={departure}, 目的地={arrival}, 日期={date}")

        def query():
            return service.search_flights(departure=departure, arrival=arrival, date=date)

        result = benchmark(query)
        assert result is not None

    def test_booking_query_performance(self, db, benchmark):
        """测试预订查询性能（不实际下单）"""
        # 直接用 SQL 获取一个真实存在的航班 ID
        rows = db.execute_query("SELECT flight_id FROM Flight LIMIT 1")
        if not rows:
            pytest.skip("没有可用航班")

        flight_id = rows[0]['flight_id']

        def get_seat():
            return db.get_seat_class(flight_id, 'economy')

        result = benchmark(get_seat)
        assert result is not None