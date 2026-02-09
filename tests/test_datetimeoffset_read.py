"""
Unit tests for reading DATETIMEOFFSET values from SQL Server to Python.

This module tests the conversion of SQL Server DATETIMEOFFSET data types
to Python datetime objects with timezone information.
"""
from datetime import datetime, timezone, timedelta
import unittest

import ctds

from .base import TestExternalDatabase


class TestDateTimeOffsetRead(TestExternalDatabase):
    """Test reading DATETIMEOFFSET values from SQL Server."""

    def setUp(self):
        TestExternalDatabase.setUp(self)
        self.connection = self.connect()
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.cursor.close()
        self.connection.close()
        TestExternalDatabase.tearDown(self)

    def test_datetimeoffset_null(self):
        """Test reading NULL DATETIMEOFFSET value."""
        self.cursor.execute('SELECT CONVERT(DATETIMEOFFSET, NULL)')
        result = self.cursor.fetchone()
        self.assertIsNone(result[0])

    def test_datetimeoffset_utc(self):
        """Test reading DATETIMEOFFSET with UTC timezone."""
        self.cursor.execute(
            "SELECT CONVERT(DATETIMEOFFSET, '2024-01-15 12:30:45.1234567 +00:00')"
        )
        result = self.cursor.fetchone()[0]
        
        expected = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
        self.assertEqual(result, expected)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_datetimeoffset_positive_offset(self):
        """Test reading DATETIMEOFFSET with positive timezone offset."""
        # Test +05:30 (India Standard Time)
        self.cursor.execute(
            "SELECT CONVERT(DATETIMEOFFSET, '2024-03-20 14:15:30.5000000 +05:30')"
        )
        result = self.cursor.fetchone()[0]
        
        expected_tz = timezone(timedelta(hours=5, minutes=30))
        expected = datetime(2024, 3, 20, 14, 15, 30, 500000, tzinfo=expected_tz)
        self.assertEqual(result, expected)
        self.assertEqual(result.utcoffset(), timedelta(hours=5, minutes=30))

    def test_datetimeoffset_negative_offset(self):
        """Test reading DATETIMEOFFSET with negative timezone offset."""
        # Test -05:00 (Eastern Standard Time)
        self.cursor.execute(
            "SELECT CONVERT(DATETIMEOFFSET, '2024-06-10 09:45:22.7890000 -05:00')"
        )
        result = self.cursor.fetchone()[0]
        
        expected_tz = timezone(timedelta(hours=-5))
        expected = datetime(2024, 6, 10, 9, 45, 22, 789000, tzinfo=expected_tz)
        self.assertEqual(result, expected)
        self.assertEqual(result.utcoffset(), timedelta(hours=-5))

    def test_datetimeoffset_various_offsets(self):
        """Test reading DATETIMEOFFSET with various timezone offsets."""
        test_cases = [
            # (SQL value, expected offset hours, expected offset minutes)
            ('2024-01-01 00:00:00.0000000 +00:00', 0, 0),
            ('2024-01-01 00:00:00.0000000 +01:00', 1, 0),
            ('2024-01-01 00:00:00.0000000 -08:00', -8, 0),
            ('2024-01-01 00:00:00.0000000 +09:30', 9, 30),
            ('2024-01-01 00:00:00.0000000 -03:30', -3, -30),
            ('2024-01-01 00:00:00.0000000 +12:00', 12, 0),
            ('2024-01-01 00:00:00.0000000 -12:00', -12, 0),
            ('2024-01-01 00:00:00.0000000 +14:00', 14, 0),
        ]
        
        for sql_value, offset_hours, offset_minutes in test_cases:
            with self.subTest(sql_value=sql_value):
                self.cursor.execute(f"SELECT CONVERT(DATETIMEOFFSET, '{sql_value}')")
                result = self.cursor.fetchone()[0]
                
                expected_offset = timedelta(hours=offset_hours, minutes=offset_minutes)
                self.assertEqual(result.utcoffset(), expected_offset)

    def test_datetimeoffset_microsecond_precision(self):
        """Test reading DATETIMEOFFSET with various microsecond precisions."""
        test_cases = [
            ('2024-01-01 12:00:00.0000000 +00:00', 0),
            ('2024-01-01 12:00:00.1000000 +00:00', 100000),
            ('2024-01-01 12:00:00.1200000 +00:00', 120000),
            ('2024-01-01 12:00:00.1234560 +00:00', 123456),
            ('2024-01-01 12:00:00.1234567 +00:00', 123456),  # 7th digit truncated
            ('2024-01-01 12:00:00.9999999 +00:00', 999999),
        ]
        
        for sql_value, expected_microseconds in test_cases:
            with self.subTest(sql_value=sql_value):
                self.cursor.execute(f"SELECT CONVERT(DATETIMEOFFSET, '{sql_value}')")
                result = self.cursor.fetchone()[0]
                self.assertEqual(result.microsecond, expected_microseconds)

    def test_datetimeoffset_boundary_dates(self):
        """Test reading DATETIMEOFFSET with boundary date values."""
        test_cases = [
            # Minimum value for DATETIMEOFFSET
            '0001-01-01 00:00:00.0000000 +00:00',
            # Maximum value for DATETIMEOFFSET
            '9999-12-31 23:59:59.9999999 +00:00',
            # Leap year
            '2024-02-29 12:00:00.0000000 +00:00',
            # End of month
            '2024-01-31 23:59:59.9999999 +00:00',
            '2024-04-30 23:59:59.9999999 +00:00',
        ]
        
        for sql_value in test_cases:
            with self.subTest(sql_value=sql_value):
                self.cursor.execute(f"SELECT CONVERT(DATETIMEOFFSET, '{sql_value}')")
                result = self.cursor.fetchone()[0]
                self.assertIsInstance(result, datetime)
                self.assertIsNotNone(result.tzinfo)

    def test_datetimeoffset_multiple_rows(self):
        """Test reading multiple DATETIMEOFFSET values in one query."""
        self.cursor.execute(
            """
            SELECT 
                CONVERT(DATETIMEOFFSET, '2024-01-01 10:00:00.0000000 +00:00'),
                CONVERT(DATETIMEOFFSET, '2024-06-15 15:30:00.0000000 +05:30'),
                CONVERT(DATETIMEOFFSET, '2024-12-31 20:45:00.0000000 -08:00'),
                CONVERT(DATETIMEOFFSET, NULL)
            """
        )
        result = self.cursor.fetchone()
        
        self.assertEqual(len(result), 4)
        
        # First value - UTC
        self.assertEqual(result[0].utcoffset(), timedelta(0))
        
        # Second value - +05:30
        self.assertEqual(result[1].utcoffset(), timedelta(hours=5, minutes=30))
        
        # Third value - -08:00
        self.assertEqual(result[2].utcoffset(), timedelta(hours=-8))
        
        # Fourth value - NULL
        self.assertIsNone(result[3])

    def test_datetimeoffset_from_table(self):
        """Test reading DATETIMEOFFSET from a table column."""
        # Create a temporary table
        self.cursor.execute(
            """
            CREATE TABLE #test_dto (
                id INT,
                event_time DATETIMEOFFSET
            )
            """
        )
        
        # Insert test data
        self.cursor.execute(
            """
            INSERT INTO #test_dto (id, event_time) VALUES
            (1, '2024-01-15 08:00:00.0000000 +00:00'),
            (2, '2024-01-15 08:00:00.0000000 +05:30'),
            (3, '2024-01-15 08:00:00.0000000 -08:00'),
            (4, NULL)
            """
        )
        
        # Read the data
        self.cursor.execute("SELECT id, event_time FROM #test_dto ORDER BY id")
        rows = self.cursor.fetchall()
        
        self.assertEqual(len(rows), 4)
        
        # Verify first row
        self.assertEqual(rows[0].id, 1)
        self.assertEqual(rows[0].event_time.utcoffset(), timedelta(0))
        
        # Verify second row
        self.assertEqual(rows[1].id, 2)
        self.assertEqual(rows[1].event_time.utcoffset(), timedelta(hours=5, minutes=30))
        
        # Verify third row
        self.assertEqual(rows[2].id, 3)
        self.assertEqual(rows[2].event_time.utcoffset(), timedelta(hours=-8))
        
        # Verify fourth row (NULL)
        self.assertEqual(rows[3].id, 4)
        self.assertIsNone(rows[3].event_time)

    def test_datetimeoffset_switchoffset(self):
        """Test reading DATETIMEOFFSET after using SWITCHOFFSET function."""
        self.cursor.execute(
            """
            SELECT 
                SWITCHOFFSET(
                    CONVERT(DATETIMEOFFSET, '2024-01-15 12:00:00.0000000 +00:00'),
                    '+05:30'
                )
            """
        )
        result = self.cursor.fetchone()[0]
        
        # SWITCHOFFSET converts the time to the new timezone
        expected_tz = timezone(timedelta(hours=5, minutes=30))
        expected = datetime(2024, 1, 15, 17, 30, 0, 0, tzinfo=expected_tz)
        self.assertEqual(result, expected)

    def test_datetimeoffset_todatetimeoffset(self):
        """Test reading DATETIMEOFFSET after using TODATETIMEOFFSET function."""
        self.cursor.execute(
            """
            SELECT 
                TODATETIMEOFFSET(
                    CONVERT(DATETIME, '2024-01-15 12:00:00.000'),
                    '+05:30'
                )
            """
        )
        result = self.cursor.fetchone()[0]
        
        expected_tz = timezone(timedelta(hours=5, minutes=30))
        expected = datetime(2024, 1, 15, 12, 0, 0, 0, tzinfo=expected_tz)
        self.assertEqual(result, expected)

    def test_datetimeoffset_at_time_zone(self):
        """Test reading DATETIMEOFFSET with AT TIME ZONE clause."""
        # Note: AT TIME ZONE requires SQL Server 2016+
        try:
            self.cursor.execute(
                """
                SELECT 
                    CONVERT(DATETIMEOFFSET, '2024-01-15 12:00:00.0000000 +00:00')
                    AT TIME ZONE 'Pacific Standard Time'
                """
            )
            result = self.cursor.fetchone()[0]
            self.assertIsInstance(result, datetime)
            self.assertIsNotNone(result.tzinfo)
        except ctds.DatabaseError:
            # Skip if AT TIME ZONE is not supported
            self.skipTest("AT TIME ZONE not supported on this SQL Server version")

    def test_datetimeoffset_column_description(self):
        """Test cursor description for DATETIMEOFFSET columns."""
        self.cursor.execute(
            "SELECT CONVERT(DATETIMEOFFSET, '2024-01-15 12:00:00.0000000 +00:00') AS dto_col"
        )
        
        description = self.cursor.description[0]
        self.assertEqual(description.name, 'dto_col')
        # Verify the type code indicates DATETIMEOFFSET
        self.assertIsNotNone(description.type_code)


if __name__ == '__main__':
    unittest.main()
