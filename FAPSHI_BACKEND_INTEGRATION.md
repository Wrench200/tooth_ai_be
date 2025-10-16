# Fapshi Backend Payment Integration

This document outlines the backend implementation of Fapshi payment gateway integration.

## Overview

The payment system has been moved from frontend to backend for better security and centralized payment processing. All Fapshi API calls are now handled by the backend, and the frontend communicates with the backend through REST API endpoints.

## Environment Variables

Add the following environment variables to your backend `.env` file:

```env
# Fapshi Configuration
FAPSHI_API_URL=https://live.fapshi.com
FAPSHI_API_KEY=your_fapshi_api_key_here
FAPSHI_API_USER=your_fapshi_api_user_here

# Backend URL (for frontend callbacks)
BACKEND_URL=http://localhost:8080
```

## Backend Files

### 1. `fapshi_payment.py`
- **Purpose**: Core Fapshi payment integration class
- **Features**:
  - Payment initiation
  - Payment status checking
  - Payment verification
  - Error handling and logging

### 2. `main.py` - Payment Endpoints
- **`POST /api/payment/initiate`** - Initiate payment
- **`POST /api/payment/verify`** - Verify payment
- **`GET /api/payment/status`** - Get payment status
- **`POST /api/payment/callback`** - Handle payment callbacks

## API Endpoints

### 1. Initiate Payment
**POST** `/api/payment/initiate`

**Request Body:**
```json
{
  "amount": 15000,
  "brandId": "brand-uuid-here",
  "email": "customer@example.com",
  "redirectUrl": "https://yourapp.com/payment-success",
  "userId": "user-123",
  "message": "Payment for Brand Kit"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment initiated successfully",
  "data": {
    "link": "https://fapshi.com/pay/abc123",
    "transId": "TRANS123456",
    "dateInitiated": "2023-12-25"
  },
  "external_id": "brand_ai_brand-uuid-here_abc123"
}
```

### 2. Verify Payment
**POST** `/api/payment/verify`

**Request Body:**
```json
{
  "transId": "TRANS123456"
}
```

**Response:**
```json
{
  "success": true,
  "verified": true,
  "message": "Payment verified successfully",
  "payment_data": {
    "transId": "TRANS123456",
    "status": "SUCCESSFUL",
    "amount": 15000,
    "currency": "XAF",
    "payerName": "John Doe",
    "email": "john@example.com"
  }
}
```

### 3. Get Payment Status
**GET** `/api/payment/status?transId=TRANS123456`

**Response:**
```json
{
  "success": true,
  "payment_data": {
    "transId": "TRANS123456",
    "status": "SUCCESSFUL",
    "amount": 15000,
    "currency": "XAF"
  }
}
```

### 4. Payment Callback
**POST** `/api/payment/callback`

**Request Body:**
```json
{
  "transId": "TRANS123456",
  "status": "SUCCESSFUL",
  "amount": 15000,
  "externalId": "brand_ai_brand-uuid-here_abc123",
  "currency": "XAF",
  "payerName": "John Doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Fapshi payment callback processed successfully"
}
```

## Payment Flow

1. **Frontend calls backend** `/api/payment/initiate` with payment details
2. **Backend calls Fapshi API** to create payment link
3. **Backend returns payment link** to frontend
4. **Frontend redirects user** to Fapshi payment page
5. **User completes payment** on Fapshi platform
6. **Fapshi redirects user** back to frontend with transaction ID
7. **Frontend calls backend** `/api/payment/verify` to verify payment
8. **Backend verifies payment** with Fapshi API
9. **Backend updates database** with payment status
10. **Backend processes referral rewards** if applicable

## Security Features

- **API Key Protection**: Fapshi API keys are stored securely on backend
- **Input Validation**: All payment requests are validated
- **Error Handling**: Comprehensive error handling and logging
- **Transaction Tracking**: Unique external IDs for transaction tracking

## Database Integration

The payment system integrates with the existing database:

- **Brand Payment Status**: Updated automatically on successful payment
- **Referral Rewards**: Processed automatically for successful payments
- **Transaction Tracking**: External IDs link payments to brands

## Testing

Use the provided test script to verify the integration:

```bash
python3 test_fapshi_payment.py
```

The test script will:
1. Test payment initiation
2. Test payment status checking
3. Test payment verification
4. Test payment callbacks
5. Test brand payment status updates

## Error Handling

The system handles various error scenarios:

- **Network Errors**: Retry logic and fallback responses
- **API Errors**: Proper error messages and status codes
- **Invalid Data**: Input validation and error responses
- **Payment Failures**: Graceful handling of failed payments

## Logging

All payment operations are logged with:
- Request/response data
- Error messages
- Transaction IDs
- Timestamps

## Production Deployment

For production deployment:

1. **Update API URL**: Change to `https://fapshi.com`
2. **Use Production Keys**: Replace test API keys with production keys
3. **Update Redirect URLs**: Use production domain URLs
4. **Enable HTTPS**: Ensure all communication is over HTTPS
5. **Monitor Logs**: Set up proper logging and monitoring

## Frontend Integration

The frontend has been updated to use the backend endpoints:

- **`useFapshiPayment` hook**: Updated to call backend APIs
- **Payment pages**: Updated to use backend endpoints
- **Callback handling**: Forwards callbacks to backend

## Migration Notes

The following changes were made during migration:

1. **Removed**: Direct Fapshi API calls from frontend
2. **Added**: Backend payment endpoints
3. **Updated**: Frontend to use backend APIs
4. **Maintained**: Existing payment flow and user experience

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Test with the provided test script
4. Check Fapshi API documentation for any changes


