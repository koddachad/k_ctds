"""
Unit tests for DATETIMEOFFSET with BULK INSERT operations.

This module tests the bulk insertion of timezone-aware datetime values
using the Connection.bulk_insert() method.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import unittest
import warnings

from .base import TestExternalDatabase


class TestDateTimeOffsetBulkInsert(TestExternalDatabase):
    """Test DATETIMEOFFSET with bulk insert operations."""

    def test_bulk_insert_datetimeoffset_basic(self):
        """Test basic bulk insert with DATETIMEOFFSET column."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_basic.__name__)
                    )

                # Prepare test data
                rows = [
                    (1, datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)),
                    (2, datetime(2024, 1, 2, 11, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=5, minutes=30)))),
                    (3, datetime(2024, 1, 3, 12, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=-8)))),
                    (4, datetime(2024, 1, 4, 13, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=1)))),
                    (5, datetime(2024, 1, 5, 14, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=-5)))),
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_basic.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT id, event_time FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_basic.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, (expected_id, expected_dt) in enumerate(rows):
                    self.assertEqual(results[i].id, expected_id)
                    self.assertEqual(results[i].event_time, expected_dt)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_large_dataset(self):
        """Test bulk insert with large number of DATETIMEOFFSET rows."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_large_dataset.__name__)
                    )

                # Generate large dataset with various timezones
                num_rows = 1000
                timezones = [
                    timezone.utc,
                    timezone(timedelta(hours=5, minutes=30)),
                    timezone(timedelta(hours=-8)),
                    timezone(timedelta(hours=1)),
                    timezone(timedelta(hours=-5)),
                    timezone(timedelta(hours=9)),
                    timezone(timedelta(hours=-3, minutes=-30)),
                ]

                rows = [
                    (
                        i,
                        datetime(
                            2024, 
                            1 + (i % 12), 
                            1 + (i % 28),
                            (i % 24),
                            (i % 60),
                            (i % 60),
                            (i % 1000) * 1000,
                            tzinfo=timezones[i % len(timezones)]
                        )
                    )
                    for i in range(num_rows)
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_large_dataset.__name__,
                        rows
                    )

                self.assertEqual(inserted, num_rows)

                # Verify row count
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) FROM {0}'.format(
                            self.test_bulk_insert_datetimeoffset_large_dataset.__name__
                        )
                    )
                    count = cursor.fetchone()[0]
                    self.assertEqual(count, num_rows)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_with_null(self):
        """Test bulk insert with DATETIMEOFFSET NULL values."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_with_null.__name__)
                    )

                # Prepare test data with NULL values
                rows = [
                    (1, datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc)),
                    (2, None),
                    (3, datetime(2024, 1, 3, 12, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=5, minutes=30)))),
                    (4, None),
                    (5, datetime(2024, 1, 5, 14, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=-8)))),
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_with_null.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT id, event_time FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_with_null.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, (expected_id, expected_dt) in enumerate(rows):
                    self.assertEqual(results[i].id, expected_id)
                    if expected_dt is None:
                        self.assertIsNone(results[i].event_time)
                    else:
                        self.assertEqual(results[i].event_time, expected_dt)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_mixed_types(self):
        """Test bulk insert with DATETIMEOFFSET and other data types."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            event_time DATETIMEOFFSET NOT NULL,
                            amount DECIMAL(10,2) NULL,
                            is_active BIT NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_mixed_types.__name__)
                    )

                # Prepare test data with mixed types
                rows = [
                    (
                        1, 
                        'Event One',
                        datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
                        Decimal('100.50'),
                        True
                    ),
                    (
                        2,
                        'Event Two',
                        datetime(2024, 1, 2, 11, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=5, minutes=30))),
                        Decimal('200.75'),
                        False
                    ),
                    (
                        3,
                        'Event Three',
                        datetime(2024, 1, 3, 12, 0, 0, 0, 
                                tzinfo=timezone(timedelta(hours=-8))),
                        None,
                        True
                    ),
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_mixed_types.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_mixed_types.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, expected_row in enumerate(rows):
                    result = results[i]
                    self.assertEqual(result.id, expected_row[0])
                    self.assertEqual(result.name, expected_row[1])
                    self.assertEqual(result.event_time, expected_row[2])
                    self.assertEqual(result.amount, expected_row[3])
                    self.assertEqual(result.is_active, expected_row[4])

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_dict_format(self):
        """Test bulk insert with DATETIMEOFFSET using dict format."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL,
                            description VARCHAR(100) NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_dict_format.__name__)
                    )

                # Prepare test data as dictionaries
                rows = [
                    {
                        'id': 1,
                        'event_time': datetime(2024, 1, 1, 10, 0, 0, 0, tzinfo=timezone.utc),
                        'description': 'First event'
                    },
                    {
                        'id': 2,
                        'event_time': datetime(2024, 1, 2, 11, 0, 0, 0, 
                                              tzinfo=timezone(timedelta(hours=5, minutes=30))),
                        'description': 'Second event'
                    },
                    {
                        'id': 3,
                        'event_time': datetime(2024, 1, 3, 12, 0, 0, 0, 
                                              tzinfo=timezone(timedelta(hours=-8))),
                        'description': None
                    },
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_dict_format.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_dict_format.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, expected_row in enumerate(rows):
                    result = results[i]
                    self.assertEqual(result.id, expected_row['id'])
                    self.assertEqual(result.event_time, expected_row['event_time'])
                    self.assertEqual(result.description, expected_row['description'])

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_batch_size(self):
        """Test bulk insert with DATETIMEOFFSET using batch_size parameter."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_batch_size.__name__)
                    )

                # Prepare test data
                num_rows = 100
                batch_size = 20
                rows = [
                    (
                        i,
                        datetime(
                            2024, 
                            1, 
                            1 + (i % 28),
                            (i % 24),
                            (i % 60),
                            (i % 60),
                            0,
                            tzinfo=timezone(timedelta(hours=(i % 24) - 12))
                        )
                    )
                    for i in range(num_rows)
                ]

                # Bulk insert with batch_size
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_batch_size.__name__,
                        rows,
                        batch_size=batch_size
                    )

                self.assertEqual(inserted, num_rows)

                # Verify row count
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) FROM {0}'.format(
                            self.test_bulk_insert_datetimeoffset_batch_size.__name__
                        )
                    )
                    count = cursor.fetchone()[0]
                    self.assertEqual(count, num_rows)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_various_offsets(self):
        """Test bulk insert with DATETIMEOFFSET values having various timezone offsets."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL,
                            offset_description VARCHAR(50) NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_various_offsets.__name__)
                    )

                # Prepare test data with various offsets
                base_dt = datetime(2024, 1, 15, 12, 0, 0, 0)
                rows = [
                    (1, base_dt.replace(tzinfo=timezone.utc), 'UTC'),
                    (2, base_dt.replace(tzinfo=timezone(timedelta(hours=1))), '+01:00'),
                    (3, base_dt.replace(tzinfo=timezone(timedelta(hours=-8))), '-08:00 PST'),
                    (4, base_dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30))), '+05:30 IST'),
                    (5, base_dt.replace(tzinfo=timezone(timedelta(hours=9, minutes=30))), '+09:30'),
                    (6, base_dt.replace(tzinfo=timezone(timedelta(hours=-3, minutes=-30))), '-03:30'),
                    (7, base_dt.replace(tzinfo=timezone(timedelta(hours=12))), '+12:00'),
                    (8, base_dt.replace(tzinfo=timezone(timedelta(hours=-11))), '-11:00'),
                    (9, base_dt.replace(tzinfo=timezone(timedelta(hours=14))), '+14:00 Max'),
                    (10, base_dt.replace(tzinfo=timezone(timedelta(hours=-12))), '-12:00'),
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_various_offsets.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_various_offsets.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, (expected_id, expected_dt, expected_desc) in enumerate(rows):
                    result = results[i]
                    self.assertEqual(result.id, expected_id)
                    self.assertEqual(result.event_time, expected_dt)
                    self.assertEqual(result.offset_description, expected_desc)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_microsecond_precision(self):
        """Test bulk insert with DATETIMEOFFSET values with various microsecond precision."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_microsecond_precision.__name__)
                    )

                # Prepare test data with various microsecond values
                tz = timezone.utc
                rows = [
                    (1, datetime(2024, 1, 1, 12, 0, 0, 0, tzinfo=tz)),
                    (2, datetime(2024, 1, 1, 12, 0, 0, 1, tzinfo=tz)),
                    (3, datetime(2024, 1, 1, 12, 0, 0, 100000, tzinfo=tz)),
                    (4, datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=tz)),
                    (5, datetime(2024, 1, 1, 12, 0, 0, 999999, tzinfo=tz)),
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_microsecond_precision.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_microsecond_precision.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, (expected_id, expected_dt) in enumerate(rows):
                    result = results[i]
                    self.assertEqual(result.id, expected_id)
                    self.assertEqual(result.event_time.microsecond, expected_dt.microsecond)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_boundary_dates(self):
        """Test bulk insert with DATETIMEOFFSET boundary date values."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_boundary_dates.__name__)
                    )

                # Prepare test data with boundary dates
                tz = timezone.utc
                rows = [
                    (1, datetime(1, 1, 1, 0, 0, 0, 0, tzinfo=tz)),  # Minimum
                    (2, datetime(2024, 2, 29, 12, 0, 0, 0, tzinfo=tz)),  # Leap year
                    (3, datetime(2024, 12, 31, 23, 59, 59, 999999, tzinfo=tz)),
                    (4, datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=tz)),  # Maximum
                ]

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_boundary_dates.__name__,
                        rows
                    )

                self.assertEqual(inserted, len(rows))

                # Verify the data
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY id'.format(
                            self.test_bulk_insert_datetimeoffset_boundary_dates.__name__
                        )
                    )
                    results = cursor.fetchall()

                self.assertEqual(len(results), len(rows))
                for i, (expected_id, expected_dt) in enumerate(rows):
                    result = results[i]
                    self.assertEqual(result.id, expected_id)
                    self.assertEqual(result.event_time.year, expected_dt.year)
                    self.assertEqual(result.event_time.month, expected_dt.month)
                    self.assertEqual(result.event_time.day, expected_dt.day)

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_tablock(self):
        """Test bulk insert with DATETIMEOFFSET using tablock parameter."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_tablock.__name__)
                    )

                # Prepare test data
                rows = [
                    (i, datetime(2024, 1, 1 + i, 12, 0, 0, 0, tzinfo=timezone.utc))
                    for i in range(10)
                ]

                # Bulk insert with tablock
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_tablock.__name__,
                        rows,
                        tablock=True
                    )

                self.assertEqual(inserted, len(rows))

                # Verify row count
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) FROM {0}'.format(
                            self.test_bulk_insert_datetimeoffset_tablock.__name__
                        )
                    )
                    count = cursor.fetchone()[0]
                    self.assertEqual(count, len(rows))

            finally:
                connection.rollback()

    def test_bulk_insert_datetimeoffset_generator(self):
        """Test bulk insert with DATETIMEOFFSET using generator expression."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            id INT NOT NULL PRIMARY KEY,
                            event_time DATETIMEOFFSET NOT NULL
                        )
                        '''.format(self.test_bulk_insert_datetimeoffset_generator.__name__)
                    )

                # Use generator expression for rows
                num_rows = 50
                rows = (
                    (
                        i,
                        datetime(
                            2024, 
                            1, 
                            1 + (i % 28),
                            12, 
                            0, 
                            0, 
                            0,
                            tzinfo=timezone(timedelta(hours=(i % 13) - 6))
                        )
                    )
                    for i in range(num_rows)
                )

                # Bulk insert
                with warnings.catch_warnings(record=True):
                    inserted = connection.bulk_insert(
                        self.test_bulk_insert_datetimeoffset_generator.__name__,
                        rows
                    )

                self.assertEqual(inserted, num_rows)

                # Verify row count
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) FROM {0}'.format(
                            self.test_bulk_insert_datetimeoffset_generator.__name__
                        )
                    )
                    count = cursor.fetchone()[0]
                    self.assertEqual(count, num_rows)

            finally:
                connection.rollback()


if __name__ == '__main__':
    unittest.main()
