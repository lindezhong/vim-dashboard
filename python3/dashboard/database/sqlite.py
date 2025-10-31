"""
SQLite database connection implementation
"""

import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from .base import SQLDatabaseConnection, DatabaseManager


class SQLiteConnection(SQLDatabaseConnection):
    """SQLite database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        # For SQLite, the database path is in the URL path
        if self.url.startswith('sqlite:///'):
            self.database_path = self.url[10:]  # Remove 'sqlite:///'
        else:
            raise ValueError("Invalid SQLite URL format. Expected: sqlite:///path/to/database.db")
    
    def connect(self) -> bool:
        """Establish SQLite connection."""
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            self.is_connected = True
            return True
            
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to SQLite: {e}")
    
    def disconnect(self):
        """Close SQLite connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQLite query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to SQLite database")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Fetch all results
            rows = cursor.fetchall()
            
            # Convert sqlite3.Row objects to dictionaries
            results = []
            for row in rows:
                results.append(dict(row))
            
            cursor.close()
            return results
                    
        except Exception as e:
            raise RuntimeError(self.format_sql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SQLite connection."""
        try:
            if not self.is_connected:
                self.connect()
            
            # Simple test query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_column_names(self, query: str) -> List[str]:
        """Get column names from query results."""
        if not self.is_connected or not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            if cursor.description:
                column_names = [desc[0] for desc in cursor.description]
                cursor.close()
                return column_names
            
            cursor.close()
            return []
        except Exception:
            return []


# Register SQLite connection class
DatabaseManager.register_connection_class('sqlite', SQLiteConnection)