"""
Unit tests for ctds._bulk_insert internals.

Tests cover the pure-Python logic (table name parsing, codec resolution,
row encoding) and do not require a database connection.
"""
import unittest

from ctds._bulk_insert import (
    _parse_table_name,
    _encode_rows,
    _get_column_codecs,
    _CODEPAGE_TO_CODEC,
)
from _tds import SqlVarChar # pylint: disable=no-name-in-module


class TestParseTableName(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(_parse_table_name('MyTable'), (None, None, 'MyTable'))

    def test_two_part(self):
        self.assertEqual(_parse_table_name('dbo.MyTable'), (None, 'dbo', 'MyTable'))

    def test_three_part(self):
        self.assertEqual(_parse_table_name('mydb.dbo.MyTable'), ('mydb', 'dbo', 'MyTable'))

    def test_bracketed(self):
        self.assertEqual(
            _parse_table_name('[my db].[dbo].[My Table]'),
            ('my db', 'dbo', 'My Table')
        )

    def test_dots_inside_brackets(self):
        self.assertEqual(
            _parse_table_name('[my.db].[my.schema].[my.table]'),
            ('my.db', 'my.schema', 'my.table')
        )

    def test_quoted(self):
        self.assertEqual(
            _parse_table_name('"my db"."dbo"."My Table"'),
            ('my db', 'dbo', 'My Table')
        )

    def test_escaped_quotes(self):
        self.assertEqual(
            _parse_table_name('"my""db".dbo.table'),
            ('my"db', 'dbo', 'table')
        )

    def test_mixed_brackets_and_plain(self):
        self.assertEqual(
            _parse_table_name('[mydb].dbo.[My Table]'),
            ('mydb', 'dbo', 'My Table')
        )

    def test_too_many_parts(self):
        with self.assertRaises(ValueError):
            _parse_table_name('a.b.c.d')

    def test_unterminated_quote(self):
        """Unterminated quoted identifier parses what it can."""
        self.assertEqual(
            _parse_table_name('"unterminated'),
            (None, None, 'unterminated')
        )

    def test_unterminated_quote_after_escaped(self):
        """String ends after an escaped quote pair with no closing quote."""
        self.assertEqual(
            _parse_table_name('"ab""'),
            (None, None, 'ab"')
        )

    def test_unterminated_double_quote(self):
        self.assertEqual(
            _parse_table_name('dbo."MyTable'),
            (None, 'dbo', 'MyTable')
        )

    def test_unterminated_bracket(self):
        """Bracketed identifier with no closing bracket."""
        self.assertEqual(
            _parse_table_name('[unterminated'),
            (None, None, 'unterminated')
        )

class TestEncodeRows(unittest.TestCase):

    def test_sequence_row_encodes_by_position(self):
        by_position = ['utf-16-le', None, 'cp1252']
        by_name = {}
        rows = [('hello', 42, 'world')]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertEqual(len(result), 1)

        row = result[0]
        self.assertIsInstance(row[0], SqlVarChar)
        self.assertEqual(row[0].value, 'hello'.encode('utf-16-le'))
        self.assertEqual(row[1], 42)
        self.assertIsInstance(row[2], SqlVarChar)
        self.assertEqual(row[2].value, 'world'.encode('cp1252'))

    def test_sequence_row_none_values_unchanged(self):
        by_position = ['utf-16-le']
        by_name = {}
        rows = [(None,)]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertIsNone(result[0][0])

    def test_sequence_row_extra_columns_pass_through(self):
        """Columns beyond metadata length are not encoded."""
        by_position = ['utf-16-le']
        by_name = {}
        rows = [('hello', 'extra')]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertIsInstance(result[0][0], SqlVarChar)
        self.assertEqual(result[0][0].value, 'hello'.encode('utf-16-le'))
        self.assertEqual(result[0][1], 'extra')  # no metadata -> unchanged

    def test_sequence_row_no_codec_passes_through(self):
        """Non-text columns (codec=None) leave str values unchanged."""
        by_position = [None]
        by_name = {}
        rows = [('123',)]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertEqual(result[0][0], '123')
        self.assertIsInstance(result[0][0], str)

    def test_dict_row_encodes_by_name(self):
        by_position = []
        by_name = {'Name': 'utf-16-le', 'Code': 'cp1252', 'Id': None}
        rows = [{'Name': 'hello', 'Code': 'world', 'Id': 42}]

        result = list(_encode_rows(rows, by_position, by_name))
        row = result[0]
        self.assertIsInstance(row['Name'], SqlVarChar)
        self.assertEqual(row['Name'].value, 'hello'.encode('utf-16-le'))
        self.assertIsInstance(row['Code'], SqlVarChar)
        self.assertEqual(row['Code'].value, 'world'.encode('cp1252'))
        self.assertEqual(row['Id'], 42)


    def test_multiple_rows(self):
        by_position = ['cp1252']
        by_name = {}
        rows = [('a',), ('b',), ('c',)]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertEqual(len(result), 3)
        for i, letter in enumerate(['a', 'b', 'c']):
            self.assertIsInstance(result[i][0], SqlVarChar)
            self.assertEqual(result[i][0].value, letter.encode('cp1252'))

    def test_non_ascii_varchar_encoding(self):
        """Verify non-ASCII chars encode to the correct code page bytes."""
        by_position = ['cp1252']
        by_name = {}
        # U+00BD = ½, which is 0xBD in cp1252 but 0xC2 0xBD in UTF-8
        rows = [('\u00bd',)]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertEqual(result[0][0].value, b'\xbd')

    def test_non_ascii_nvarchar_encoding(self):
        """Verify non-ASCII chars encode to UTF-16LE for nvarchar columns."""
        by_position = ['utf-16-le']
        by_name = {}
        # Japanese katakana ホ (U+30DB)
        rows = [('\u30db',)]

        result = list(_encode_rows(rows, by_position, by_name))
        self.assertEqual(result[0][0].value, '\u30db'.encode('utf-16-le'))
        self.assertEqual(result[0][0].value, b'\xdb\x30')

    def test_generator_is_lazy(self):
        """_encode_rows should yield one row at a time, not buffer."""
        by_position = [None]
        by_name = {}
        call_count = [0]

        def counting_rows():
            for i in range(3):
                call_count[0] += 1
                yield (i,)

        gen = _encode_rows(counting_rows(), by_position, by_name)
        self.assertEqual(call_count[0], 0)
        next(gen)
        self.assertEqual(call_count[0], 1)


class TestGetColumnCodecsNoResults(unittest.TestCase):

    def test_raises_on_empty_results(self):
        """_get_column_codecs should raise ValueError when no columns found."""
        class FakeCursor:
            def execute(self, query, params):
                pass
            def fetchall(self):
                return []
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

        with self.assertRaises(ValueError) as ctx:
            _get_column_codecs(FakeConnection(), 'NonExistentTable')

        self.assertIn('NonExistentTable', str(ctx.exception))
        self.assertIn('INFORMATION_SCHEMA', str(ctx.exception))


class TestCodePageMapping(unittest.TestCase):

    def test_common_code_pages_present(self):
        expected = {
            1252: 'cp1252', 1250: 'cp1250', 1251: 'cp1251',
            932: 'shift_jis', 936: 'gbk', 949: 'euc-kr',
            950: 'big5', 65001: 'utf-8',
        }
        for cp, codec in expected.items():
            self.assertIn(cp, _CODEPAGE_TO_CODEC)
            self.assertEqual(_CODEPAGE_TO_CODEC[cp], codec)


if __name__ == '__main__':
    unittest.main()
