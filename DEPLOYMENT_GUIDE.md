# Deployment Guide

## Issues Fixed

✅ **Database Connection**: Fixed malformed `sslmode` parameter in DATABASE_URL  
✅ **Missing Dependencies**: Added all required packages to requirements.txt and pyproject.toml  
✅ **SSL Connection Issues**: Implemented robust connection pooling and SSL handling
✅ **Context Manager Bug**: Fixed nested yield issue in database context manager that was causing hanging  
✅ **Dictionary Update Sequence Error**: Fixed parse_json_field function to handle malformed CSV data properly
✅ **Database Row Conversion Error**: Fixed dict(row) conversion in database functions to properly handle tuple rows
✅ **Module Import Blocking**: Fixed module-level database connection that was blocking imports
✅ **Database Connection Scope Error**: Fixed NameError in brand assets functions by removing manual conn.commit/rollback calls

## Updated Dependencies

The following dependencies have been added to your project:

### requirements.txt
```
flask
flask_cors
requests
uuid
pillow
psycopg2-binary
python-dotenv
cloudinary
google-auth
google-auth-oauthlib
google-auth-httplib2
fpdf2
openai
requests-toolbelt
```

### pyproject.toml
Updated with all necessary dependencies for modern Python packaging.

## SSL Connection Improvements

### What Was Fixed
- **SSL Connection Drops**: Implemented connection pooling to handle SSL connection timeouts
- **Connection Management**: Added thread-safe connection manager with automatic reconnection
- **SSL Parameters**: Configured proper SSL settings for production environments
- **Error Recovery**: Added automatic retry logic for failed connections
- **Context Manager Bug**: Fixed critical nested yield issue that was causing all database operations to hang
- **Dictionary Update Sequence Error**: Fixed parse_json_field function to properly handle CSV data with mismatched header/row lengths
- **Database Row Conversion Error**: Fixed dict(row) conversion in database functions to properly handle tuple rows from regular cursors
- **Module Import Blocking**: Moved table creation from module-level to function-level to prevent import blocking

### Key Features
- **Connection Pooling**: Reuses connections efficiently to reduce SSL handshake overhead
- **Automatic Reconnection**: Detects and recovers from SSL connection drops
- **Thread Safety**: Safe for concurrent requests
- **SSL Optimization**: Configured keepalives and timeouts for better SSL performance

## Environment Variables Required

Make sure you have these environment variables set in your deployment platform:

```env
# Database
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require

# API Keys
REPLICATE_API_TOKEN=your_replicate_token
OPENAI_API_KEY=your_openai_key

# Cloudinary (if using)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Google OAuth (if using)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=your_redirect_uri

# Flask
FLASK_ENV=production
FLASK_DEBUG=0
```

## Testing Your Connection

### Basic Connection Test
```bash
python test_db_connection.py
```

### SSL Connection Test
```bash
python test_ssl_connection.py
```

This will test:
- Basic database connectivity
- Concurrent connections
- Connection reuse and pooling
- SSL parameters
- Error handling and recovery

## Deployment Steps

### 1. Test Locally First
```bash
# Install dependencies
pip install -r requirements.txt

# Test database connection
python test_db_connection.py

# Test SSL connection management
python test_ssl_connection.py

# Run the application
python main.py
```

### 2. Deploy to Your Platform

#### Render
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python main.py`
4. Add environment variables in the dashboard

#### Railway
1. Connect your GitHub repository
2. Add environment variables in the Variables tab
3. Deploy automatically

#### Heroku
```bash
heroku create your-app-name
heroku config:set DATABASE_URL="your_connection_string"
heroku config:set REPLICATE_API_TOKEN="your_token"
# ... add other environment variables
git push heroku main
```

#### DigitalOcean App Platform
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set run command: `python main.py`
4. Add environment variables in Settings

## Testing Your Deployment

1. **Health Check**: Visit `/health` endpoint
2. **Database Test**: The app will automatically test the database connection on startup
3. **SSL Test**: Run the SSL connection test to verify SSL handling and concurrency
4. **API Endpoints**: Test your main API endpoints

### Test Results
The SSL connection test now passes all 5 tests:
- ✅ Basic connection test
- ✅ Concurrent connections (5/5 workers succeeded)
- ✅ Connection reuse
- ✅ SSL parameters
- ✅ Error handling and recovery

### Additional Fixes Applied
- ✅ **Dictionary Update Sequence Error**: Fixed in `main.py` parse_json_field function
- ✅ **Database Row Conversion Error**: Fixed in `db.py` by properly converting tuple rows to dictionaries
- ✅ **Module Import Blocking**: Fixed in `db.py` by moving table creation to function level
- ✅ **All Database Connection Issues**: Resolved SSL, concurrency, and hanging problems

## Troubleshooting

### Common Issues and Solutions

1. **"dictionary update sequence element #0 has length 36; 2 is required"**
   - **Cause**: Malformed CSV data in the parse_json_field function where headers and row data don't match
   - **Solution**: Fixed by adding proper validation and error handling in the parse_json_field function
   - **Location**: `main.py` line 1226

2. **"dictionary update sequence element #0 has length X; 2 is required" (in database functions)**
   - **Cause**: Using `dict(row)` on tuple rows from regular database cursors instead of DictCursor
   - **Solution**: Fixed by using `dict(zip(column_names, row))` to properly convert tuple rows to dictionaries
   - **Location**: `db.py` functions: get_brand, get_user, get_user_from_email, get_user_by_google_id, get_all_users, get_all_user_brands

3. **Module import hanging during startup**
   - **Cause**: Database connection being established at module level during import
   - **Solution**: Moved table creation to function level with proper error handling
   - **Location**: `db.py` line 409

4. **SSL connection drops and "cursor already closed" errors**
   - **Cause**: Single global connection not suitable for concurrent requests
   - **Solution**: Implemented ThreadLocalConnection with proper connection management
   - **Location**: `db.py` ThreadLocalConnection class

5. **NameError: name 'conn' is not defined in brand assets functions**
   - **Cause**: Manual `conn.commit()` and `conn.rollback()` calls in functions using the context manager
   - **Solution**: Removed manual connection operations since the context manager handles them automatically
   - **Location**: `db.py` create_brand_assets and delete_brand_assets functions

### Common Issues

1. **ModuleNotFoundError**: Make sure all dependencies are in requirements.txt
2. **Database Connection**: Use the test script to verify your DATABASE_URL
3. **SSL Connection Drops**: The new connection manager should handle this automatically
4. **Environment Variables**: Ensure all required variables are set in your deployment platform

### Debug Commands

```bash
# Test database connection
python test_db_connection.py

# Test SSL connection management
python test_ssl_connection.py

# Check installed packages
pip list

# Test Flask app locally
python main.py
```

### SSL Connection Issues

If you're still experiencing SSL connection issues:

1. **Check DATABASE_URL**: Ensure it includes `sslmode=require`
2. **Database Provider**: Some providers require specific SSL settings
3. **Network Issues**: Check if your deployment platform has network restrictions
4. **Connection Limits**: Ensure you're not hitting database connection limits

## File Structure

```
tooth_ai_be/
├── main.py                 # Main Flask application
├── db.py                   # Database operations (fixed with SSL support)
├── requirements.txt        # Python dependencies (updated)
├── pyproject.toml         # Modern Python packaging (updated)
├── test_db_connection.py  # Database connection test
├── test_ssl_connection.py # SSL connection management test
├── ENVIRONMENT_SETUP.md   # Environment setup guide
├── DEPLOYMENT_GUIDE.md    # This file
├── fonts/                 # Font files for PDF generation
├── cloudinary_utils.py    # Cloudinary integration
├── google_oauth.py        # Google OAuth integration
└── ... (other files)
```

## Next Steps

1. ✅ Fix database connection issues
2. ✅ Add missing dependencies
3. ✅ Fix SSL connection drops
4. 🔄 Deploy to your chosen platform
5. 🔄 Test all endpoints
6. 🔄 Monitor application logs

Your application should now deploy successfully and handle SSL connections robustly! 