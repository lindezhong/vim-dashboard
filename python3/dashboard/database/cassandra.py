"""
Cassandra database connection implementation
"""

from typing import Dict, Any, List, Optional, Tuple
from .base import NoSQLDatabaseConnection, DatabaseManager


class CassandraConnection(NoSQLDatabaseConnection):
    """Cassandra database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 9042  # Default Cassandra port
        self.keyspace = self.database  # Cassandra uses keyspace instead of database
    
    def connect(self) -> bool:
        """Establish Cassandra connection."""
        try:
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider
            
            # Setup authentication if credentials provided
            auth_provider = None
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.username, 
                    password=self.password
                )
            
            # Create cluster connection
            self.cluster = Cluster(
                [self.hostname],
                port=self.port,
                auth_provider=auth_provider
            )
            
            self.connection = self.cluster.connect()
            
            # Set keyspace if provided
            if self.keyspace:
                self.connection.set_keyspace(self.keyspace)
            
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("cassandra-driver library is required for Cassandra connections. Install with: pip install cassandra-driver")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to Cassandra: {e}")
    
    def disconnect(self):
        """Close Cassandra connection."""
        if hasattr(self, 'connection') and self.connection:
            try:
                self.connection.shutdown()
            except Exception:
                pass
        
        if hasattr(self, 'cluster') and self.cluster:
            try:
                self.cluster.shutdown()
            except Exception:
                pass
            finally:
                self.cluster = None
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute Cassandra CQL query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to Cassandra database")
        
        try:
            # Execute CQL query
            result_set = self.connection.execute(query)
            
            # Convert results to list of dictionaries
            results = []
            for row in result_set:
                # Convert Row object to dictionary
                row_dict = {}
                for column_name in row._fields:
                    value = getattr(row, column_name)
                    # Convert UUID and other special types to string
                    if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                        value = str(value)
                    row_dict[column_name] = value
                results.append(row_dict)
            
            return results
                    
        except Exception as e:
            raise RuntimeError(self.format_nosql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test Cassandra connection."""
        try:
            if not self.is_connected:
                self.connect()
            
            # Simple test query
            result = self.connection.execute("SELECT release_version FROM system.local")
            return True, None
            
        except Exception as e:
            return False, str(e)


# Register Cassandra connection class
DatabaseManager.register_connection_class('cassandra', CassandraConnection)