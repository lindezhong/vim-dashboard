"""
MongoDB database connection implementation
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from .base import NoSQLDatabaseConnection, DatabaseManager


class MongoDBConnection(NoSQLDatabaseConnection):
    """MongoDB database connection implementation."""
    
    def __init__(self, url: str):
        super().__init__(url)
        self.port = self.port or 27017  # Default MongoDB port
    
    def connect(self) -> bool:
        """Establish MongoDB connection."""
        try:
            import pymongo
            
            # Build connection string
            if self.username and self.password:
                conn_str = f"mongodb://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.database}"
            else:
                conn_str = f"mongodb://{self.hostname}:{self.port}/{self.database}"
            
            self.client = pymongo.MongoClient(conn_str)
            self.connection = self.client[self.database]
            
            # Test connection
            self.client.admin.command('ping')
            self.is_connected = True
            return True
            
        except ImportError:
            raise ImportError("pymongo library is required for MongoDB connections. Install with: pip install pymongo")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def disconnect(self):
        """Close MongoDB connection."""
        if hasattr(self, 'client') and self.client:
            try:
                self.client.close()
            except Exception:
                pass
            finally:
                self.client = None
                self.connection = None
                self.is_connected = False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute MongoDB query and return results."""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Not connected to MongoDB database")
        
        try:
            # Parse MongoDB query (simplified JSON format)
            # Expected format: {"collection": "name", "operation": "find", "filter": {...}, "limit": 100}
            query_obj = json.loads(query)
            
            collection_name = query_obj.get('collection')
            operation = query_obj.get('operation', 'find')
            filter_obj = query_obj.get('filter', {})
            limit = query_obj.get('limit', 1000)
            
            if not collection_name:
                raise ValueError("MongoDB query must specify 'collection'")
            
            collection = self.connection[collection_name]
            
            if operation == 'find':
                cursor = collection.find(filter_obj).limit(limit)
                results = []
                for doc in cursor:
                    # Convert ObjectId to string for JSON serialization
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                    results.append(doc)
                return results
            
            elif operation == 'aggregate':
                pipeline = query_obj.get('pipeline', [])
                cursor = collection.aggregate(pipeline)
                results = []
                for doc in cursor:
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                    results.append(doc)
                return results
            
            elif operation == 'count':
                count = collection.count_documents(filter_obj)
                return [{'count': count}]
            
            else:
                raise ValueError(f"Unsupported MongoDB operation: {operation}")
                    
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON query format: {e}")
        except Exception as e:
            raise RuntimeError(self.format_nosql_error(e))
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MongoDB connection."""
        try:
            if not self.is_connected:
                self.connect()
            
            # Simple test command
            result = self.client.admin.command('ping')
            return True, None
            
        except Exception as e:
            return False, str(e)


# Register MongoDB connection class
DatabaseManager.register_connection_class('mongodb', MongoDBConnection)