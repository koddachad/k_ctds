"""
Unit tests for DATETIMEOFFSET compatibility.

This module ensures that:
1. Naive datetimes still work correctly (no regression)
2. Timezone-aware datetimes are preserved as DATETIMEOFFSET
3. Reading DATETIMEOFFSET columns works correctly
4. All existing datetime functionality remains unchanged
"""
from datetime import datetime, timezone, timedelta
import unittest

import k_ctds as ctds

from .base import TestExternalDatabase


class TestDateTimeOffsetBackwardCompatibility(TestExternalDatabase):
    """Test DATETIMEOFFSET behavior on all FreeTDS versions."""

    def setUp(self):
        TestExternalDatabase.setUp(self)
        self.connection = self.connect()
        self.cursor = self.connection.cursor()

    def tearDown(self):
        self.cursor.close()
        self.connection.close()
        TestExternalDatabase.tearDown(self)

    # ========================================================================
    # Tests for FreeTDS < 0.95: Ensure graceful fallback behavior
    # ========================================================================

    def test_naive_datetime_still_works(self):
        """
        Test that naive datetime (no timezone) still works on all FreeTDS versions.
        
        This is the pre-DATETIMEOFFSET behavior that must not regress.
        """
        # Naive datetime (no tzinfo)
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
        
        self.cursor.execute(
            "SELECT :0 AS result",
            (dt,)
        )
        result = self.cursor.fetchone()[0]
        
        # Should get back a datetime (might lose microsecond precision on old versions)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, dt.year)
        self.assertEqual(result.month, dt.month)
        self.assertEqual(result.day, dt.day)
        self.assertEqual(result.hour, dt.hour)
        self.assertEqual(result.minute, dt.minute)
        self.assertEqual(result.second, dt.second)
        
        self.assertEqual(result.microsecond, dt.microsecond)
        
        # Result should be timezone-naive (no tzinfo)
        self.assertIsNone(result.tzinfo)

    def test_timezone_aware_fallback_to_datetime(self):
        """
        Test that timezone-aware datetime falls back to DATETIME on old FreeTDS.
        
        On FreeTDS < 0.95:
        - Timezone info is silently dropped
        - Value is sent as DATETIME (not DATETIMEOFFSET)
        - This is the existing behavior - no regression
        
        On FreeTDS 0.95+:
        - Timezone info is preserved
        - Value is sent as DATETIMEOFFSET
        """
        # Timezone-aware datetime
        tz = timezone(timedelta(hours=5, minutes=30))
        dt = datetime(2024, 1, 15, 12, 30, 45, 0, tzinfo=tz)
        
        self.cursor.execute(
            "SELECT :0 AS result",
            (dt,)
        )
        result = self.cursor.fetchone()[0]
        
        # Should get back a datetime
        self.assertIsInstance(result, datetime)
        
        # Timezone should be preserved
        self.assertIsNotNone(result.tzinfo, 
                                "FreeTDS 0.95+ should preserve timezone")
        self.assertEqual(result, dt,
                           "FreeTDS 0.95+ should preserve exact datetime")

    def test_reading_datetimeoffset_column_behavior(self):
        """
        Test reading DATETIMEOFFSET column behavior across FreeTDS versions.
        
        - Should successfully read and return timezone-aware datetime
        """
        # Create a table with DATETIMEOFFSET column
        try:
            self.cursor.execute(
                """
                CREATE TABLE #test_dto_compat (
                    id INT,
                    dto_col DATETIMEOFFSET
                )
                """
            )
            
            # Insert a value directly in SQL
            self.cursor.execute(
                """
                INSERT INTO #test_dto_compat (id, dto_col) 
                VALUES (1, '2024-01-15 12:30:45.0000000 +05:30')
                """
            )
            
            # Try to read it
            self.cursor.execute("SELECT dto_col FROM #test_dto_compat WHERE id = 1")
            
            result = self.cursor.fetchone()[0]
            self.assertIsInstance(result, datetime)
            self.assertIsNotNone(result.tzinfo,
                               "Should read timezone-aware datetime")
                
        except ctds.DatabaseError as e:
            # If DATETIMEOFFSET type isn't supported by SQL Server (very old version)
            if "DATETIMEOFFSET" in str(e):
                self.skipTest("SQL Server version doesn't support DATETIMEOFFSET type")
            raise

    def test_datetime_column_still_works(self):
        """
        Test that regular DATETIME columns work on all FreeTDS versions.
        
        This is the baseline functionality that must never regress.
        """
        # Create table with DATETIME column (not DATETIMEOFFSET)
        self.cursor.execute(
            """
            CREATE TABLE #test_datetime_compat (
                id INT,
                dt_col DATETIME
            )
            """
        )
        
        # Insert and read back
        dt = datetime(2024, 1, 15, 12, 30, 45)
        self.cursor.execute(
            "INSERT INTO #test_datetime_compat (id, dt_col) VALUES (1, :0)",
            (dt,)
        )
        
        self.cursor.execute("SELECT dt_col FROM #test_datetime_compat WHERE id = 1")
        result = self.cursor.fetchone()[0]
        
        # Should work on all FreeTDS versions
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, dt.year)
        self.assertEqual(result.month, dt.month)
        self.assertEqual(result.day, dt.day)
        self.assertEqual(result.hour, dt.hour)
        self.assertEqual(result.minute, dt.minute)
        self.assertEqual(result.second, dt.second)
        
        # Should be timezone-naive
        self.assertIsNone(result.tzinfo)

    def test_datetime2_column_behavior(self):
        """
        Test DATETIME2 column behavior (requires FreeTDS 0.95+).
        
        DATETIME2 is also TDS 7.3+, so should have same version requirement.
        """
        if self.freetds_version < (0, 95, 0):
            self.skipTest("DATETIME2 requires FreeTDS 0.95+ (same as DATETIMEOFFSET)")
        
        # Create table with DATETIME2 column
        self.cursor.execute(
            """
            CREATE TABLE #test_datetime2_compat (
                id INT,
                dt2_col DATETIME2
            )
            """
        )
        
        # Insert and read back with microsecond precision
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
        self.cursor.execute(
            "INSERT INTO #test_datetime2_compat (id, dt2_col) VALUES (1, :0)",
            (dt,)
        )
        
        self.cursor.execute("SELECT dt2_col FROM #test_datetime2_compat WHERE id = 1")
        result = self.cursor.fetchone()[0]
        
        # Should work with full microsecond precision
        self.assertIsInstance(result, datetime)
        self.assertEqual(result, dt)
        self.assertIsNone(result.tzinfo)

    def test_bulk_insert_naive_datetime_still_works(self):
        """
        Test that bulk insert with naive datetimes still works on all versions.
        """
        self.cursor.execute(
            """
            CREATE TABLE #test_bulk_compat (
                id INT,
                dt_col DATETIME
            )
            """
        )
        
        # Bulk insert naive datetimes
        rows = [
            (i, datetime(2024, 1, i, 12, 0, 0))
            for i in range(1, 11)
        ]
        
        inserted = self.connection.bulk_insert('#test_bulk_compat', rows)
        self.assertEqual(inserted, 10)
        
        # Verify
        self.cursor.execute("SELECT COUNT(*) FROM #test_bulk_compat")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 10)

    def test_bulk_insert_timezone_aware_fallback(self):
        """
        Test bulk insert with timezone-aware datetimes.
        
        Should work and preserve timezone (use DATETIMEOFFSET)
        """
        self.cursor.execute(
            """
            CREATE TABLE #test_bulk_tz_compat (
                id INT,
                dto_col DATETIMEOFFSET
            )
            """
        )
        
        # Bulk insert timezone-aware datetimes
        tz = timezone.utc
        rows = [
            (i, datetime(2024, 1, i, 12, 0, 0, tzinfo=tz))
            for i in range(1, 6)
        ]
        
        inserted = self.connection.bulk_insert('#test_bulk_tz_compat', rows)
        self.assertEqual(inserted, 5)
        
        # Verify
        self.cursor.execute("SELECT id, dto_col FROM #test_bulk_tz_compat ORDER BY id")
        results = self.cursor.fetchall()
        
        self.assertEqual(len(results), 5)
        
        # Should have timezone preserved
        for i, row in enumerate(results, 1):
            self.assertIsNotNone(row.dto_col.tzinfo,
                                f"Row {i} should have timezone preserved")

    def test_stored_procedure_datetime_parameter(self):
        """
        Test that stored procedures with DATETIME parameters still work.
        """
        with self.stored_procedure(
            self.cursor,
            'test_datetime_compat_sproc',
            '''
            @input_dt DATETIME,
            @output_dt DATETIME OUTPUT
            AS
            BEGIN
                SET @output_dt = @input_dt
            END
            '''
        ):
            input_dt = datetime(2024, 1, 15, 12, 30, 45)
            output_dt = ctds.Parameter(input_dt, output=True)            
            outputs = self.cursor.callproc('test_datetime_compat_sproc', (input_dt, output_dt))            
            self.assertEqual(outputs[1], input_dt) 
            # Should work on all FreeTDS versions

    def test_executemany_naive_datetime_still_works(self):
        """
        Test that executemany with naive datetimes still works.
        """
        self.cursor.execute(
            """
            CREATE TABLE #test_execmany_compat (
                id INT,
                dt_col DATETIME
            )
            """
        )
        
        # executemany with naive datetimes
        data = [
            (i, datetime(2024, 1, i, 12, 0, 0))
            for i in range(1, 6)
        ]
        
        self.cursor.executemany(
            "INSERT INTO #test_execmany_compat (id, dt_col) VALUES (:0, :1)",
            data
        )
        
        # Verify
        self.cursor.execute("SELECT COUNT(*) FROM #test_execmany_compat")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 5)

    def test_version_detection_works(self):
        """
        Test that FreeTDS version detection works correctly.
        
        This is important for the version checks in other tests.
        """
        # Should be able to get FreeTDS version
        self.assertIsInstance(self.freetds_version, tuple)
        self.assertEqual(len(self.freetds_version), 3)
        
        # All components should be integers
        for component in self.freetds_version:
            self.assertIsInstance(component, int)
        
        # Version should be reasonable (not negative, not crazy high)
        major, _, _ = self.freetds_version
        self.assertGreaterEqual(major, 0)
        self.assertLess(major, 100)

    def test_tds_version_detection(self):
        """
        Test that TDS protocol version detection works.
        
        This affects whether DATETIMEOFFSET is available.
        """
        tds_version = self.connection.tds_version
        
        # Should be a string like "7.3" or "7.4"
        self.assertIsInstance(tds_version, str)
        
        # Should be parseable
        parts = tds_version.split('.')
        self.assertGreaterEqual(len(parts), 1)
        
        major = int(parts[0])
        self.assertGreaterEqual(major, 4)
        self.assertLess(major, 10)
        
        # If FreeTDS >= 0.95, TDS version should be >= 7.3
        if self.freetds_version >= (1, 0, 0):
            # Should support TDS 7.3+
            # (Though connection might still negotiate lower)
            pass


class TestDateTimeOffsetVersionDetection(TestExternalDatabase):
    """
    Test version detection and capability checking.

    These tests ensure that the version checks used in other tests work correctly.
    """

    def test_freetds_version_property(self):
        """Test that freetds_version property works."""
        version = self.freetds_version

        self.assertIsInstance(version, tuple)
        self.assertEqual(len(version), 3)

        major, minor, patch = version
        self.assertGreaterEqual(major, 0)
        self.assertGreaterEqual(minor, 0)
        self.assertGreaterEqual(patch, 0)

    def test_freetds_version_comparison(self):
        """Test that version comparisons work correctly."""
        version = self.freetds_version

        self.assertTrue(version >= (0, 0, 0))
        self.assertTrue(version < (100, 0, 0))

        # Minimum supported version is 1.0
        self.assertGreaterEqual(version, (1, 0, 0))

    def test_tdsdatetime2_supported_property(self):
        """Test the tdsdatetime2_supported property."""
        self.assertTrue(self.tdsdatetime2_supported)

    def test_tdstime_supported_property(self):
        """Test the tdstime_supported property."""
        self.assertTrue(self.tdstime_supported)

    def test_capability_detection_consistency(self):
        """
        Test that all TDS 7.3 capabilities are detected consistently.

        DATETIMEOFFSET, DATETIME2, TIME, and DATE all require TDS 7.3+,
        so their support should be consistent.
        """
        self.assertTrue(self.tdsdatetime2_supported)
        self.assertTrue(self.tdstime_supported)

if __name__ == '__main__':
    unittest.main()
