import pymysql
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

def generate_share_hash():
    """Generate a secure random hash for chat sharing"""
    return secrets.token_urlsafe(24)  # Generates 32 character URL-safe string

def get_db_connection():
    """Create and return a database connection"""
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

def init_database():
    """Initialize database tables"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    -- Subscription fields
                    subscription_status ENUM('free', 'pro', 'cancelled', 'past_due') DEFAULT 'free',
                    subscription_id VARCHAR(255) NULL,
                    lemonsqueezy_customer_id VARCHAR(255) NULL,
                    plan_name VARCHAR(50) DEFAULT 'Free',
                    subscription_start_date TIMESTAMP NULL,
                    subscription_end_date TIMESTAMP NULL,
                    current_period_start TIMESTAMP NULL,
                    current_period_end TIMESTAMP NULL,
                    monthly_quota INT DEFAULT 50,
                    requests_used INT DEFAULT 0,
                    last_quota_reset TIMESTAMP NULL,
                    overage_enabled BOOLEAN DEFAULT TRUE,
                    auto_stop_at_limit BOOLEAN DEFAULT FALSE,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_subscription_id (subscription_id),
                    INDEX idx_lemonsqueezy_customer_id (lemonsqueezy_customer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    share_hash VARCHAR(40) UNIQUE NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    model_id VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_share_hash (share_hash),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    role ENUM('user', 'assistant') NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    INDEX idx_session_id (session_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create usage_logs table for tracking API usage
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
            
            # Create subscription_events table for webhook tracking
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
            
        connection.commit()
        print("Database tables initialized successfully")
    except Exception as e:
        connection.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        connection.close()

if __name__ == '__main__':
    init_database()
