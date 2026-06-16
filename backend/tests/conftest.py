import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
import sqlalchemy

@pytest.fixture(scope="session")
def db_engine():
    # Connect to default postgres DB first to create the test DB
    sys_engine = create_engine("postgresql://postgres:password@127.0.0.1:5435/postgres", isolation_level="AUTOCOMMIT")
    with sys_engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text("CREATE DATABASE sarvam_talent_test"))
        except Exception:
            # Database might already exist or permission error, ignore
            pass
    sys_engine.dispose()

    # Now connect to the test database
    engine = create_engine(
        "postgresql://postgres:password@127.0.0.1:5435/sarvam_talent_test",
        pool_pre_ping=True
    )
    
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
