# Render Deployment Guide

## Overview
This guide covers deploying ToothAI on Render's free tier and handling the 15-minute sleep timeout.

## Deployment Steps

### 1. Render Configuration
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Environment**: Python 3.9+

### 2. Environment Variables
Set these in your Render dashboard:
```env
DATABASE_URL=your_neon_postgres_url
OPENAI_API_KEY=your_openai_key
REPLICATE_API_TOKEN=your_replicate_token
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Handling Sleep Timeout

### Option 1: External Keep-Alive Service
Use a free service like UptimeRobot or Cron-job.org to ping your app:

**UptimeRobot Setup:**
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add a new monitor
3. **Monitor Type**: HTTP(s)
4. **URL**: `https://your-app-name.onrender.com/health`
5. **Check Interval**: 5 minutes
6. **Alert**: Only when down

**Cron-job.org Setup:**
1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a new cronjob
3. **URL**: `https://your-app-name.onrender.com/health`
4. **Schedule**: Every 10 minutes
5. **Method**: GET

### Option 2: Local Keep-Alive Script
Run the included `keep_alive.py` script on your local machine:

```bash
# Install dependencies
pip install requests

# Set your app URL
export APP_URL=https://your-app-name.onrender.com

# Run the script
python keep_alive.py
```

### Option 3: GitHub Actions (Free)
Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep App Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping App
        run: |
          curl -X GET https://your-app-name.onrender.com/health
```

## Performance Optimizations

### 1. Request Timeouts
- Frontend should handle timeouts gracefully
- Consider implementing progress indicators for long operations
- Use the `/status` endpoint to check app health

### 2. Cold Start Handling
- First request after sleep may take 30-60 seconds
- Implement loading states in your frontend
- Consider showing estimated wait times

### 3. Error Handling
```javascript
// Frontend example
async function callAPI() {
  try {
    const response = await fetch('/get_results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      timeout: 300000 // 5 minutes
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'TimeoutError') {
      // Handle timeout - app might be waking up
      return { error: 'App is starting up, please try again in 30 seconds' };
    }
    throw error;
  }
}
```

## Monitoring

### Health Check Endpoints
- `GET /health` - Basic health check
- `GET /status` - Detailed status with database connection

### Expected Response Times
- **Cold Start**: 30-60 seconds
- **Warm Start**: 1-5 seconds
- **API Calls**: 2-10 seconds
- **Image Generation**: 30-120 seconds

## Troubleshooting

### Common Issues

1. **App Not Responding**
   - Check if app is sleeping (first request after 15+ minutes)
   - Verify keep-alive service is working
   - Check Render logs for errors

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is correct
   - Check if Neon database is active
   - Test connection with `/status` endpoint

3. **Image Generation Fails**
   - Verify Replicate API token
   - Check Cloudinary credentials
   - Review error logs in Render dashboard

### Logs
Monitor your app logs in Render dashboard:
- **Build Logs**: Check for dependency issues
- **Runtime Logs**: Monitor API calls and errors
- **Request Logs**: Track response times and failures

## Cost Considerations

### Free Tier Limits
- **Sleep Timeout**: 15 minutes
- **Build Time**: 10 minutes
- **Bandwidth**: 100 GB/month
- **Runtime**: 750 hours/month

### Upgrade Options
Consider upgrading to paid tier if you need:
- No sleep timeout
- Faster cold starts
- More bandwidth
- Custom domains

## Best Practices

1. **Keep-Alive**: Always use a keep-alive service
2. **Error Handling**: Implement robust error handling
3. **Loading States**: Show loading indicators for long operations
4. **Retry Logic**: Implement retry logic for failed requests
5. **Monitoring**: Regularly check app status
6. **Backup**: Keep local development environment ready 