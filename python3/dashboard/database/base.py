"""
Base database connection classes for vim-dashboard
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from ..utils import format_error_message


class DatabaseConnection(ABC):
    """Abstract base class for database connections."""
    
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.is_connected = False
        self._parse_url()
    
    def _parse_url(self):
        """Parse database URL and extract connection parameters."""
        parsed = urlparse(self.url)
        self.scheme = parsed.scheme
        self.username = parsed.username
        self.password = parsed.password
        self.hostname = parsed.hostname
        self.port = parsed.port
        self.database = parsed.path.lstrip('/') if parsed.path else None
        self.params = dict(param.split('=') for param in parsed.query.split('&') if '=' in param) if parsed.query else {}
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test database connection."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class SQLDatabaseConnection(DatabaseConnection):
    """Base class for SQL databases."""
    
    def get_column_names(self, query: str) -> List[str]:
        """Extract column names from query results."""
        # This will be implemented by subclasses based on their cursor capabilities
        return []
    
    def format_sql_error(self, error: Exception) -> str:
        """Format SQL error message."""
        return format_error_message(error, "SQL")


class NoSQLDatabaseConnection(DatabaseConnection):
    """Base class for NoSQL databases."""
    
    def format_nosql_error(self, error: Exception) -> str:
        """Format NoSQL error message."""
        return format_error_message(error, "NoSQL")


class DatabaseManager:
    """Factory class for creating database connections."""
    
    # Registry of database connection classes
    _connection_classes = {}
    
    @classmethod
    def register_connection_class(cls, scheme: str, connection_class: type):
        """Register a database connection class for a URL scheme."""
        cls._connection_classes[scheme] = connection_class
    
    @classmethod
    def create_connection(cls, url: str) -> DatabaseConnection:
        """Create appropriate database connection based on URL scheme."""
        scheme = cls._extract_scheme(url)
        
        if scheme not in cls._connection_classes:
            raise ValueError(f"Unsupported database type: {scheme}")
        
        connection_class = cls._connection_classes[scheme]
        return connection_class(url)
    
    @classmethod
    def _extract_scheme(cls, url: str) -> str:
        """Extract scheme from database URL."""
        if '://' not in url:
            raise ValueError(f"Invalid database URL format: {url}")
        
        return url.split('://')[0].lower()
    
    @classmethod
    def get_supported_databases(cls) -> List[str]:
        """Get list of supported database types."""
        return list(cls._connection_classes.keys())
    
    @classmethod
    def is_supported(cls, scheme: str) -> bool:
        """Check if database type is supported."""
        return scheme.lower() in cls._connection_classes


# Connection pool for reusing database connections
class ConnectionPool:
    """Simple connection pool for database connections."""
    
    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self._pools = {}  # url -> list of connections
        self._active_connections = {}  # url -> count
    
    def get_connection(self, url: str) -> DatabaseConnection:
        """Get connection from pool or create new one."""
        if url not in self._pools:
            self._pools[url] = []
            self._active_connections[url] = 0
        
        pool = self._pools[url]
        
        # Try to reuse existing connection
        for conn in pool:
            if not conn.is_connected:
                try:
                    if conn.connect():
                        self._active_connections[url] += 1
                        return conn
                except Exception:
                    # Connection failed, remove from pool
                    pool.remove(conn)
        
        # Create new connection if under limit
        if self._active_connections[url] < self.max_connections:
            try:
                conn = DatabaseManager.create_connection(url)
                if conn.connect():
                    pool.append(conn)
                    self._active_connections[url] += 1
                    return conn
            except Exception as e:
                raise ConnectionError(f"Failed to create database connection: {e}")
        
        raise ConnectionError(f"Connection pool limit reached for {url}")
    
    def return_connection(self, url: str, connection: DatabaseConnection):
        """Return connection to pool."""
        if url in self._active_connections:
            self._active_connections[url] = max(0, self._active_connections[url] - 1)
        
        # Keep connection alive for reuse
        # Connection will be closed when pool is cleaned up
    
    def close_all_connections(self, url: Optional[str] = None):
        """Close all connections for a URL or all URLs."""
        if url:
            if url in self._pools:
                for conn in self._pools[url]:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
                self._pools[url] = []
                self._active_connections[url] = 0
        else:
            for url in list(self._pools.keys()):
                self.close_all_connections(url)


# Global connection pool instance
connection_pool = ConnectionPool()