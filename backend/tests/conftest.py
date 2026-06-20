import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from config import settings


def _get_test_db_url() -> str:
    """
    Derive the test database URL from settings.
    Uses TEST_DATABASE_URL if set, otherwise appends '_test' to the main DB URL.
    Handles query parameters properly (e.g. Neon connection strings).
    """
    if settings.TEST_DATABASE_URL:
        # Check if the configured default in Settings is local, but the main DB is Neon.
        # If the user is using Neon (DATABASE_URL is neon), we want to auto-derive from Neon
        # instead of failing connection to local postgres that doesn't have the default password.
        if "neon.tech" in settings.DATABASE_URL and "127.0.0.1" in settings.TEST_DATABASE_URL:
            pass  # let it auto-derive from Neon DATABASE_URL
        else:
            return settings.TEST_DATABASE_URL

    url = settings.DATABASE_URL
    if "?" in url:
        base_url, query_params = url.split("?", 1)
        if "/" in base_url:
            prefix, db_name = base_url.rsplit("/", 1)
            return f"{prefix}/{db_name}_test?{query_params}"
    else:
        if "/" in url:
            prefix, db_name = url.rsplit("/", 1)
            return f"{prefix}/{db_name}_test"
    return url


@pytest.fixture(scope="session")
def db_engine():
    test_url = _get_test_db_url()

    # Connect to default postgres DB first to create the test DB, preserving query params (like SSL)
    if "?" in test_url:
        db_part, query_part = test_url.split("?", 1)
        base_db_part = db_part.rsplit("/", 1)[0] + "/postgres"
        base_url = f"{base_db_part}?{query_part}"
        db_name = db_part.rsplit("/", 1)[-1]
    else:
        base_url = test_url.rsplit("/", 1)[0] + "/postgres"
        db_name = test_url.rsplit("/", 1)[-1]

    sys_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with sys_engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text(f"CREATE DATABASE {db_name}"))
        except Exception:
            # Database might already exist — that's fine
            pass
    sys_engine.dispose()

    # Now connect to the test database
    engine = create_engine(test_url, pool_pre_ping=True)

    # Drop and recreate tables to ensure a clean schema
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"
