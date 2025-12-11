# 🚀 ZED AI - LemonSqueezy Subscription Integration Guide

## 📋 Overview

ZED AI now includes a complete subscription and usage-based billing system powered by LemonSqueezy. This guide will help you set everything up.

## 💰 Pricing Model

### Free Plan
- **Price**: $0/month
- **Quota**: 50 requests per month
- **Features**: Basic AI features, Chrome extension access

### Pro Plan  
- **Base Price**: $9.99/month
- **Included Quota**: 2,000 requests
- **Overage**: $0.01 per additional request
- **Features**: Full AI access, priority speed, auto-fill, unlimited overage

## 🛠️ Setup Instructions

### 1. LemonSqueezy Account Setup

1. **Create Account**
   - Go to https://lemonsqueezy.com
   - Create an account and verify your email
   - Complete store setup

2. **Create Product**
   - Navigate to Products → New Product
   - Name: "ZED AI Pro"
   - Price: $9.99 (monthly recurring)
   - Save the product

3. **Get Variant ID**
   - Open the product you just created
   - Go to Variants tab
   - Copy the Variant ID (format: `12345`)

4. **Get API Key**
   - Go to Settings → API
   - Create a new API key
   - Copy the key (starts with `lmn_`)

5. **Get Store ID**
   - Go to Settings → Stores
   - Copy your Store ID

6. **Setup Webhook**
   - Go to Settings → Webhooks
   - Create new webhook
   - URL: `https://yourdomain.com/api/webhooks/lemonsqueezy`
   - Events: Select all subscription events
   - Copy the signing secret

### 2. Environment Configuration

Update your `.env` file with LemonSqueezy credentials:

```bash
# LemonSqueezy Configuration
LEMONSQUEEZY_API_KEY=lmn_your_api_key_here
LEMONSQUEEZY_STORE_ID=12345
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_here
LEMONSQUEEZY_PRO_VARIANT_ID=67890

# Pricing Configuration
PRO_PLAN_PRICE=9.99
PRO_PLAN_INCLUDED_REQUESTS=2000
OVERAGE_RATE_PER_REQUEST=0.01
FREE_PLAN_MONTHLY_LIMIT=50

# Billing Settings
ENABLE_USAGE_BILLING=true
BILLING_CYCLE_DAY=1
OVERAGE_WARNING_THRESHOLD=0.8
AUTO_STOP_AT_LIMIT=false
```

### 3. Database Migration

Run the migration script to add subscription tables:

```bash
python migrate_subscription.py
```

This will:
- Add subscription columns to `users` table
- Create `usage_logs` table for tracking
- Create `subscription_events` table for webhooks

### 4. Test the Integration

1. **Start the server**:
   ```bash
   python app.py
   ```

2. **Access pricing page**:
   - Navigate to `https://ai.hellozed.com/pricing`
   - Review the pricing plans

3. **Test subscription flow**:
   - Click "Upgrade to Pro"
   - Complete checkout on LemonSqueezy
   - Verify webhook receives payment

4. **Check usage tracking**:
   - Go to `https://ai.hellozed.com/billing`
   - Verify usage stats display correctly

## 🔌 API Endpoints

### Billing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/billing/pricing` | GET | Get pricing information |
| `/api/billing/checkout` | POST | Create checkout session |
| `/api/billing/portal` | GET | Get customer portal URL |
| `/api/billing/usage` | GET | Get usage statistics |
| `/api/billing/quota` | GET | Check current quota |
| `/api/billing/settings` | PUT | Update billing preferences |
| `/api/webhooks/lemonsqueezy` | POST | Handle LemonSqueezy webhooks |

### Usage Tracking

All AI requests automatically:
1. Check user quota before processing
2. Log usage to database
3. Increment request counter
4. Return updated quota info

## 🎨 Chrome Extension Integration

The extension now includes:

### Usage Bar
- Displays current plan and quota
- Visual progress bar
- Warning indicators at 80% and 100%
- Upgrade button for free users

### Quota Handling
- Shows error when quota exceeded
- Prompts to upgrade or manage billing
- Auto-refreshes usage after requests

### Update Extension

Reload the extension to apply changes:
1. Go to `chrome://extensions/`
2. Click reload on ZED AI Extension
3. Test quota display

## 📊 Features Implemented

### User Experience
✅ Usage bar in extension popup
✅ Real-time quota tracking  
✅ Overage warnings at 80% usage
✅ Quota exceeded error messages
✅ One-click upgrade to Pro
✅ Billing dashboard
✅ Pricing page with FAQ

### Backend
✅ Quota checking middleware
✅ Usage logging per request
✅ LemonSqueezy webhook handling
✅ Automatic subscription sync
✅ Overage calculation
✅ Usage breakdown by action type

### Security
✅ Webhook signature verification
✅ User-scoped quota checks
✅ Protected billing endpoints
✅ Secure API key storage

## 🧪 Testing Checklist

- [ ] Free user can make 50 requests
- [ ] Requests blocked after quota exceeded
- [ ] Upgrade flow works end-to-end
- [ ] Usage bar updates after requests
- [ ] Webhooks process correctly
- [ ] Billing dashboard displays stats
- [ ] Overage charges calculate correctly
- [ ] Settings (overage toggle) work
- [ ] Customer portal link works

## 🐛 Troubleshooting

### Webhook not receiving events
- Check webhook URL is publicly accessible
- Verify webhook secret matches .env
- Check LemonSqueezy webhook logs

### Usage not tracking
- Verify database migration ran successfully
- Check `usage_logs` table exists
- Verify user has `requests_used` column

### Checkout not working
- Verify API key has permission
- Check variant ID is correct
- Ensure store is active

### Quota not updating
- Check `log_api_usage()` is called after requests
- Verify `current_period_end` is set correctly
- Reset quota manually if needed

## 📈 Analytics & Monitoring

Track these metrics:

1. **User Metrics**
   - Free vs Pro users
   - Average requests per user
   - Conversion rate to Pro

2. **Revenue Metrics**
   - Monthly recurring revenue (MRR)
   - Overage revenue
   - Average revenue per user (ARPU)

3. **Usage Metrics**
   - Total requests per day
   - Action type breakdown
   - Peak usage times

Query examples:

```sql
-- Total revenue this month
SELECT 
  COUNT(*) * 9.99 as base_revenue,
  SUM((requests_used - monthly_quota) * 0.01) as overage_revenue
FROM users 
WHERE subscription_status = 'pro' 
  AND current_period_start >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Usage breakdown
SELECT 
  action_type, 
  COUNT(*) as requests,
  SUM(is_overage) as overage_requests
FROM usage_logs
WHERE billing_period_start >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY action_type;
```

## 🚀 Go Live Checklist

Before production:

- [ ] Update webhook URL to production domain
- [ ] Set `FLASK_DEBUG=False` in .env
- [ ] Use production database
- [ ] Set up monitoring/alerts
- [ ] Test all subscription flows
- [ ] Configure SSL for webhooks
- [ ] Set proper CORS origins
- [ ] Review rate limits
- [ ] Prepare customer support docs
- [ ] Set up revenue tracking

## 📞 Support

For issues or questions:
- Check LemonSqueezy documentation: https://docs.lemonsqueezy.com
- Review error logs in `usage_logs` table
- Check webhook event logs in `subscription_events` table

## 🎉 Success!

Your ZED AI subscription system is now ready! Users can:
- Start with free tier
- Upgrade to Pro seamlessly  
- Pay only for what they use
- Manage billing independently

**Revenue flows automatically, scaling with your user base!** 💰
