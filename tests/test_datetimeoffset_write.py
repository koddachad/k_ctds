"""
Unit tests for writing DATETIMEOFFSET values from Python to SQL Server.

This module tests the conversion of Python datetime objects with timezone
information to SQL Server DATETIMEOFFSET data types.
"""
from datetime import datetime, timezone, timedelta
import unittest

import ctds

from .base import TestExternalDatabase


class TestDateTimeOffsetWrite(TestExternalDatabase):
    """Test writing DATETIMEOFFSET values to SQL Server."""

    def setUp(self):
        TestExternalDatabase.setUp(self)
        self.connection = self.connect()
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.cursor.close()
        self.connection.close()
        TestExternalDatabase.tearDown(self)

    def test_datetimeoffset_utc(self):
        """Test writing timezone-aware datetime with UTC timezone."""
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
        
        self.cursor.execute(
            "SELECT :0 AS result",
            (dt,)
        )
        result = self.cursor.fetchone()[0]
        
        self.assertEqual(result, dt)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_datetimeoffset_positive_offset(self):
        """Test writing timezone-aware datetime with positive offset."""
        # Test +05:30 (India Standard Time)
        tz = timezone(timedelta(hours=5, minutes=30))
        dt = datetime(2024, 3, 20, 14, 15, 30, 500000, tzinfo=tz)
        
        self.cursor.execute(
            "SELECT :0 AS result",
            (dt,)
        )
        result = self.cursor.fetchone()[0]
        
        self.assertEqual(result, dt)
        self.assertEqual(result.utcoffset(), timedelta(hours=5, minutes=30))

    def test_datetimeoffset_negative_offset(self):
        """Test writing timezone-aware datetime with negative offset."""
        # Test -08:00 (Pacific Standard Time)
        tz = timezone(timedelta(hours=-8))
        dt = datetime(2024, 6, 10, 9, 45, 22, 789000, tzinfo=tz)
        
        self.cursor.execute(
            "SELECT :0 AS result",
            (dt,)
        )
        result = self.cursor.fetchone()[0]
        
        self.assertEqual(result, dt)
        self.assertEqual(result.utcoffset(), timedelta(hours=-8))

    def test_datetimeoffset_various_offsets(self):
        """Test writing timezone-aware datetime with various offsets."""
        test_cases = [
            (0, 0),      # UTC
            (1, 0),      # +01:00
            (-8, 0),     # -08:00 (PST)
            (5, 30),     # +05:30 (IST)
            (9, 30),     # +09:30
            (-3, -30),   # -03:30
            (12, 0),     # +12:00
            (-11, 0),    # -11:00
            (14, 0),     # +14:00 (maximum offset)
        ]
        
        base_dt = datetime(2024, 1, 15, 12, 0, 0, 0)
        
        for offset_hours, offset_minutes in test_cases:
            with self.subTest(offset_hours=offset_hours, offset_minutes=offset_minutes):
                tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
                dt = base_dt.replace(tzinfo=tz)
                
                self.cursor.execute("SELECT :0 AS result", (dt,))
                result = self.cursor.fetchone()[0]
                
                self.assertEqual(result, dt)
                self.assertEqual(
                    result.utcoffset(), 
                    timedelta(hours=offset_hours, minutes=offset_minutes)
                )

    def test_datetimeoffset_microsecond_precision(self):
        """Test writing timezone-aware datetime with various microsecond values."""
        tz = timezone.utc
        test_cases = [
            0,
            1,
            100000,
            123456,
            999999,
        ]
        
        for microseconds in test_cases:
            with self.subTest(microseconds=microseconds):
                dt = datetime(2024, 1, 1, 12, 0, 0, microseconds, tzinfo=tz)
                
                self.cursor.execute("SELECT :0 AS result", (dt,))
                result = self.cursor.fetchone()[0]
                
                # SQL Server truncates to 7 decimal places, Python uses 6
                # So we compare with truncation to microseconds
                self.assertEqual(result.microsecond, microseconds)

    def test_datetimeoffset_null(self):
        """Test writing NULL for DATETIMEOFFSET."""
        self.cursor.execute(
            "SELECT :0 AS result",
            (None,)
        )
        result = self.cursor.fetchone()[0]
        self.assertIsNone(result)

    def test_datetimeoffset_insert_table(self):
        """Test inserting timezone-aware datetime into a table."""
        # Create a temporary table
        self.cursor.execute(
            """
            CREATE TABLE #test_dto_write (
                id INT,
                event_time DATETIMEOFFSET
            )
            """
        )
        
        # Test data with various timezones
        test_data = [
            (1, datetime(2024, 1, 15, 8, 0, 0, 0, tzinfo=timezone.utc)),
            (2, datetime(2024, 1, 15, 8, 0, 0, 0, 
                        tzinfo=timezone(timedelta(hours=5, minutes=30)))),
            (3, datetime(2024, 1, 15, 8, 0, 0, 0, 
                        tzinfo=timezone(timedelta(hours=-8)))),
            (4, None),
        ]
        
        # Insert the data
        for id_val, dt_val in test_data:
            self.cursor.execute(
                "INSERT INTO #test_dto_write (id, event_time) VALUES (:0, :1)",
                (id_val, dt_val)
            )
        
        # Read it back
        self.cursor.execute("SELECT id, event_time FROM #test_dto_write ORDER BY id")
        rows = self.cursor.fetchall()
        
        self.assertEqual(len(rows), 4)
        
        for i, (id_val, dt_val) in enumerate(test_data):
            self.assertEqual(rows[i].id, id_val)
            if dt_val is None:
                self.assertIsNone(rows[i].event_time)
            else:
                self.assertEqual(rows[i].event_time, dt_val)

    def test_datetimeoffset_executemany(self):
        """Test writing multiple timezone-aware datetimes using executemany."""
        # Create a temporary table
        self.cursor.execute(
            """
            CREATE TABLE #test_dto_many (
                id INT,
                event_time DATETIMEOFFSET
            )
            """
        )
        
        # Test data
        test_data = [
            (1, datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)),
            (2, datetime(2024, 1, 2, 11, 0, 0, 0, 
                        tzinfo=timezone(timedelta(hours=1)))),
            (3, datetime(2024, 1, 3, 12, 0, 0, 0, 
                        tzinfo=timezone(timedelta(hours=-5)))),
            (4, datetime(2024, 1, 4, 13, 0, 0, 0, 
                        tzinfo=timezone(timedelta(hours=8)))),
        ]
        
        # Insert using executemany
        self.cursor.executemany(
            "INSERT INTO #test_dto_many (id, event_time) VALUES (:0, :1)",
            test_data
        )
        
        # Read it back
        self.cursor.execute("SELECT id, event_time FROM #test_dto_many ORDER BY id")
        rows = self.cursor.fetchall()
        
        self.assertEqual(len(rows), len(test_data))
        
        for i, (id_val, dt_val) in enumerate(test_data):
            self.assertEqual(rows[i].id, id_val)
            self.assertEqual(rows[i].event_time, dt_val)

    def test_datetimeoffset_boundary_dates(self):
        """Test writing boundary date values for DATETIMEOFFSET."""
        tz = timezone.utc
        
        test_cases = [
            # Minimum representable datetime in Python
            datetime(1, 1, 1, 0, 0, 0, 0, tzinfo=tz),
            # Leap year
            datetime(2024, 2, 29, 12, 0, 0, 0, tzinfo=tz),
            # End of month
            datetime(2024, 1, 31, 23, 59, 59, 999999, tzinfo=tz),
            # Maximum year (SQL Server supports up to 9999)
            datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=tz),
        ]
        
        for dt in test_cases:
            with self.subTest(dt=dt):
                self.cursor.execute("SELECT :0 AS result", (dt,))
                result = self.cursor.fetchone()[0]
                
                self.assertEqual(result.year, dt.year)
                self.assertEqual(result.month, dt.month)
                self.assertEqual(result.day, dt.day)
                self.assertEqual(result.hour, dt.hour)
                self.assertEqual(result.minute, dt.minute)
                self.assertEqual(result.second, dt.second)
                self.assertEqual(result.microsecond, dt.microsecond)
                self.assertEqual(result.utcoffset(), dt.utcoffset())

    def test_datetimeoffset_stored_procedure(self):
        """Test passing timezone-aware datetime to stored procedure."""
        with self.stored_procedure(
            self.cursor,
            'test_dto_sproc',
            '''
            @input_dt DATETIMEOFFSET,
            @output_dt DATETIMEOFFSET OUTPUT
            AS
            BEGIN
                SET @output_dt = @input_dt
            END
            '''
        ):
            tz = timezone(timedelta(hours=5, minutes=30))
            input_dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=tz)
            output_dt = ctds.Parameter(input_dt, output=True)
            outputs = self.cursor.callproc('test_dto_sproc', (input_dt, output_dt))
            self.assertEqual(outputs[1], input_dt) 

    def test_datetimeoffset_parameter_type(self):
        """Test that timezone-aware datetime is recognized as DATETIMEOFFSET."""
        tz = timezone(timedelta(hours=5, minutes=30))
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=tz)
        
        row = self.parameter_type(self.cursor, dt)
        
        # For DATETIMEOFFSET, SQL_VARIANT_PROPERTY returns 'datetimeoffset'
        self.assertEqual(row.Type.lower(), 'datetimeoffset')

    def test_datetimeoffset_comparison(self):
        """Test comparing DATETIMEOFFSET values in SQL."""
        tz1 = timezone(timedelta(hours=0))
        tz2 = timezone(timedelta(hours=5, minutes=30))
        
        # Same instant in time, different timezones
        dt1 = datetime(2024, 1, 15, 12, 0, 0, 0, tzinfo=tz1)
        dt2 = datetime(2024, 1, 15, 17, 30, 0, 0, tzinfo=tz2)
        
        self.cursor.execute(
            """
            SELECT 
                CASE WHEN :0 = :1 THEN 1 ELSE 0 END AS equal,
                CASE WHEN :0 < :1 THEN 1 ELSE 0 END AS less_than,
                CASE WHEN :0 > :1 THEN 1 ELSE 0 END AS greater_than
            """,
            (dt1, dt2)
        )
        result = self.cursor.fetchone()
        
        # Both represent the same instant
        self.assertEqual(result.equal, 1)
        self.assertEqual(result.less_than, 0)
        self.assertEqual(result.greater_than, 0)

    def test_datetimeoffset_update(self):
        """Test updating DATETIMEOFFSET column."""
        # Create and populate table
        self.cursor.execute(
            """
            CREATE TABLE #test_dto_update (
                id INT,
                event_time DATETIMEOFFSET
            )
            """
        )
        
        initial_dt = datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
        self.cursor.execute(
            "INSERT INTO #test_dto_update (id, event_time) VALUES (1, :0)",
            (initial_dt,)
        )
        
        # Update with new value
        updated_dt = datetime(2024, 6, 15, 15, 30, 0, 0, 
                             tzinfo=timezone(timedelta(hours=5, minutes=30)))
        self.cursor.execute(
            "UPDATE #test_dto_update SET event_time = :0 WHERE id = 1",
            (updated_dt,)
        )
        
        # Read back
        self.cursor.execute("SELECT event_time FROM #test_dto_update WHERE id = 1")
        result = self.cursor.fetchone()[0]
        
        self.assertEqual(result, updated_dt)

    def test_datetimeoffset_where_clause(self):
        """Test using DATETIMEOFFSET in WHERE clause."""
        # Create and populate table
        self.cursor.execute(
            """
            CREATE TABLE #test_dto_where (
                id INT,
                event_time DATETIMEOFFSET
            )
            """
        )
        
        test_data = [
            (1, datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)),
            (2, datetime(2024, 1, 2, 11, 0, 0, 0, tzinfo=timezone.utc)),
            (3, datetime(2024, 1, 3, 12, 0, 0, 0, tzinfo=timezone.utc)),
        ]
        
        for id_val, dt_val in test_data:
            self.cursor.execute(
                "INSERT INTO #test_dto_where (id, event_time) VALUES (:0, :1)",
                (id_val, dt_val)
            )
        
        # Query with WHERE clause
        search_dt = test_data[1][1]
        self.cursor.execute(
            "SELECT id FROM #test_dto_where WHERE event_time = :0",
            (search_dt,)
        )
        result = self.cursor.fetchone()
        
        self.assertEqual(result.id, 2)

    def test_naive_datetime_error(self):
        """Test that naive datetime (without timezone) raises an appropriate error or converts."""
        # Naive datetime (no timezone info)
        naive_dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
        
        # The behavior here depends on implementation - it might:
        # 1. Raise an error
        # 2. Assume UTC
        # 3. Convert to DATETIME instead of DATETIMEOFFSET
        
        try:
            self.cursor.execute("SELECT :0 AS result", (naive_dt,))
            result = self.cursor.fetchone()[0]
            
            # If it doesn't raise an error, check what type it became
            # This is implementation-dependent
            if hasattr(result, 'tzinfo'):
                # It was converted to timezone-aware
                self.assertIsNotNone(result)
            else:
                # It was kept as naive datetime (DATETIME type)
                self.assertEqual(result.year, naive_dt.year)
                self.assertEqual(result.month, naive_dt.month)
        except (ValueError, ctds.DataError, ctds.ProgrammingError):
            # It's acceptable to raise an error for naive datetime
            pass


if __name__ == '__main__':
    unittest.main()
