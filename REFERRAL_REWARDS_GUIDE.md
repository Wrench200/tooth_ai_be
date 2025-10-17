# Referral Rewards System

This document explains the referral reward system implemented in Jara AI, where users earn rewards when they or their referrals pay for premium brands.

## 🎯 **Overview**

When a user pays **15,000 XAF** for a full brand, the system automatically distributes **20% (3,000 XAF)** as referral rewards:

- **10% (1,500 XAF)** → Brand creator (the user who paid)
- **10% (1,500 XAF)** → Referrer (if the user was referred by someone)

## 🔧 **Implementation Details**

### **Backend Components**

#### **1. Database Functions (`db.py`)**

**`process_referral_reward(brand_id, user_id, amount_paid=15000)`**
- Processes referral rewards when a payment is successful
- Calculates 20% of payment amount as total rewards
- Splits rewards equally between brand creator and referrer
- Updates user's `referred_amount` field in database

**`get_referral_reward_history(user_id)`**
- Retrieves user's referral reward history and statistics
- Returns total earnings, referral count, and other metrics

#### **2. API Endpoints (`main.py`)**

**`POST /api/payment/verify`**
- Enhanced to automatically process referral rewards on successful payment
- Triggers reward distribution after brand payment status is updated

**`GET /referral/rewards/{user_id}`**
- Returns detailed referral reward information for a user
- Includes earnings breakdown and referral statistics

### **Frontend Components**

#### **1. React Hooks (`hooks.ts`)**

**`useReferralRewards(userId)`**
- Fetches user's referral reward data
- Provides real-time earnings and statistics

**`useReferralStats(userId)`**
- Gets user's referral statistics
- Used for displaying referral performance

#### **2. Dashboard Integration**

**Dashboard Overview Page**
- Displays real-time referral earnings
- Shows total referrals and earnings in XAF
- Updates automatically when rewards are processed

## 💰 **Reward Calculation**

### **Example Scenarios**

#### **Scenario 1: User with Referrer**
```
Payment: 15,000 XAF
Total Rewards: 3,000 XAF (20%)
├── Brand Creator: 1,500 XAF (10%)
└── Referrer: 1,500 XAF (10%)
```

#### **Scenario 2: User without Referrer**
```
Payment: 15,000 XAF
Total Rewards: 1,500 XAF (10%)
└── Brand Creator: 1,500 XAF (10%)
```

### **Reward Processing Flow**

1. **Payment Verification** → User completes 15k XAF payment
2. **Brand Status Update** → Brand payment status set to `true`
3. **Reward Calculation** → System calculates 20% of payment
4. **User Lookup** → Check if user has a referrer
5. **Reward Distribution** → Update both users' `referred_amount`
6. **Logging** → Log all reward transactions

## 🗄️ **Database Schema**

### **Users Table**
```sql
referral_code TEXT UNIQUE,           -- User's unique referral code
referred_by TEXT,                    -- ID of user who referred them
referred_users INT DEFAULT 0,        -- Number of users they referred
referred_amount INT DEFAULT 0,       -- Total earnings from referrals
```

### **Payment Transactions Table**
```sql
referral_reward_processed BOOLEAN DEFAULT FALSE  -- Tracks if rewards were processed
```

## 🔄 **API Endpoints**

### **Get Referral Rewards**
```http
GET /referral/rewards/{user_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "userId": "user-uuid",
    "referral_code": "ABC12345",
    "total_referrals": 5,
    "total_earnings": 7500,
    "can_refer": true,
    "referred_by": "referrer-uuid",
    "earnings_breakdown": {
      "from_referrals": 7500,
      "from_purchases": 0,
      "total": 7500
    }
  }
}
```

### **Payment Verification (Enhanced)**
```http
POST /api/payment/verify
```

**Request:**
```json
{
  "transId": "fapshi-transaction-id"
}
```

**Response:**
```json
{
  "success": true,
  "verified": true,
  "message": "Payment verified successfully",
  "payment_data": {
    "amount": 15000,
    "status": "SUCCESSFUL",
    "externalId": "brand_ai_brand-uuid"
  }
}
```

## 🧪 **Testing**

### **Test Script**
Run the test script to verify the referral reward system:

```bash
cd /home/wrench/Documents/jara/backend
python3 test_referral_rewards.py
```

### **Manual Testing**

1. **Create Test Users:**
   - User A (referrer)
   - User B (referred by User A)

2. **Generate Referral Code:**
   - User A gets a referral code
   - User B signs up using User A's code

3. **Test Payment:**
   - User B creates a brand
   - User B pays 15,000 XAF for premium
   - Check backend logs for reward processing

4. **Verify Rewards:**
   - Check User A's `referred_amount` increased by 1,500 XAF
   - Check User B's `referred_amount` increased by 1,500 XAF

## 📊 **Monitoring & Logs**

### **Backend Logs**
The system provides detailed logging for referral reward processing:

```
🔄 Processing referral reward for brand brand-uuid, user user-uuid, amount 15000
💰 Total reward: 3000 XAF, Individual reward: 1500 XAF
✅ Brand creator user-uuid rewarded 1500 XAF
✅ Referrer referrer-uuid rewarded 1500 XAF
```

### **Error Handling**
- Referral reward processing failures don't affect payment verification
- All errors are logged for debugging
- Users still get their brands even if reward processing fails

## 🔒 **Security Features**

- **Authorization**: Users can only view their own referral data
- **Validation**: All user IDs and amounts are validated
- **Atomic Operations**: Database transactions ensure data consistency
- **Error Isolation**: Reward processing failures don't affect payments

## 🚀 **Deployment Notes**

1. **Database Migration**: Ensure all referral fields exist in users table
2. **Backend Deployment**: Deploy updated backend with referral reward logic
3. **Frontend Update**: Deploy frontend with new referral hooks
4. **Testing**: Run test script to verify functionality
5. **Monitoring**: Monitor logs for successful reward processing

## 📈 **Future Enhancements**

- **Reward History**: Detailed transaction history for each reward
- **Withdrawal System**: Allow users to withdraw their earnings
- **Tiered Rewards**: Different reward percentages based on user tier
- **Analytics Dashboard**: Comprehensive referral performance analytics
- **Notification System**: Notify users when they earn rewards

## 🎉 **Benefits**

- **User Engagement**: Encourages users to refer others
- **Revenue Sharing**: Rewards both creators and referrers
- **Viral Growth**: Creates incentive for organic user acquisition
- **User Retention**: Provides ongoing value to active users
- **Transparency**: Clear reward structure and tracking

The referral reward system is now fully implemented and will automatically process rewards whenever users pay for premium brands! 🎉
