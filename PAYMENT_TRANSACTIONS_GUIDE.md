# Payment Transactions Database Guide

This document outlines the payment transaction tracking system implemented for the Fapshi payment integration.

## Overview

The system now includes a comprehensive payment transaction tracking database that stores detailed information about all payment attempts, their status, and related data. This provides better audit trails, analytics, and debugging capabilities.

## Database Schema

### Payment Transactions Table

```sql
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    fapshi_trans_id TEXT,
    brand_id TEXT NOT NULL,
    user_id TEXT,
    amount INTEGER NOT NULL,
    currency TEXT DEFAULT 'XAF',
    status TEXT DEFAULT 'PENDING',
    payment_method TEXT,
    payer_name TEXT,
    payer_email TEXT,
    payer_phone TEXT,
    redirect_url TEXT,
    message TEXT,
    fapshi_payment_link TEXT,
    payment_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Indexes

```sql
-- For faster lookups
CREATE INDEX idx_payment_transactions_external_id ON payment_transactions(external_id);
CREATE INDEX idx_payment_transactions_fapshi_trans_id ON payment_transactions(fapshi_trans_id);
CREATE INDEX idx_payment_transactions_brand_id ON payment_transactions(brand_id);
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Primary key, auto-incrementing |
| `external_id` | TEXT | Unique identifier for tracking (format: `brand_ai_{brand_id}_{random}`) |
| `fapshi_trans_id` | TEXT | Fapshi's transaction ID |
| `brand_id` | TEXT | Associated brand ID |
| `user_id` | TEXT | User who initiated the payment |
| `amount` | INTEGER | Payment amount in XAF |
| `currency` | TEXT | Currency code (default: XAF) |
| `status` | TEXT | Payment status (PENDING, SUCCESSFUL, FAILED, EXPIRED) |
| `payment_method` | TEXT | Payment method used (MTN, Orange, etc.) |
| `payer_name` | TEXT | Name of the person who paid |
| `payer_email` | TEXT | Email of the payer |
| `payer_phone` | TEXT | Phone number of the payer |
| `redirect_url` | TEXT | URL to redirect after payment |
| `message` | TEXT | Payment description/message |
| `fapshi_payment_link` | TEXT | Fapshi payment URL |
| `payment_data` | JSONB | Complete payment data from Fapshi |
| `created_at` | TIMESTAMP | When the transaction was created |
| `updated_at` | TIMESTAMP | When the transaction was last updated |
| `completed_at` | TIMESTAMP | When the payment was completed |

## Database Functions

### 1. Create Payment Transaction

```python
def create_payment_transaction(external_id, brand_id, user_id, amount, currency='XAF', 
                              redirect_url=None, message=None, payer_email=None):
    """Create a new payment transaction record"""
```

**Usage:**
```python
transaction_id = db.create_payment_transaction(
    external_id="brand_ai_123_abc456",
    brand_id="brand-123",
    user_id="user-456",
    amount=15000,
    currency="XAF",
    redirect_url="https://app.com/success",
    message="Payment for Brand Kit",
    payer_email="user@example.com"
)
```

### 2. Update Payment Transaction

```python
def update_payment_transaction(external_id, fapshi_trans_id=None, status=None, 
                              payment_link=None, payment_data=None, payer_name=None, 
                              payer_phone=None, payment_method=None):
    """Update payment transaction with Fapshi details"""
```

**Usage:**
```python
db.update_payment_transaction(
    external_id="brand_ai_123_abc456",
    fapshi_trans_id="TRANS123456",
    status="SUCCESSFUL",
    payment_link="https://fapshi.com/pay/abc123",
    payment_data={"amount": 15000, "status": "SUCCESSFUL"},
    payer_name="John Doe",
    payer_phone="+237123456789",
    payment_method="MTN"
)
```

### 3. Get Payment Transaction

```python
def get_payment_transaction(external_id=None, fapshi_trans_id=None):
    """Get payment transaction by external_id or fapshi_trans_id"""
```

**Usage:**
```python
# By external_id
transaction = db.get_payment_transaction(external_id="brand_ai_123_abc456")

# By Fapshi transaction ID
transaction = db.get_payment_transaction(fapshi_trans_id="TRANS123456")
```

### 4. Get Transactions by Brand

```python
def get_payment_transactions_by_brand(brand_id):
    """Get all payment transactions for a specific brand"""
```

**Usage:**
```python
transactions = db.get_payment_transactions_by_brand("brand-123")
```

### 5. Get Transactions by User

```python
def get_payment_transactions_by_user(user_id):
    """Get all payment transactions for a specific user"""
```

**Usage:**
```python
transactions = db.get_payment_transactions_by_user("user-456")
```

## API Endpoints

### 1. Get Transactions by Brand

**GET** `/api/payment/transactions/{brand_id}`

**Response:**
```json
{
  "success": true,
  "transactions": [
    {
      "id": 1,
      "external_id": "brand_ai_123_abc456",
      "fapshi_trans_id": "TRANS123456",
      "brand_id": "brand-123",
      "user_id": "user-456",
      "amount": 15000,
      "currency": "XAF",
      "status": "SUCCESSFUL",
      "payment_method": "MTN",
      "payer_name": "John Doe",
      "payer_email": "john@example.com",
      "payer_phone": "+237123456789",
      "created_at": "2023-12-25T10:00:00Z",
      "completed_at": "2023-12-25T10:05:00Z"
    }
  ],
  "count": 1
}
```

### 2. Get Transactions by User

**GET** `/api/payment/transactions/user/{user_id}`

**Response:** Same format as above

### 3. Get Specific Transaction

**GET** `/api/payment/transaction/{external_id}`

**Response:**
```json
{
  "success": true,
  "transaction": {
    "id": 1,
    "external_id": "brand_ai_123_abc456",
    "fapshi_trans_id": "TRANS123456",
    "brand_id": "brand-123",
    "user_id": "user-456",
    "amount": 15000,
    "currency": "XAF",
    "status": "SUCCESSFUL",
    "payment_method": "MTN",
    "payer_name": "John Doe",
    "payer_email": "john@example.com",
    "payer_phone": "+237123456789",
    "payment_data": {
      "transId": "TRANS123456",
      "status": "SUCCESSFUL",
      "amount": 15000,
      "currency": "XAF",
      "payerName": "John Doe",
      "email": "john@example.com",
      "phone_number": "+237123456789",
      "medium": "MTN"
    },
    "created_at": "2023-12-25T10:00:00Z",
    "updated_at": "2023-12-25T10:05:00Z",
    "completed_at": "2023-12-25T10:05:00Z"
  }
}
```

## Payment Flow with Database Tracking

1. **Payment Initiation:**
   - Frontend calls `/api/payment/initiate`
   - Backend creates payment transaction record with status `PENDING`
   - Backend calls Fapshi API to create payment link
   - Backend updates transaction with Fapshi details

2. **Payment Processing:**
   - User completes payment on Fapshi
   - Fapshi sends callback to `/api/payment/callback`
   - Backend updates transaction status to `SUCCESSFUL` or `FAILED`
   - Backend updates brand payment status

3. **Payment Verification:**
   - Frontend calls `/api/payment/verify`
   - Backend verifies payment with Fapshi API
   - Backend updates transaction with latest payment data

## Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Payment initiated but not completed |
| `SUCCESSFUL` | Payment completed successfully |
| `FAILED` | Payment failed |
| `EXPIRED` | Payment link expired |

## Benefits

1. **Complete Audit Trail:** Every payment attempt is tracked
2. **Analytics:** Can analyze payment patterns, success rates, etc.
3. **Debugging:** Easy to troubleshoot payment issues
4. **Reporting:** Generate payment reports for business insights
5. **Reconciliation:** Match payments with Fapshi records
6. **User Support:** Help users with payment-related queries

## Testing

Use the test script to verify the payment transaction system:

```bash
python test_fapshi_payment.py
```

The test includes:
- Payment initiation and database storage
- Payment verification and status updates
- Transaction retrieval by brand and user
- Payment callback processing

## Monitoring and Maintenance

1. **Regular Cleanup:** Consider archiving old transactions
2. **Performance:** Monitor query performance with indexes
3. **Backup:** Ensure regular database backups
4. **Analytics:** Use transaction data for business insights

## Security Considerations

1. **Data Privacy:** Payer information is stored - ensure GDPR compliance
2. **Access Control:** Limit access to payment transaction data
3. **Encryption:** Consider encrypting sensitive payment data
4. **Audit Logs:** Track who accesses payment transaction data


