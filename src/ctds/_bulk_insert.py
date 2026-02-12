"""
Auto-encoding support for bulk_insert.

Queries INFORMATION_SCHEMA.COLUMNS to determine each column's type and
collation, then encodes Python str values to the correct byte
representation before passing rows to the C bulk_insert.
"""

from _tds import SqlVarChar


# SQL Server collation code page -> Python codec name.
_CODEPAGE_TO_CODEC = {
    437: 'cp437',
    850: 'cp850',
    874: 'cp874',
    932: 'shift_jis',
    936: 'gbk',
    949: 'euc-kr',
    950: 'big5',
    1250: 'cp1250',
    1251: 'cp1251',
    1252: 'cp1252',
    1253: 'cp1253',
    1254: 'cp1254',
    1255: 'cp1255',
    1256: 'cp1256',
    1257: 'cp1257',
    1258: 'cp1258',
    65001: 'utf-8',
}


def _parse_table_name(table):
    """
    Parse a possibly multi-part SQL Server table name into
    (catalog, schema, table) components.

    Splits on '.' while respecting [bracketed] and "quoted" identifiers.
    Parts are assigned right-to-left: table, schema, catalog.

    Returns:
        tuple: (catalog, schema, table) where catalog and schema may be None.

    Raises:
        ValueError: If the table name has more than 3 parts.
    """
    parts = []
    current = []
    i = 0

    while i < len(table):
        ch = table[i]

        if ch == '[':
            i += 1
            while i < len(table) and table[i] != ']':
                current.append(table[i])
                i += 1
            if i < len(table):
                i += 1  # skip closing ]

        elif ch == '"':
            i += 1
            while i < len(table):
                if table[i] == '"':
                    if i + 1 < len(table) and table[i + 1] == '"':
                        current.append('"')
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    current.append(table[i])
                    i += 1

        elif ch == '.':
            parts.append(''.join(current))
            current = []
            i += 1

        else:
            current.append(ch)
            i += 1

    parts.append(''.join(current))

    if len(parts) == 1:
        return (None, None, parts[0])
    elif len(parts) == 2:
        return (None, parts[0], parts[1])
    elif len(parts) == 3:
        return (parts[0], parts[1], parts[2])
    else:
        raise ValueError(
            'Invalid table name: {!r}. '
            'Expected [catalog.][schema.]table'.format(table)
        )


def _get_column_codecs(connection, table):
    """
    Query INFORMATION_SCHEMA.COLUMNS to build an ordered list of codecs
    for the target table.

    Returns two structures:
        by_position: list in ORDINAL_POSITION order where each entry is
            either a Python codec name (str) or None for non-text columns.
            NVARCHAR/NCHAR/NTEXT -> 'utf-16-le'
            VARCHAR/CHAR/TEXT    -> collation codec (e.g. 'cp1252')
            everything else     -> None
        by_name: dict of column_name -> codec_or_None (same values)
    """
    catalog, schema, table_name = _parse_table_name(table)

    if catalog:
        info_schema = '[{}].INFORMATION_SCHEMA.COLUMNS'.format(
            catalog.replace(']', ']]')
        )
    else:
        info_schema = 'INFORMATION_SCHEMA.COLUMNS'

    params = [table_name]
    where_clauses = ['TABLE_NAME = :0']

    if schema is not None:
        params.append(schema)
        where_clauses.append('TABLE_SCHEMA = :1')

    if catalog is not None:
        params.append(catalog)
        where_clauses.append('TABLE_CATALOG = :{}'.format(len(params) - 1))

    query = (
        'SELECT COLUMN_NAME, DATA_TYPE, '
        "CAST(COLLATIONPROPERTY(COLLATION_NAME, 'CodePage') AS INT) AS CodePage " 
        'FROM {} WHERE {} '
        'ORDER BY ORDINAL_POSITION'.format(
            info_schema, ' AND '.join(where_clauses)
        )
    )

    by_position = []
    by_name = {}

    with connection.cursor() as cursor:
        cursor.execute(query, tuple(params))
        for row in cursor.fetchall():
            col_name = row[0]
            data_type = row[1].lower()
            code_page = row[2]

            # Resolve the codec once here — no need to classify types later.
            if data_type in ('nvarchar', 'nchar', 'ntext'):
                codec = 'utf-16-le'
            elif data_type in ('varchar', 'char', 'text') and code_page is not None:
                codec = _CODEPAGE_TO_CODEC.get(int(code_page))
            else:
                codec = None

            by_position.append(codec)
            by_name[col_name] = codec

    if not by_position:
        raise ValueError(
            'No columns found for table {!r} in INFORMATION_SCHEMA.COLUMNS. '
            'Verify the table exists and the current user has access. '
            'Note: temporary tables are not supported with auto_encode.'.format(table)
        )

    return by_position, by_name


def _encode_rows(rows, by_position, by_name):
    """
    Generator that encodes str values in each row before yielding.

    For sequence rows: uses by_position (ordinal index).
    For dict rows: uses by_name (column name lookup).

    Both NVARCHAR and VARCHAR columns are wrapped as SqlVarChar with
    pre-encoded bytes. This is necessary because FreeTDS BCP downgrades
    TDSNVARCHAR to TDSVARCHAR, so SqlNVarChar would corrupt Unicode data.
    SqlVarChar with the correctly encoded bytes works for both column types.
    """
    for row in rows:
        if isinstance(row, dict):
            yield {
                k: SqlVarChar(v.encode(by_name[k]))
                   if isinstance(v, str) and by_name.get(k)
                   else v
                for k, v in row.items()
            }
        else:
            yield tuple(
                SqlVarChar(v.encode(by_position[i]))
                   if isinstance(v, str) and i < len(by_position) and by_position[i]
                   else v
                for i, v in enumerate(row)
            )
