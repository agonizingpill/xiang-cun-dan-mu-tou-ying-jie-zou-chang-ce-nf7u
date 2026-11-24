import threading
from contextlib import contextmanager

from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.schema import CreateColumn

from core.config import DATABASE_URL

metadata = MetaData()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

_schema_lock = threading.Lock()
_schema_ready_for = None


def ensure_schema():
    """Create missing tables and add columns introduced after an initial snapshot.

    ``metadata.create_all`` deliberately does not ALTER existing tables.  The
    lightweight column check keeps review/demo databases on the named volume
    usable without introducing a separate migration tool.
    """
    global _schema_ready_for
    ready_token = (id(engine), str(engine.url))
    if _schema_ready_for == ready_token:
        return
    with _schema_lock:
        if _schema_ready_for == ready_token:
            return
        metadata.create_all(engine)
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        with engine.begin() as conn:
            for table in metadata.tables.values():
                if table.name not in existing_tables:
                    continue
                present = {column['name'] for column in inspector.get_columns(table.name)}
                for column in table.columns:
                    if column.name in present:
                        continue
                    column_ddl = str(CreateColumn(column).compile(dialect=engine.dialect))
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {column_ddl}'))
        _schema_ready_for = ready_token


@contextmanager
def transaction():
    ensure_schema()
    with engine.begin() as conn:
        yield conn
