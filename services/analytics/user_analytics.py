"""
SKAILA User Analytics & Feature Usage Tracking
Task 8: User analytics and feature usage tracking system
"""

from datetime import datetime, timedelta
from database_manager import db_manager
from typing import Dict, List, Optional

class UserAnalytics:
    """Track user behavior and feature usage for insights"""
    
    def __init__(self):
        self.init_analytics_tables()
    
    def init_analytics_tables(self):
        """Initialize analytics tracking tables"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                is_postgres = db_manager.db_type == 'postgresql'
                timestamp_type = 'TIMESTAMP' if is_postgres else 'DATETIME'
                serial_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY AUTOINCREMENT'
                
                # Feature usage tracking
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS feature_usage (
                        id {serial_type},
                        user_id INTEGER NOT NULL,
                        scuola_id INTEGER NOT NULL,
                        feature_name VARCHAR(100) NOT NULL,
                        action VARCHAR(100),
                        metadata TEXT,
                        timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES utenti(id)
                    )
                ''')
                
                # Page views tracking
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS page_views (
                        id {serial_type},
                        user_id INTEGER,
                        scuola_id INTEGER,
                        page_path VARCHAR(255) NOT NULL,
                        referrer VARCHAR(255),
                        session_id VARCHAR(100),
                        timestamp {timestamp_type} DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User sessions tracking
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id {serial_type},
                        user_id INTEGER NOT NULL,
                        scuola_id INTEGER NOT NULL,
                        session_start {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                        session_end {timestamp_type},
                        duration_seconds INTEGER,
                        pages_viewed INTEGER DEFAULT 0,
                        actions_performed INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES utenti(id)
                    )
                ''')
                
                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_usage_user ON feature_usage(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON feature_usage(feature_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_usage_timestamp ON feature_usage(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_page_views_user ON page_views(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_page_views_page ON page_views(page_path)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)')
                
                conn.commit()
                print("✅ User analytics tables initialized")
        except Exception as e:
            print(f"⚠️ Analytics tables init warning: {e}")
    
    def track_feature_usage(self, user_id: int, scuola_id: int, feature_name: str, 
                           action: str = None, metadata: str = None):
        """Track when a user uses a specific feature"""
        try:
            db_manager.execute('''
                INSERT INTO feature_usage (user_id, scuola_id, feature_name, action, metadata)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, scuola_id, feature_name, action, metadata))
        except Exception as e:
            print(f"Analytics tracking error: {e}")
    
    def track_page_view(self, user_id: Optional[int], scuola_id: Optional[int], 
                       page_path: str, referrer: str = None, session_id: str = None):
        """Track page views"""
        try:
            db_manager.execute('''
                INSERT INTO page_views (user_id, scuola_id, page_path, referrer, session_id)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, scuola_id, page_path, referrer, session_id))
        except Exception as e:
            print(f"Page view tracking error: {e}")
    
    def get_feature_usage_stats(self, scuola_id: int, days: int = 30) -> List[Dict]:
        """Get feature usage statistics for a school"""
        since = datetime.now() - timedelta(days=days)
        
        results = db_manager.query('''
            SELECT 
                feature_name,
                COUNT(*) as usage_count,
                COUNT(DISTINCT user_id) as unique_users,
                MAX(timestamp) as last_used
            FROM feature_usage
            WHERE scuola_id = %s 
            AND timestamp >= %s
            GROUP BY feature_name
            ORDER BY usage_count DESC
        ''', (scuola_id, since))
        
        return results or []
    
    def get_most_active_users(self, scuola_id: int, limit: int = 10) -> List[Dict]:
        """Get most active users by feature usage"""
        results = db_manager.query('''
            SELECT 
                u.id,
                u.nome,
                u.cognome,
                u.ruolo,
                COUNT(f.id) as total_actions
            FROM utenti u
            LEFT JOIN feature_usage f ON u.id = f.user_id
            WHERE u.scuola_id = %s
            GROUP BY u.id, u.nome, u.cognome, u.ruolo
            ORDER BY total_actions DESC
            LIMIT %s
        ''', (scuola_id, limit))
        
        return results or []
    
    def get_user_activity_timeline(self, user_id: int, days: int = 7) -> List[Dict]:
        """Get user's activity timeline"""
        since = datetime.now() - timedelta(days=days)
        
        results = db_manager.query('''
            SELECT 
                feature_name,
                action,
                timestamp
            FROM feature_usage
            WHERE user_id = %s
            AND timestamp >= %s
            ORDER BY timestamp DESC
        ''', (user_id, since))
        
        return results or []

# Initialize analytics service
user_analytics = UserAnalytics()
print("✅ User Analytics Service initialized")
