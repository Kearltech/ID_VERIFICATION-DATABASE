# Quick Start - MySQL Database Integration

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
Already done! ✅ The packages are installed:
- mysql-connector-python
- SQLAlchemy  
- cryptography

### Step 2: Create Database in MySQL Workbench
1. Open MySQL Workbench
2. Connect to your local instance (127.0.0.1:3306)
3. Run this SQL:
```sql
CREATE DATABASE IDverification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3: Setup Tables
Run the setup script:
```powershell
python setup_database.py
```

Or manually:
```powershell
python database/setup.py --host 127.0.0.1 --port 3306 --user root --password YOUR_PASSWORD
```

### Step 4: Connect in App
1. Run: `streamlit run app_gemini.py`
2. In sidebar → Expand "🗄️ Database"
3. Expand "Database Settings"
4. Enter your MySQL credentials:
   - Host: 127.0.0.1
   - Port: 3306
   - Username: root
   - Password: (your MySQL password)
   - Database: IDverification
5. Click "Connect to Database"
6. See "✅ Database Connected"

## ✨ What You Get

### Automatic Features (When Connected)
✅ **All verification data saved to MySQL** (not just CSV)
✅ **Sensitive data encrypted** (ID numbers, names, DOB)
✅ **Detailed audit logs** of every validation
✅ **API usage tracking** (tokens, costs)
✅ **Statistics dashboard** - Click "View Statistics" button

### Database Tables Created
1. **users** - User accounts
2. **submissions** - All ID verifications (with encryption)
3. **validation_logs** - Detailed field validation results
4. **api_usage** - Gemini API call tracking
5. **audit_logs** - Complete audit trail

### Statistics Dashboard Shows
- Total submissions (last 30 days)
- Success rate percentage
- Breakdown by ID type (Ghana Card, Passport, etc.)
- API usage (total calls, tokens, cost in USD)
- Recent submissions table

## 💡 Usage Examples

### View Your Stats
1. Connect to database
2. Click "View Statistics" in sidebar
3. See comprehensive dashboard

### Query Database Directly
```python
from database.connection import get_db_session
from database.repository import SubmissionRepository

with get_db_session() as session:
    repo = SubmissionRepository(session)
    
    # Get recent submissions
    submissions = repo.get_by_user('default_user', limit=10)
    
    # Get statistics
    stats = repo.get_statistics(days=30)
    print(f"Success rate: {stats['success_rate']}%")
```

### Export Data
```python
from database.connection import get_db_session
from database.models import Submission
import pandas as pd

with get_db_session() as session:
    submissions = session.query(Submission).all()
    
    data = [{
        'date': s.created_at,
        'id_type': s.id_type,
        'valid': s.validation_overall,
        'face_match': s.face_match
    } for s in submissions]
    
    df = pd.DataFrame(data)
    df.to_csv('export.csv', index=False)
```

## 🔐 Security Features

### Data Encryption
Sensitive fields automatically encrypted:
- ID numbers (Ghana Card PIN, Passport #, etc.)
- Full names (firstname, surname)
- Date of birth

### Audit Trail
Every action logged:
- Who validated what ID
- When validation occurred
- What the result was
- Which API calls were made

### Data Retention
- Auto-deletion after 90 days (configurable)
- Soft delete (can be recovered)
- Secure data disposal

## 🛠️ Troubleshooting

### "Database not available"
```powershell
pip install mysql-connector-python SQLAlchemy cryptography
```

### "Connection refused"
- Check MySQL is running in MySQL Workbench
- Verify port 3306 is open
- Check username/password

### "Database doesn't exist"
```sql
CREATE DATABASE IDverification;
```

### "Access denied"
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON IDverification.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

## 📊 Database Schema Quick Reference

### submissions table
- `submission_id` - Unique ID (UUID)
- `user_id` - User who submitted
- `id_type` - Ghana Card, Passport, etc.
- `id_number_encrypted` - Encrypted ID number
- `surname_encrypted` - Encrypted surname
- `firstname_encrypted` - Encrypted firstname
- `validation_overall` - Pass/Fail
- `face_match` - Face comparison result
- `gemini_confidence` - AI confidence score
- `created_at` - Timestamp

### Full schema in `database/models.py`

## 🎯 Next Steps

1. ✅ Database connected
2. ✅ Tables created
3. ✅ Test a verification
4. ✅ Check statistics dashboard
5. 📈 Monitor API usage and costs
6. 🔄 Set up automated backups (recommended)

## 📞 Support

See full documentation: `DATABASE_README.md`
Database models: `database/models.py`
Repository methods: `database/repository.py`
