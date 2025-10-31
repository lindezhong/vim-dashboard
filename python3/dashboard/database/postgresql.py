"""
PostgreSQL database connection implementation
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import SQLDatabaseConnection, DatabaseManager


class PostgreSQLConnection(SQLDatabaseConnection):
    """PostgreSQL database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 5432  # Default PostgreSQL port
    
    def connect(self) -> bool:
        """Establish PostgreSQL connection."""
        try:
            import psycopg2
            import psycopg2.extras
            
            self.connection = psycopg2.connect(
                host=self.hostname,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database
            )
            self.connection.autocommit = True
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("psycopg2 library is required for PostgreSQL connections. Install with: pip install psycopg2-binary")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    def disconnect(self):
        """Close PostgreSQL connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute PostgreSQL query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to PostgreSQL database")
        
        try:
            import psycopg2.extras
            
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert RealDictRow objects to regular dictionaries
                return [dict(row) for row in results]
                    
        except Exception as e:
            raise RuntimeError(self.format_sql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test PostgreSQL connection."""
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


# Register PostgreSQL connection class
DatabaseManager.register_connection_class('postgres', PostgreSQLConnection)
DatabaseManager.register_connection_class('postgresql', PostgreSQLConnection)