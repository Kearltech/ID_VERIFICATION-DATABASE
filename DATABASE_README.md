# MySQL Database Integration for ID Verification System

## Overview
Complete MySQL database integration with SQLAlchemy ORM, data encryption, and comprehensive repository pattern.

## Setup Instructions

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Create MySQL Database
Open MySQL Workbench and create the database:
```sql
CREATE DATABASE IDverification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Setup Database Tables
Run the setup script:
```powershell
python database/setup.py --host 127.0.0.1 --port 3306 --user root --password YOUR_PASSWORD --database IDverification
```

Or with options:
```powershell
# Drop existing tables and recreate
python database/setup.py --drop

# Create sample data for testing
python database/setup.py --sample-data
```

### 4. Configure Environment Variables (Optional)
Create a `.env` file:
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=IDverification
ENCRYPTION_KEY=your_encryption_key
```

### 5. Run the Application
```powershell
streamlit run app_gemini.py
```

## Database Schema

### Tables Created

#### 1. **users**
- User accounts and authentication
- Fields: user_id, username, email, password_hash, full_name, role, is_active, created_at, last_login

#### 2. **submissions**
- ID verification submissions
- Fields: submission_id, user_id, id_type, encrypted personal data, validation results, Gemini API results, file paths
- Includes automatic deletion scheduling (90 days default)

#### 3. **validation_logs**
- Detailed field-by-field validation logs
- Fields: log_id, submission_id, field_name, validation_type, validation_result, expected_value, actual_value

#### 4. **api_usage**
- Gemini API usage and cost tracking
- Fields: usage_id, user_id, api_operation, model_name, tokens, estimated_cost, duration

#### 5. **audit_logs**
- System-wide audit trail
- Fields: log_id, event_type, event_category, event_description, user_id, severity, timestamp

## Features

### 🔐 Data Security
- **Encryption**: Sensitive data (ID numbers, names, DOB) encrypted at rest using Fernet (symmetric encryption)
- **Secure Storage**: Encrypted fields stored separately from metadata
- **Audit Logging**: All database operations logged with timestamps and user context

### 📊 Statistics & Analytics
- User submission statistics (success rate, totals, trends)
- API usage tracking (calls, tokens, costs)
- ID type breakdowns
- Recent submission history

### 🔄 Connection Management
- Connection pooling for performance
- Automatic reconnection with health checks
- Transaction management with automatic rollback
- Context managers for safe database operations

### 💾 Repository Pattern
Clean separation of concerns with dedicated repositories:
- `UserRepository`: User management
- `SubmissionRepository`: Submission CRUD operations
- `ValidationLogRepository`: Validation log management
- `APIUsageRepository`: API usage tracking
- `AuditLogRepository`: Audit trail management

## Usage in Application

### Connecting to Database
In the Streamlit app sidebar:
1. Expand "Database Settings"
2. Enter MySQL connection details
3. Click "Connect to Database"
4. Status will show "✅ Database Connected"

### Automatic Data Saving
When database is connected, each validation automatically:
- Saves submission with encrypted sensitive data
- Logs detailed field validations
- Tracks API usage and costs
- Creates audit trail entries
- Falls back to CSV if database save fails

### Viewing Statistics
1. Connect to database
2. Click "View Statistics" in sidebar
3. Dashboard shows:
   - Total submissions and success rate
   - Breakdown by ID type
   - API usage and costs
   - Recent submission history

## Code Examples

### Save a Verification Submission
```python
from database.db_utils import get_db_service

db_service = get_db_service()

submission_id = db_service.save_submission(
    user_id='user123',
    id_type='Ghana Card',
    form_data={
        'id_number': 'GHA-123456789-0',
        'surname': 'Doe',
        'firstname': 'John',
        'date_of_birth': '1990-01-01',
        'sex': 'M'
    },
    validation_results={'overall': True, 'fields': {...}},
    ocr_results={'valid': True, 'passed_fields': [...], ...},
    face_match_results={'match': True, 'distance': 0.35}
)
```

### Get User Statistics
```python
stats = db_service.get_user_statistics('user123', days=30)
print(f"Success rate: {stats['submissions']['success_rate']}%")
print(f"Total cost: ${stats['api_usage']['total_cost_usd']:.4f}")
```

### Query Submissions
```python
from database.connection import get_db_session
from database.repository import SubmissionRepository

with get_db_session() as session:
    repo = SubmissionRepository(session)
    
    # Get user's recent submissions
    submissions = repo.get_by_user('user123', limit=10)
    
    # Get statistics
    stats = repo.get_statistics(user_id='user123', days=30)
```

### Log API Usage
```python
db_service.log_api_usage(
    user_id='user123',
    api_operation='extract_text',
    model_name='gemini-1.5-flash',
    input_tokens=1500,
    output_tokens=300,
    estimated_cost=0.0003,
    success=True,
    duration_ms=2500
)
```

## Database Maintenance

### Backup Database
```powershell
# Using mysqldump
mysqldump -u root -p IDverification > backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

### Restore Database
```powershell
mysql -u root -p IDverification < backup_20250101_120000.sql
```

### Clean Old Records
```python
from database.connection import get_db_session
from database.models import Submission
from datetime import datetime

with get_db_session() as session:
    # Soft delete submissions past their retention date
    expired = session.query(Submission).filter(
        Submission.should_delete_after < datetime.utcnow(),
        Submission.is_deleted == False
    ).all()
    
    for sub in expired:
        sub.is_deleted = True
    session.commit()
```

### View Database Statistics
```python
from database.connection import get_db_session
from database.repository import SubmissionRepository, APIUsageRepository

with get_db_session() as session:
    submission_repo = SubmissionRepository(session)
    api_repo = APIUsageRepository(session)
    
    # Overall stats
    stats = submission_repo.get_statistics(days=30)
    api_stats = api_repo.get_total_usage(days=30)
    
    print(f"Total submissions: {stats['total_submissions']}")
    print(f"Success rate: {stats['success_rate']}%")
    print(f"Total API cost: ${api_stats['total_cost_usd']:.4f}")
```

## Troubleshooting

### Connection Errors
- Verify MySQL is running: Check MySQL Workbench
- Check credentials: Ensure username/password correct
- Verify database exists: `SHOW DATABASES;`
- Check port: Default is 3306

### Import Errors
```powershell
# Reinstall dependencies
pip install --upgrade mysql-connector-python SQLAlchemy cryptography
```

### Encryption Key Management
Generate a new encryption key:
```python
from database.db_utils import EncryptionManager
key = EncryptionManager.generate_key()
print(f"ENCRYPTION_KEY={key}")
```

Add to environment or `.env` file.

## Performance Tips

1. **Connection Pooling**: Already configured (5 connections, 10 overflow)
2. **Indexes**: Created on frequently queried fields (user_id, created_at, etc.)
3. **Soft Deletes**: Use soft deletion to preserve data integrity
4. **Batch Operations**: Use transactions for multiple inserts

## Security Best Practices

1. ✅ **Encrypt sensitive data** (ID numbers, names, DOB)
2. ✅ **Use environment variables** for credentials
3. ✅ **Enable audit logging** for all database operations
4. ✅ **Set data retention policies** (automatic deletion after 90 days)
5. ✅ **Use parameterized queries** (SQLAlchemy ORM prevents SQL injection)
6. ⚠️ **Rotate encryption keys** periodically
7. ⚠️ **Backup database** regularly
8. ⚠️ **Monitor access logs**

## Next Steps

- [ ] Implement user authentication system
- [ ] Add role-based access control (RBAC)
- [ ] Create admin dashboard for system monitoring
- [ ] Set up automated database backups
- [ ] Implement data retention policies with automated cleanup
- [ ] Add database replication for high availability
- [ ] Create API endpoints for external integrations

## Support

For issues or questions:
1. Check MySQL connection in MySQL Workbench
2. Review logs in `logs/` directory
3. Verify all dependencies installed
4. Check database tables created: `SHOW TABLES;`
