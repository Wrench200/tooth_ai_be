# Referral System Guide

## Overview
The referral system allows users to invite friends and earn rewards when they sign up and use the platform. Each user gets a unique referral code that they can share with others.

## Features

### 🔑 **Referral Code Generation**
- **Automatic**: Every new user gets a unique 8-character referral code
- **Unique**: Codes are automatically generated and checked for uniqueness
- **Regeneratable**: Users can generate new codes if needed

### 📊 **Referral Tracking**
- **Referrer Stats**: Track how many users you've referred
- **Earnings**: Track total amount earned from referrals
- **Referral List**: See all users you've referred with join dates

### 💰 **Reward System**
- **Per Referral**: 4500 earned for each successful referral
- **Eligibility**: Users can refer others after their first referral
- **Leaderboard**: Top referrers are displayed on a leaderboard

## API Endpoints

### 1. **Get User Referral Stats**
```http
GET /referral/stats/{user_id}
```
**Response:**
```json
{
  "success": true,
  "stats": {
    "referral_code": "ABC12345",
    "referred_users": 5,
    "referred_amount": 5000,
    "can_refer": true
  }
}
```

### 2. **Validate Referral Code**
```http
GET /referral/validate/{referral_code}
```
**Response:**
```json
{
  "success": true,
  "valid": true,
  "referrer": {
    "id": "user-uuid",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### 3. **Get User Referrals**
```http
GET /referral/referrals/{user_id}
```
**Response:**
```json
{
  "success": true,
  "referrals": [
    {
      "id": "user-uuid",
      "username": "jane_doe",
      "email": "jane@example.com",
      "joined_date": "2024-01-15T10:30:00Z"
    }
  ],
  "total_referrals": 1
}
```

### 4. **Get Referral Leaderboard**
```http
GET /referral/leaderboard
```
**Response:**
```json
{
  "success": true,
  "leaderboard": [
    {
      "rank": 1,
      "username": "top_referrer",
      "referred_users": 25,
      "referred_amount": 25000
    }
  ]
}
```

### 5. **Regenerate Referral Code**
```http
POST /referral/generate-code/{user_id}
```
**Response:**
```json
{
  "success": true,
  "new_referral_code": "XYZ98765"
}
```

## Frontend Integration

### **Registration Form**
The registration form now includes an optional referral code field:
```html
<div>
  <label>Referral Code (Optional)</label>
  <input type="text" name="referralCode" placeholder="Enter referral code if you have one" />
</div>
```

### **Dashboard Referral Section**
Users can see their referral information on the dashboard:
- **Referral Code**: Displayed prominently with copy functionality
- **Referral Stats**: Shows users referred and total earnings
- **Referral List**: Displays all users they've referred

### **Copy Referral Code**
Users can easily copy their referral code to share with others:
```javascript
// Copy to clipboard functionality
const copyBtn = root.querySelector('#copyReferralCode');
copyBtn.addEventListener('click', async () => {
  const code = root.querySelector('#referralCode code');
  if (code) {
    await navigator.clipboard.writeText(code.textContent);
    UI.toast('Referral code copied!');
  }
});
```

## Database Schema

### **Users Table Updates**
```sql
-- Referral-related columns added to users table
ALTER TABLE users ADD COLUMN referral_code TEXT UNIQUE;
ALTER TABLE users ADD COLUMN referred_by TEXT;
ALTER TABLE users ADD COLUMN referred_users INT DEFAULT 0;
ALTER TABLE users ADD COLUMN referred_amount INT DEFAULT 0;
ALTER TABLE users ADD COLUMN can_refer BOOLEAN DEFAULT FALSE;
```

### **Referral Flow**
1. **User Registration**: New user provides referral code (optional)
2. **Code Validation**: System validates the referral code
3. **User Creation**: User is created with referral tracking
4. **Referral Processing**: Referrer's stats are updated
5. **Code Generation**: New user gets their own referral code

## Usage Examples

### **Sharing Referral Code**
1. User goes to dashboard
2. Copies their referral code
3. Shares code with friends via social media, email, etc.
4. Friends use code during registration

### **Tracking Referrals**
1. User can see how many people they've referred
2. View total earnings from referrals
3. See list of referred users with join dates
4. Check if they're eligible to refer more users

### **Referral Rewards**
- **First Referral**: ₦1,000 earned
- **Subsequent Referrals**: ₦1,000 each
- **Eligibility**: Users can refer after their first successful referral

## Security Features

### **Code Validation**
- Referral codes are validated before processing
- Invalid codes return appropriate error messages
- Codes are unique across all users

### **Referral Processing**
- Referral processing is wrapped in database transactions
- Error handling prevents partial updates
- Logging tracks all referral activities

## Future Enhancements

### **Planned Features**
- **Referral Tiers**: Multi-level referral rewards
- **Referral Analytics**: Detailed performance metrics
- **Referral Campaigns**: Time-limited bonus rewards
- **Social Sharing**: Direct social media integration
- **Referral Notifications**: Email/SMS notifications for successful referrals

### **Advanced Analytics**
- **Conversion Tracking**: Track referral-to-customer conversion
- **Geographic Data**: Location-based referral insights
- **Time Analysis**: Best times for referral sharing
- **Channel Performance**: Which sharing methods work best

## Troubleshooting

### **Common Issues**
1. **Invalid Referral Code**: Check if code exists and is active
2. **Referral Not Processing**: Verify database connection and permissions
3. **Stats Not Updating**: Check for database transaction errors

### **Debug Information**
- All referral operations are logged
- Database errors include detailed error messages
- Frontend shows appropriate error messages to users

## Testing

### **Test Scenarios**
1. **Valid Referral**: User registers with valid referral code
2. **Invalid Referral**: User registers with invalid referral code
3. **No Referral**: User registers without referral code
4. **Referral Stats**: Verify stats update correctly
5. **Code Generation**: Ensure unique codes are generated

### **Test Data**
```sql
-- Insert test referral data
INSERT INTO users (userId, username, email, referral_code) 
VALUES ('test-uuid', 'test_user', 'test@example.com', 'TEST1234');
```

This referral system provides a complete solution for user acquisition and engagement, with robust tracking, rewards, and user experience features.
