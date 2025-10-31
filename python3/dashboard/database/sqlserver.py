"""
SQL Server database connection implementation
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import SQLDatabaseConnection, DatabaseManager


class SQLServerConnection(SQLDatabaseConnection):
    """SQL Server database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 1433  # Default SQL Server port
    
    def connect(self) -> bool:
        """Establish SQL Server connection."""
        try:
            import pyodbc
            
            # Build connection string
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.hostname},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password}"
            )
            
            self.connection = pyodbc.connect(conn_str)
            self.connection.autocommit = True
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("pyodbc library is required for SQL Server connections. Install with: pip install pyodbc")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to SQL Server: {e}")
    
    def disconnect(self):
        """Close SQL Server connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL Server query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to SQL Server database")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        row_dict[columns[i]] = value
                results.append(row_dict)
            
            cursor.close()
            return results
                    
        except Exception as e:
            raise RuntimeError(self.format_sql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test SQL Server connection."""
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


# Register SQL Server connection class
DatabaseManager.register_connection_class('mssql', SQLServerConnection)