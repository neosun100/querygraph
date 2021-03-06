from querygraph.utils import optional_import


try:
    from _sqlite import Sqlite
except ImportError:
    Sqlite = optional_import.NotInstalled(name='sqlite3')


try:
    from _postgres import Postgres
except ImportError:
    Postgres = optional_import.NotInstalled(name='psycopg2')


try:
    from _mysql import MySql
except ImportError:
    MySql = optional_import.NotInstalled(name='mysql-connector-python')


try:
    from _maria_db import MariaDb
except ImportError:
    MariaDb = optional_import.NotInstalled(name='mysql-connector-python')


try:
    from _mongo_db import MongoDb
except ImportError:
    MongoDb = optional_import.NotInstalled(name='pymongo')


try:
    from _elastic_search import ElasticSearch
except ImportError:
    ElasticSearch = optional_import.NotInstalled(name='elasticsearch')

try:
    from _cassandra import Cassandra
except ImportError:
    Cassandra = optional_import.NotInstalled(name='cassandra-driver')

try:
    from _influx_db import InfluxDb
except ImportError:
    InfluxDb = optional_import.NotInstalled(name='influxdb')

try:
    from _ms_sql import MsSql
except ImportError:
    MsSql = optional_import.NotInstalled(name='pymssql')

try:
    from _neo4j import Neo4j
except ImportError:
    Neo4j = optional_import.NotInstalled(name='py2neo')
