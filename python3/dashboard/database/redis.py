"""
Redis database connection implementation
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from .base import NoSQLDatabaseConnection, DatabaseManager


class RedisConnection(NoSQLDatabaseConnection):
    """Redis database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 6379  # Default Redis port
        self.db = int(self.params.get('db', 0)) if self.params else 0
    
    def connect(self) -> bool:
        """Establish Redis connection."""
        try:
            import redis
            
            self.connection = redis.Redis(
                host=self.hostname,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True
            )
            
            # Test connection
            self.connection.ping()
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("redis library is required for Redis connections. Install with: pip install redis")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    def disconnect(self):
        """Close Redis connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute Redis command and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to Redis database")
        
        try:
            # Parse Redis command
            parts = query.strip().split()
            if not parts:
                return []
            
            command = parts[0].upper()
            args = parts[1:] if len(parts) > 1 else []
            
            # Execute command
            if command == 'KEYS':
                pattern = args[0] if args else '*'
                keys = self.connection.keys(pattern)
                return [{'key': key} for key in keys]
            
            elif command == 'GET':
                if not args:
                    raise ValueError("GET command requires a key")
                value = self.connection.get(args[0])
                return [{'key': args[0], 'value': value}]
            
            elif command == 'HGETALL':
                if not args:
                    raise ValueError("HGETALL command requires a key")
                hash_data = self.connection.hgetall(args[0])
                return [{'field': k, 'value': v} for k, v in hash_data.items()]
            
            elif command == 'LRANGE':
                if len(args) < 3:
                    raise ValueError("LRANGE command requires key, start, and stop")
                key, start, stop = args[0], int(args[1]), int(args[2])
                items = self.connection.lrange(key, start, stop)
                return [{'index': i, 'value': item} for i, item in enumerate(items)]
            
            elif command == 'SMEMBERS':
                if not args:
                    raise ValueError("SMEMBERS command requires a key")
                members = self.connection.smembers(args[0])
                return [{'member': member} for member in members]
            
            else:
                # Generic command execution
                result = self.connection.execute_command(command, *args)
                if isinstance(result, (list, tuple)):
                    return [{'value': str(item)} for item in result]
                else:
                    return [{'result': str(result)}]
                    
        except Exception as e:
            raise RuntimeError(self.format_nosql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test Redis connection."""
        try:
            if not self.is_connected:
                self.connect()
            
            # Simple test command
            result = self.connection.ping()
            return True, None
            
        except Exception as e:
            return False, str(e)


# Register Redis connection class
DatabaseManager.register_connection_class('redis', RedisConnection)