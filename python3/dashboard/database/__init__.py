"""
Database connection module for vim-dashboard
"""

from .base import DatabaseConnection, DatabaseManager
from .mysql import MySQLConnection
from .postgresql import PostgreSQLConnection
from .sqlite import SQLiteConnection
from .oracle import OracleConnection
from .sqlserver import SQLServerConnection
from .redis import RedisConnection
from .mongodb import MongoDBConnection
from .cassandra import CassandraConnection

# Register all database connection classes
DatabaseManager.register_connection_class('mysql', MySQLConnection)
DatabaseManager.register_connection_class('postgresql', PostgreSQLConnection)
DatabaseManager.register_connection_class('postgres', PostgreSQLConnection)  # Alternative name
DatabaseManager.register_connection_class('sqlite', SQLiteConnection)
DatabaseManager.register_connection_class('oracle', OracleConnection)
DatabaseManager.register_connection_class('mssql', SQLServerConnection)
DatabaseManager.register_connection_class('sqlserver', SQLServerConnection)  # Alternative name
DatabaseManager.register_connection_class('redis', RedisConnection)
DatabaseManager.register_connection_class('mongodb', MongoDBConnection)
DatabaseManager.register_connection_class('cassandra', CassandraConnection)

__all__ = [
    'DatabaseConnection',
    'DatabaseManager',
    'MySQLConnection',
    'PostgreSQLConnection', 
    'SQLiteConnection',
    'OracleConnection',
    'SQLServerConnection',
    'RedisConnection',
    'MongoDBConnection',
    'CassandraConnection'
]