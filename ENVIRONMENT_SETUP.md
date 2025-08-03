# Environment Setup Guide

## Database Connection Issue Fix

The error you're encountering is due to a malformed `DATABASE_URL` environment variable. The `sslmode` parameter is missing its value.

## Required Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require

# Cloudinary Configuration (if using)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Google OAuth (if using)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Other configurations
FLASK_ENV=production
FLASK_DEBUG=0
```

## Common DATABASE_URL Issues

### 1. Malformed sslmode parameter
**Wrong:**
```
postgresql://user:pass@host:port/db?sslmode&other=value
```

**Correct:**
```
postgresql://user:pass@host:port/db?sslmode=require&other=value
```

### 2. Missing sslmode parameter
**Wrong:**
```
postgresql://user:pass@host:port/db
```

**Correct:**
```
postgresql://user:pass@host:port/db?sslmode=require
```

### 3. Special characters in password
If your password contains special characters, URL-encode them:
- `@` becomes `%40`
- `#` becomes `%23`
- `%` becomes `%25`
- `&` becomes `%26`
- `+` becomes `%2B`
- `/` becomes `%2F`
- `:` becomes `%3A`

## Testing Your Connection

Run the test script to verify your database connection:

```bash
python test_db_connection.py
```

## Deployment Platforms

### Render
1. Go to your service dashboard
2. Navigate to "Environment" tab
3. Add environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - Other required variables

### Railway
1. Go to your project dashboard
2. Navigate to "Variables" tab
3. Add environment variables

### Heroku
```bash
heroku config:set DATABASE_URL="your_connection_string"
```

### DigitalOcean App Platform
1. Go to your app dashboard
2. Navigate to "Settings" > "Environment Variables"
3. Add required variables

## Troubleshooting

1. **Test locally first:**
   ```bash
   python test_db_connection.py
   ```

2. **Check your DATABASE_URL format:**
   - Must start with `postgresql://` or `postgres://`
   - Must include `sslmode=require` for production
   - Password must be URL-encoded if it contains special characters

3. **Verify database accessibility:**
   - Ensure your database host allows connections from your deployment platform
   - Check firewall settings
   - Verify database credentials

4. **Common fixes:**
   - Add `sslmode=require` to your DATABASE_URL
   - URL-encode special characters in password
   - Ensure the database exists and is accessible 