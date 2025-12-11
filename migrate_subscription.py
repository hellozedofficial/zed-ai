"""
Database Migration Script for LemonSqueezy Subscription System
Run this to add subscription columns to existing users table
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', 3307)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'zed'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def migrate_database():
    """Add subscription columns to users table"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print("🔄 Starting database migration...")
            
            # Check if columns already exist
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'subscription_status'
            """, (os.getenv('DB_NAME', 'zed'),))
            
            if cursor.fetchone():
                print("⚠️  Subscription columns already exist. Skipping migration.")
                return
            
            # Add subscription columns
            print("📝 Adding subscription columns to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN subscription_status ENUM('free', 'pro', 'cancelled', 'past_due') DEFAULT 'free',
                ADD COLUMN subscription_id VARCHAR(255) NULL,
                ADD COLUMN lemonsqueezy_customer_id VARCHAR(255) NULL,
                ADD COLUMN plan_name VARCHAR(50) DEFAULT 'Free',
                ADD COLUMN subscription_start_date TIMESTAMP NULL,
                ADD COLUMN subscription_end_date TIMESTAMP NULL,
                ADD COLUMN current_period_start TIMESTAMP NULL,
                ADD COLUMN current_period_end TIMESTAMP NULL,
                ADD COLUMN monthly_quota INT DEFAULT 50,
                ADD COLUMN requests_used INT DEFAULT 0,
                ADD COLUMN last_quota_reset TIMESTAMP NULL,
                ADD COLUMN overage_enabled BOOLEAN DEFAULT TRUE,
                ADD COLUMN auto_stop_at_limit BOOLEAN DEFAULT FALSE,
                ADD INDEX idx_subscription_id (subscription_id),
                ADD INDEX idx_lemonsqueezy_customer_id (lemonsqueezy_customer_id)
            """)
            
            print("✅ Successfully added subscription columns")
            
            # Create usage_logs table
            print("📝 Creating usage_logs table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    action_type ENUM('summarize', 'ask', 'explain', 'autofill', 'chat') NOT NULL,
                    tokens_used INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    billing_period_start TIMESTAMP NOT NULL,
                    billing_period_end TIMESTAMP NOT NULL,
                    is_overage BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_billing_period (billing_period_start, billing_period_end)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            print("✅ Successfully created usage_logs table")
            
            # Create subscription_events table
            print("📝 Creating subscription_events table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_events (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    subscription_id VARCHAR(255) NOT NULL,
                    lemonsqueezy_event_id VARCHAR(255) UNIQUE NOT NULL,
                    payload JSON NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_subscription_id (subscription_id),
                    INDEX idx_event_type (event_type),
                    INDEX idx_processed (processed)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            print("✅ Successfully created subscription_events table")
            
        connection.commit()
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your .env file with LemonSqueezy credentials")
        print("2. Create a product in LemonSqueezy dashboard")
        print("3. Set up webhook endpoint: /api/webhooks/lemonsqueezy")
        print("4. Test the subscription flow")
        
    except Exception as e:
        connection.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        connection.close()

if __name__ == '__main__':
    print("=" * 60)
    print("  ZED AI - Subscription System Migration")
    print("=" * 60)
    print()
    
    migrate_database()
