# Referral Code Generation Scripts

This directory contains scripts to generate referral codes for existing users in your database who don't have them yet.

## 📁 Available Scripts

### 1. **`generate_referral_codes.py`** - Comprehensive Script
- **Full-featured** referral code generation
- **Detailed logging** and progress tracking
- **Verification** of results
- **Error handling** and reporting
- **Summary statistics** after completion

### 2. **`quick_referral_codes.py`** - Quick Script
- **Fast execution** for quick tasks
- **Command line options** for flexibility
- **Dry run mode** for testing
- **Limit processing** for large databases

## 🚀 How to Use

### **Prerequisites:**
1. **Activate your virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Ensure your database is accessible** (Flask app can connect)

3. **Make sure the `db.py` module is available**

### **Option 1: Comprehensive Generation (Recommended)**
```bash
python3 generate_referral_codes.py
```

**Features:**
- ✅ Generates codes for all users without referral codes
- ✅ Ensures uniqueness across the database
- ✅ Provides detailed progress and error reporting
- ✅ Verifies results after completion
- ✅ Shows summary statistics

### **Option 2: Quick Generation**
```bash
# Generate for all users
python3 quick_referral_codes.py

# Dry run (no changes to database)
python3 quick_referral_codes.py --dry-run

# Limit to first 10 users
python3 quick_referral_codes.py --limit=10

# Combine options
python3 quick_referral_codes.py --dry-run --limit=5
```

## 🔧 How It Works

### **1. Database Scan**
- Queries for users with `NULL` or empty `referral_code` fields
- Orders by creation date (oldest first)

### **2. Code Generation**
- Generates 8-character alphanumeric codes (A-Z, 0-9)
- Ensures uniqueness by checking database before assignment
- Retries up to 100 times if duplicates found

### **3. Database Update**
- Updates each user's `referral_code` field
- Commits changes immediately
- Tracks success/failure for each user

### **4. Verification**
- Counts total users vs. users with codes
- Shows sample generated codes
- Confirms all users now have referral codes

## 📊 Expected Output

### **Comprehensive Script:**
```
🚀 Referral Code Generation Script
==================================================
✅ Database connection successful
🔍 Checking for users without referral codes...
📊 Found 15 users without referral codes

==================================================
Processing user: JohnDoe (john@example.com)
  Generated code: ABC12345
  ✅ Successfully assigned referral code: ABC12345

Processing user: JaneSmith (jane@example.com)
  Generated code: XYZ98765
  ✅ Successfully assigned referral code: XYZ98765

==================================================
📊 GENERATION SUMMARY
==================================================
Total users processed: 15
Successful updates: 15
Failed updates: 0

🎉 Successfully generated referral codes for 15 users!
💡 Users can now share their referral codes with others

🔍 Verifying referral code generation...
==================================================
📊 Verification Results:
  Total users: 25
  Users with referral codes: 25
  Users without referral codes: 0
✅ All users now have referral codes!

📝 Sample referral codes:
  JohnDoe (john@example.com): ABC12345
  JaneSmith (jane@example.com): XYZ98765
  AdminUser (admin@example.com): DEF45678
```

### **Quick Script:**
```
🚀 Quick Referral Code Generation
========================================
📊 Found 15 users without referral codes

1. JohnDoe (john@example.com)
   ✅ Generated: ABC12345

2. JaneSmith (jane@example.com)
   ✅ Generated: XYZ98765

🎉 Successfully processed 15 users!
```

## ⚠️ Important Notes

### **Safety Features:**
- **No duplicate codes**: Each code is unique across the database
- **Transaction safety**: Uses database transactions for data integrity
- **Error handling**: Continues processing even if individual users fail
- **Dry run mode**: Test without making changes

### **Database Requirements:**
- `users` table must exist with `userId` and `referral_code` columns
- `referral_code` column should be `TEXT UNIQUE` or similar
- Database connection must be accessible

### **Performance:**
- **Small databases** (< 1000 users): Use comprehensive script
- **Large databases** (> 1000 users): Use quick script with `--limit` option
- **Testing**: Always use `--dry-run` first on production databases

## 🐛 Troubleshooting

### **Common Issues:**

1. **Import Error:**
   ```bash
   ❌ Import error: No module named 'db'
   ```
   **Solution:** Activate virtual environment and ensure `db.py` is accessible

2. **Database Connection Error:**
   ```bash
   ❌ Database connection failed
   ```
   **Solution:** Check database configuration and ensure Flask app can connect

3. **Permission Error:**
   ```bash
   ❌ Permission denied for table users
   ```
   **Solution:** Ensure database user has UPDATE permissions on users table

### **Debug Mode:**
For detailed error information, the scripts include full traceback printing when exceptions occur.

## 🎯 Use Cases

### **Initial Setup:**
- First-time deployment of referral system
- Migrating existing users to new referral structure

### **Maintenance:**
- Adding referral codes to users who somehow don't have them
- Regenerating codes if needed (after clearing existing ones)

### **Testing:**
- Verifying referral code generation logic
- Testing database constraints and uniqueness

## 🔄 Running Multiple Times

The scripts are **safe to run multiple times**:
- ✅ Users with existing referral codes are skipped
- ✅ Only processes users without codes
- ✅ No duplicate codes are generated
- ✅ Can be used for incremental updates

## 📝 Customization

### **Code Length:**
Change the `length` parameter in `generate_referral_code()` function:
```python
def generate_referral_code(length=10):  # 10 characters instead of 8
```

### **Code Format:**
Modify the `characters` variable to change allowed characters:
```python
characters = string.ascii_uppercase + string.digits + string.ascii_lowercase  # Include lowercase
```

### **Database Schema:**
If your database uses different column names, update the SQL queries accordingly.

---

**Happy Referral Code Generation! 🎉**
