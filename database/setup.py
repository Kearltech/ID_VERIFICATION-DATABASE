"""
Database setup and initialization script
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import initialize_database
from database.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database(
    host: str = "127.0.0.1",
    port: int = 3306,
    user: str = "root",
    password: str = "",
    database: str = "IDverification",
    drop_existing: bool = False
):
    """
    Setup database tables
    
    Args:
        host: MySQL host
        port: MySQL port
        user: Database user
        password: Database password
        database: Database name
        drop_existing: Whether to drop existing tables first
    """
    logger.info(f"Connecting to database: {host}:{port}/{database}")
    
    try:
        # Initialize database connection
        db = initialize_database(host, port, user, password, database)
        
        # Test connection
        if not db.test_connection():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Database connection successful")
        
        # Drop existing tables if requested
        if drop_existing:
            logger.warning("Dropping existing tables...")
            db.drop_tables()
            logger.info("Existing tables dropped")
        
        # Create tables
        logger.info("Creating database tables...")
        db.create_tables()
        logger.info("Database tables created successfully")
        
        # Print table summary
        logger.info("\n" + "="*50)
        logger.info("Database Setup Complete!")
        logger.info("="*50)
        logger.info(f"Database: {database}")
        logger.info("Tables created:")
        logger.info("  - users")
        logger.info("  - submissions")
        logger.info("  - validation_logs")
        logger.info("  - api_usage")
        logger.info("  - audit_logs")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


def create_sample_data():
    """Create sample data for testing"""
    from database.connection import get_database
    from database.repository import UserRepository, SubmissionRepository
    
    logger.info("Creating sample data...")
    
    try:
        db = get_database()
        
        with db.session_scope() as session:
            # Create sample user
            user_repo = UserRepository(session)
            user = user_repo.create(
                username="testuser",
                email="test@example.com",
                full_name="Test User",
                role="user"
            )
            logger.info(f"Created user: {user.username}")
            
            # Create sample submission
            submission_repo = SubmissionRepository(session)
            submission = submission_repo.create({
                'user_id': user.user_id,
                'id_type': 'Ghana Card',
                'validation_overall': True,
                'face_match': True,
                'face_match_distance': 0.35,
                'gemini_card_type': 'Ghana Card',
                'gemini_confidence': 0.95
            })
            logger.info(f"Created submission: {submission.submission_id}")
        
        logger.info("Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup ID Verification Database')
    parser.add_argument('--host', default='127.0.0.1', help='MySQL host')
    parser.add_argument('--port', type=int, default=3306, help='MySQL port')
    parser.add_argument('--user', default='root', help='Database user')
    parser.add_argument('--password', default='', help='Database password')
    parser.add_argument('--database', default='IDverification', help='Database name')
    parser.add_argument('--drop', action='store_true', help='Drop existing tables')
    parser.add_argument('--sample-data', action='store_true', help='Create sample data')
    
    args = parser.parse_args()
    
    # Setup database
    success = setup_database(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        drop_existing=args.drop
    )
    
    if success and args.sample_data:
        create_sample_data()
    
    sys.exit(0 if success else 1)
