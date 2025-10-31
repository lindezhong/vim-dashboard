"""
SQLite database connection implementation
"""

import sqlite3
import threading
from typing import Dict, Any, List, Optional, Tuple
from .base import SQLDatabaseConnection, DatabaseManager


class SQLiteConnection(SQLDatabaseConnection):
    """SQLite database connection implementation with thread safety."""

    def __init__(self, url: str):
        super().__init__(url)
        # For SQLite, the database path is in the URL path
        if self.url.startswith('sqlite:///'):
            self.database_path = self.url[10:]  # Remove 'sqlite:///'
        else:
            raise ValueError("Invalid SQLite URL format. Expected: sqlite:///path/to/database.db")

        # Thread-local storage for connections
        self._local = threading.local()
        self._lock = threading.Lock()
    
    def _get_connection(self):
        """Get thread-local SQLite connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # Create new connection for this thread with thread safety enabled
            self._local.connection = sqlite3.connect(
                self.database_path,
                check_same_thread=False,  # Allow cross-thread usage
                timeout=30.0  # 30 second timeout
            )
            self._local.connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self._local.connection

    def connect(self) -> bool:
        """Establish SQLite connection."""
        try:
            with self._lock:
                # Test the connection
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.is_connected = True
                return True

        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to SQLite: {e}")

    def disconnect(self):
        """Close SQLite connection."""
        try:
            with self._lock:
                if hasattr(self._local, 'connection') and self._local.connection:
                    self._local.connection.close()
                    self._local.connection = None
        except Exception:
            pass
        finally:
            self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQLite query and return results."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
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
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()

                return True, None

        except Exception as e:
            return False, str(e)

    def get_column_names(self, query: str) -> List[str]:
        """Get column names from query results."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
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