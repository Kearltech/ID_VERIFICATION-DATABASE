"""
Database connection management for MySQL
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MySQL database connections using SQLAlchemy"""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "IDverification",
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ):
        """
        Initialize database connection
        
        Args:
            host: MySQL server host
            port: MySQL server port
            user: Database user
            password: Database password
            database: Database name
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Connection recycle time in seconds
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
        # Build connection URL
        self.connection_url = (
            f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
            f"?charset=utf8mb4"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.connection_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Enable connection health checks
            echo=False,  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Add connection pool event listeners
        self._setup_event_listeners()
        
        logger.info(f"Database connection configured: {host}:{port}/{database}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for connection management"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Called when a new DB-API connection is created"""
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool"""
            logger.debug("Connection checked out from pool")
    
    def create_tables(self):
        """Create all tables in the database"""
        from .models import Base
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        from .models import Base
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations
        
        Usage:
            with db_connection.session_scope() as session:
                session.add(user)
                # Automatically commits on success, rolls back on error
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close all connections and dispose of the engine"""
        self.engine.dispose()
        logger.info("Database connections closed")


# Global database connection instance
_db_connection = None


def initialize_database(
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    database: str = None
) -> DatabaseConnection:
    """
    Initialize the global database connection
    
    Args:
        host: MySQL host (defaults to env var DB_HOST or 127.0.0.1)
        port: MySQL port (defaults to env var DB_PORT or 3306)
        user: Database user (defaults to env var DB_USER or root)
        password: Database password (defaults to env var DB_PASSWORD)
        database: Database name (defaults to env var DB_NAME or IDverification)
    """
    global _db_connection
    
    # Get configuration from environment or parameters
    config = {
        'host': host or os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(port or os.getenv('DB_PORT', 3306)),
        'user': user or os.getenv('DB_USER', 'root'),
        'password': password or os.getenv('DB_PASSWORD', ''),
        'database': database or os.getenv('DB_NAME', 'IDverification')
    }
    
    _db_connection = DatabaseConnection(**config)
    return _db_connection


def get_database() -> DatabaseConnection:
    """Get the global database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = initialize_database()
    return _db_connection


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager
    
    Usage:
        with get_db_session() as session:
            users = session.query(User).all()
    """
    db = get_database()
    with db.session_scope() as session:
        yield session
