"""
LemonSqueezy Payment Integration for ZED AI
Handles subscriptions, webhooks, and usage-based billing
"""

import os
import requests
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import get_db_connection

load_dotenv()

# LemonSqueezy Configuration
LEMONSQUEEZY_API_KEY = os.getenv('LEMONSQUEEZY_API_KEY')
LEMONSQUEEZY_STORE_ID = os.getenv('LEMONSQUEEZY_STORE_ID')
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv('LEMONSQUEEZY_WEBHOOK_SECRET')
LEMONSQUEEZY_PRO_VARIANT_ID = os.getenv('LEMONSQUEEZY_PRO_VARIANT_ID')

# Pricing Configuration
PRO_PLAN_PRICE = float(os.getenv('PRO_PLAN_PRICE', '9.99'))
PRO_PLAN_INCLUDED_REQUESTS = int(os.getenv('PRO_PLAN_INCLUDED_REQUESTS', '2000'))
OVERAGE_RATE_PER_REQUEST = float(os.getenv('OVERAGE_RATE_PER_REQUEST', '0.01'))
FREE_PLAN_MONTHLY_LIMIT = int(os.getenv('FREE_PLAN_MONTHLY_LIMIT', '50'))

# LemonSqueezy API Base URL
LEMONSQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1"

class LemonSqueezyService:
    """Service for handling LemonSqueezy operations"""
    
    def __init__(self):
        self.api_key = LEMONSQUEEZY_API_KEY
        self.headers = {
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def create_checkout(self, user_id, email, custom_data=None):
        """
        Create a LemonSqueezy checkout session for Pro subscription
        
        Args:
            user_id: User ID from database
            email: User's email address
            custom_data: Additional data to pass to webhook
        
        Returns:
            dict: Checkout URL and session data
        """
        url = f"{LEMONSQUEEZY_API_URL}/checkouts"
        
        checkout_data = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": email,
                        "custom": {
                            "user_id": str(user_id),
                            **(custom_data or {})
                        }
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": LEMONSQUEEZY_STORE_ID
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": LEMONSQUEEZY_PRO_VARIANT_ID
                        }
                    }
                }
            }
        }
        
        try:
            response = requests.post(url, json=checkout_data, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            checkout_url = data['data']['attributes']['url']
            return {
                'success': True,
                'checkout_url': checkout_url,
                'checkout_id': data['data']['id']
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription(self, subscription_id):
        """Get subscription details from LemonSqueezy"""
        url = f"{LEMONSQUEEZY_API_URL}/subscriptions/{subscription_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id):
        """Cancel a subscription"""
        url = f"{LEMONSQUEEZY_API_URL}/subscriptions/{subscription_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return {'success': True}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_customer_portal_url(self, customer_id):
        """Get customer portal URL for subscription management"""
        url = f"{LEMONSQUEEZY_API_URL}/customers/{customer_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data['data']['attributes']['urls']['customer_portal']
        except requests.exceptions.RequestException as e:
            print(f"Error getting portal URL: {e}")
            return None
    
    def verify_webhook_signature(self, payload, signature):
        """Verify LemonSqueezy webhook signature"""
        expected_signature = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def process_webhook_event(self, event_data):
        """
        Process LemonSqueezy webhook events
        
        Event types:
        - subscription_created
        - subscription_updated
        - subscription_cancelled
        - subscription_resumed
        - subscription_expired
        - subscription_paused
        - subscription_unpaused
        - subscription_payment_success
        - subscription_payment_failed
        """
        event_type = event_data.get('meta', {}).get('event_name')
        # LemonSqueezy sends `webhook_id` (not `event_id`). Use it as our event identifier.
        event_id = event_data.get('meta', {}).get('event_id') or event_data.get('meta', {}).get('webhook_id')
        subscription_data = event_data.get('data', {})
        attributes = subscription_data.get('attributes', {})
        
        # Extract user_id from multiple possible locations
        user_id = None
        
        # Try 1: From custom_data in attributes
        custom_data = attributes.get('custom_data', {})
        if custom_data and isinstance(custom_data, dict):
            user_id = custom_data.get('user_id')
        
        # Try 2: From meta custom_data
        if not user_id:
            meta_custom = event_data.get('meta', {}).get('custom_data', {})
            if meta_custom and isinstance(meta_custom, dict):
                user_id = meta_custom.get('user_id')
        
        # Try 3: Find user by email
        if not user_id:
            user_email = attributes.get('user_email') or attributes.get('customer_email')
            if user_email:
                connection = get_db_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
                        user_data = cursor.fetchone()
                        if user_data:
                            user_id = user_data['id']
                finally:
                    connection.close()
        
        # Try 4: Find user by lemonsqueezy_customer_id
        if not user_id:
            customer_id = attributes.get('customer_id')
            if customer_id:
                connection = get_db_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT id FROM users WHERE lemonsqueezy_customer_id = %s", (customer_id,))
                        user_data = cursor.fetchone()
                        if user_data:
                            user_id = user_data['id']
                finally:
                    connection.close()
        
        if not user_id:
            error_msg = f"Could not find user_id. Email: {attributes.get('user_email')}, Customer ID: {attributes.get('customer_id')}"
            print(error_msg)
            return {'success': False, 'error': 'Missing user_id'}
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Log the webhook event
                # Ensure lemonsqueezy_event_id is not NULL to satisfy DB constraint
                cursor.execute("""
                    INSERT INTO subscription_events 
                    (user_id, event_type, subscription_id, lemonsqueezy_event_id, payload, processed)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    event_type,
                    subscription_data.get('id'),
                    event_id,
                    json.dumps(event_data),
                    False
                ))
                
                # Process based on event type
                if event_type == 'subscription_created':
                    self._handle_subscription_created(cursor, user_id, attributes)
                elif event_type == 'subscription_updated':
                    self._handle_subscription_updated(cursor, user_id, attributes)
                elif event_type in ['subscription_cancelled', 'subscription_expired']:
                    self._handle_subscription_cancelled(cursor, user_id, attributes)
                elif event_type == 'subscription_resumed':
                    self._handle_subscription_resumed(cursor, user_id, attributes)
                elif event_type == 'subscription_payment_success':
                    self._handle_payment_success(cursor, user_id, attributes)
                elif event_type == 'subscription_payment_failed':
                    self._handle_payment_failed(cursor, user_id, attributes)
                
                # Mark event as processed
                cursor.execute("""
                    UPDATE subscription_events 
                    SET processed = TRUE 
                    WHERE lemonsqueezy_event_id = %s
                """, (event_id,))
                
            connection.commit()
            return {'success': True}
        except Exception as e:
            connection.rollback()
            print(f"Error processing webhook: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            connection.close()
    
    def _handle_subscription_created(self, cursor, user_id, attributes):
        """Handle new subscription creation"""
        def _to_mysql_datetime(value):
            if not value:
                return None
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'pro',
                subscription_id = %s,
                lemonsqueezy_customer_id = %s,
                plan_name = 'Pro',
                subscription_start_date = %s,
                current_period_start = %s,
                current_period_end = %s,
                monthly_quota = %s,
                requests_used = 0,
                last_quota_reset = %s
            WHERE id = %s
        """, (
            attributes.get('subscription_id'),
            attributes.get('customer_id'),
            _to_mysql_datetime(attributes.get('created_at')),
            _to_mysql_datetime(attributes.get('renews_at')),
            _to_mysql_datetime(attributes.get('ends_at')),
            PRO_PLAN_INCLUDED_REQUESTS,
            datetime.now(),
            user_id
        ))
    
    def _handle_subscription_updated(self, cursor, user_id, attributes):
        """Handle subscription updates"""
        status_map = {
            'active': 'pro',
            'cancelled': 'cancelled',
            'expired': 'free',
            'past_due': 'past_due',
            'paused': 'cancelled'
        }
        
        status = status_map.get(attributes.get('status'), 'free')
        def _to_mysql_datetime(value):
            if not value:
                return None
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
        
        cursor.execute("""
            UPDATE users 
            SET subscription_status = %s,
                current_period_start = %s,
                current_period_end = %s
            WHERE id = %s
        """, (
            status,
            _to_mysql_datetime(attributes.get('renews_at')),
            _to_mysql_datetime(attributes.get('ends_at')),
            user_id
        ))
    
    def _handle_subscription_cancelled(self, cursor, user_id, attributes):
        """Handle subscription cancellation"""
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'cancelled',
                subscription_end_date = %s
            WHERE id = %s
        """, (attributes.get('ends_at'), user_id))
    
    def _handle_subscription_resumed(self, cursor, user_id, attributes):
        """Handle subscription resumption"""
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'pro',
                subscription_end_date = NULL
            WHERE id = %s
        """, (user_id,))
    
    def _handle_payment_success(self, cursor, user_id, attributes):
        """Handle successful payment - reset quota"""
        def _to_mysql_datetime(value):
            if not value:
                return None
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
        cursor.execute("""
            UPDATE users 
            SET requests_used = 0,
                last_quota_reset = %s,
                current_period_start = %s,
                current_period_end = %s
            WHERE id = %s
        """, (datetime.now(), _to_mysql_datetime(attributes.get('renews_at')), _to_mysql_datetime(attributes.get('ends_at')), user_id))
    
    def _handle_payment_failed(self, cursor, user_id, attributes):
        """Handle failed payment"""
        cursor.execute("""
            UPDATE users 
            SET subscription_status = 'past_due'
            WHERE id = %s
        """, (user_id,))


class UsageTracker:
    """Track and manage user API usage"""
    
    @staticmethod
    def check_quota(user_id):
        """
        Check if user has available quota
        
        Returns:
            dict: {
                'allowed': bool,
                'remaining': int,
                'quota': int,
                'used': int,
                'is_overage': bool,
                'plan': str
            }
        """
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT subscription_status, monthly_quota, requests_used, 
                           overage_enabled, auto_stop_at_limit, plan_name
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    return {'allowed': False, 'error': 'User not found'}
                
                quota = user['monthly_quota']
                used = user['requests_used']
                remaining = max(0, quota - used)
                is_overage = used >= quota
                
                # Check if usage is allowed
                if is_overage:
                    if user['auto_stop_at_limit']:
                        return {
                            'allowed': False,
                            'remaining': 0,
                            'quota': quota,
                            'used': used,
                            'is_overage': True,
                            'plan': user['plan_name'],
                            'message': 'Monthly quota exceeded. Please upgrade or enable overage.'
                        }
                    elif not user['overage_enabled']:
                        return {
                            'allowed': False,
                            'remaining': 0,
                            'quota': quota,
                            'used': used,
                            'is_overage': True,
                            'plan': user['plan_name'],
                            'message': 'Monthly quota exceeded. Please upgrade your plan.'
                        }
                
                return {
                    'allowed': True,
                    'remaining': remaining,
                    'quota': quota,
                    'used': used,
                    'is_overage': is_overage,
                    'plan': user['plan_name']
                }
        finally:
            connection.close()
    
    @staticmethod
    def log_usage(user_id, action_type, tokens_used=1):
        """Log API usage and increment counter"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Get user's billing period
                cursor.execute("""
                    SELECT current_period_start, current_period_end, 
                           monthly_quota, requests_used
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Determine if this is overage
                is_overage = user['requests_used'] >= user['monthly_quota']
                
                # Log the usage
                cursor.execute("""
                    INSERT INTO usage_logs 
                    (user_id, action_type, tokens_used, billing_period_start, 
                     billing_period_end, is_overage)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    action_type,
                    tokens_used,
                    user['current_period_start'] or datetime.now(),
                    user['current_period_end'] or datetime.now() + timedelta(days=30),
                    is_overage
                ))
                
                # Increment user's request counter
                cursor.execute("""
                    UPDATE users 
                    SET requests_used = requests_used + 1
                    WHERE id = %s
                """, (user_id,))
                
            connection.commit()
            return {'success': True}
        except Exception as e:
            connection.rollback()
            print(f"Error logging usage: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            connection.close()
    
    @staticmethod
    def get_usage_stats(user_id):
        """Get detailed usage statistics for current billing period"""
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Get user info
                cursor.execute("""
                    SELECT subscription_status, plan_name, monthly_quota, 
                           requests_used, current_period_start, current_period_end,
                           overage_enabled, auto_stop_at_limit
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    return None
                
                # Get usage breakdown
                cursor.execute("""
                    SELECT action_type, COUNT(*) as count, SUM(tokens_used) as tokens
                    FROM usage_logs
                    WHERE user_id = %s 
                      AND billing_period_start = %s
                      AND billing_period_end = %s
                    GROUP BY action_type
                """, (user_id, user['current_period_start'], user['current_period_end']))
                
                breakdown = cursor.fetchall()
                
                # Calculate overage
                overage_requests = max(0, user['requests_used'] - user['monthly_quota'])
                overage_cost = overage_requests * OVERAGE_RATE_PER_REQUEST
                
                return {
                    'plan': user['plan_name'],
                    'status': user['subscription_status'],
                    'quota': user['monthly_quota'],
                    'used': user['requests_used'],
                    'remaining': max(0, user['monthly_quota'] - user['requests_used']),
                    'percentage': min(100, (user['requests_used'] / user['monthly_quota']) * 100),
                    'overage_requests': overage_requests,
                    'overage_cost': round(overage_cost, 2),
                    'estimated_bill': PRO_PLAN_PRICE + overage_cost if user['subscription_status'] == 'pro' else 0,
                    'period_start': user['current_period_start'],
                    'period_end': user['current_period_end'],
                    'breakdown': breakdown,
                    'overage_enabled': user['overage_enabled'],
                    'auto_stop_at_limit': user['auto_stop_at_limit']
                }
        finally:
            connection.close()
    
    @staticmethod
    def should_show_warning(user_id):
        """Check if overage warning should be shown"""
        threshold = float(os.getenv('OVERAGE_WARNING_THRESHOLD', '0.8'))
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT monthly_quota, requests_used
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                
                if not user:
                    return False
                
                usage_percentage = user['requests_used'] / user['monthly_quota']
                return usage_percentage >= threshold
        finally:
            connection.close()


# Helper functions for easy import
def create_checkout_session(user_id, email):
    """Quick function to create checkout"""
    service = LemonSqueezyService()
    return service.create_checkout(user_id, email)

def check_user_quota(user_id):
    """Quick function to check quota"""
    return UsageTracker.check_quota(user_id)

def log_api_usage(user_id, action_type):
    """Quick function to log usage"""
    return UsageTracker.log_usage(user_id, action_type)

def get_user_usage_stats(user_id):
    """Quick function to get stats"""
    return UsageTracker.get_usage_stats(user_id)
