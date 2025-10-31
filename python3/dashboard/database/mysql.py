"""
MySQL database connection implementation
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import SQLDatabaseConnection, DatabaseManager


class MySQLConnection(SQLDatabaseConnection):
    """MySQL database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 3306  # Default MySQL port
    
    def connect(self) -> bool:
        """Establish MySQL connection."""
        try:
            import pymysql
            
            self.connection = pymysql.connect(
                host=self.hostname,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("PyMySQL library is required for MySQL connections. Install with: pip install PyMySQL")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
    
    def disconnect(self):
        """Close MySQL connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute MySQL query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to MySQL database")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert results to list of dictionaries
                if isinstance(results, (list, tuple)):
                    return list(results)
                else:
                    return [results] if results else []
                    
        except Exception as e:
            raise RuntimeError(self.format_sql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MySQL connection."""
        try:
            if not self.is_connected:
                self.connect()
            
            # Simple test query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_column_names(self, query: str) -> List[str]:
        """Get column names from query results."""
        if not self.is_connected or not self.connection:
            return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    return [desc[0] for desc in cursor.description]
                return []
        except Exception:
            return []


# Register MySQL connection class
DatabaseManager.register_connection_class('mysql', MySQLConnection)