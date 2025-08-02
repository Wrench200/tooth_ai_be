# Google OAuth Setup Guide

## Overview
This guide will help you set up Google OAuth authentication for your ToothAI application.

## Prerequisites
- Google Cloud Console account
- Your Flask application running

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API

## Step 2: Configure OAuth Consent Screen

1. In Google Cloud Console, go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "ToothAI"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/userinfo.email`
5. Add test users (your email addresses)

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set the following:
   - Name: "ToothAI Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:3000` (for development)
     - `http://localhost:8080` (for development)
     - Your production domain
   - Authorized redirect URIs:
     - `http://localhost:8080/auth/google/callback` (for development)
     - `https://yourdomain.com/auth/google/callback` (for production)
5. Click "Create"
6. Copy the Client ID and Client Secret

## Step 4: Update Environment Variables

Add these to your `.env` file:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
```

## Step 5: Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

## API Endpoints

### 1. Initiate Google OAuth Flow
```http
GET /auth/google
```

**Response:**
```json
{
    "success": true,
    "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
    "state": "random_state_string"
}
```

### 2. Google OAuth Callback (Web)
```http
GET /auth/google/callback?code=authorization_code&state=state_string
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "userId": "user_uuid",
        "username": "User Name",
        "email": "user@example.com",
        "profile_picture": "https://...",
        "auth_provider": "google"
    }
}
```

### 3. Google Token Authentication (Mobile)
```http
POST /auth/google/token
Content-Type: application/json

{
    "id_token": "google_id_token_here"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "userId": "user_uuid",
        "username": "User Name",
        "email": "user@example.com",
        "profile_picture": "https://...",
        "auth_provider": "google"
    }
}
```

## Frontend Integration

### Web Application (React/Vue/Angular)

```javascript
// 1. Get auth URL
const response = await fetch('/auth/google');
const { auth_url } = await response.json();

// 2. Redirect to Google
window.location.href = auth_url;

// 3. Handle callback (Google will redirect back to your callback URL)
// The callback endpoint will return user data
```

### Mobile Application (React Native/Flutter)

```javascript
// 1. Use Google Sign-In SDK to get ID token
import { GoogleSignin } from '@react-native-google-signin/google-signin';

const { idToken } = await GoogleSignin.signIn();

// 2. Send token to your backend
const response = await fetch('/auth/google/token', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id_token: idToken })
});

const { user } = await response.json();
```

## Security Considerations

1. **HTTPS in Production**: Always use HTTPS in production
2. **State Parameter**: The state parameter helps prevent CSRF attacks
3. **Token Verification**: Always verify Google tokens on the backend
4. **User Data**: Store only necessary user data
5. **Error Handling**: Implement proper error handling for failed authentications

## Troubleshooting

### Common Issues:

1. **"Invalid redirect URI"**
   - Check that your redirect URI exactly matches what's configured in Google Console
   - Include protocol (http/https) and port number

2. **"Access blocked"**
   - Make sure your app is published or you're using a test user
   - Check OAuth consent screen configuration

3. **"Invalid client"**
   - Verify your Client ID and Client Secret are correct
   - Check that the credentials are for a web application

4. **Database errors**
   - Ensure the database migration ran successfully
   - Check that the users table has the new columns

## Testing

1. Start your Flask application
2. Visit `http://localhost:8080/auth/google`
3. You should be redirected to Google's consent screen
4. After authorization, you should be redirected back with user data

## Production Deployment

1. Update redirect URIs in Google Console to use your production domain
2. Update environment variables with production values
3. Ensure HTTPS is enabled
4. Test the complete flow in production environment 