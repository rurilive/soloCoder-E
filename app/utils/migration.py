import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import inspect, text, MetaData, Table, Column
from sqlalchemy.engine import Engine
from app.database import Base

logger = logging.getLogger(__name__)


class MigrationResult:
    def __init__(self):
        self.success = True
        self.messages: List[str] = []
        self.altered_tables: List[str] = []
        self.errors: List[str] = []
    
    def add_message(self, msg: str):
        self.messages.append(msg)
        logger.info(msg)
    
    def add_warning(self, msg: str):
        self.messages.append(f"WARNING: {msg}")
        logger.warning(msg)
    
    def add_error(self, msg: str):
        self.errors.append(msg)
        self.success = False
        logger.error(msg)
    
    def add_altered_table(self, table_name: str):
        self.altered_tables.append(table_name)


class DatabaseMigrator:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def get_column_type_sql(self, column: Column) -> str:
        column_type = str(column.type)
        
        if column_type.startswith("VARCHAR"):
            if column.type.length:
                column_type = f"VARCHAR({column.type.length})"
            else:
                column_type = "VARCHAR(255)"
        elif column_type.startswith("INTEGER"):
            column_type = "INTEGER"
        elif column_type.startswith("BOOLEAN"):
            column_type = "BOOLEAN"
        elif column_type.startswith("DATETIME"):
            column_type = "DATETIME"
        elif column_type.startswith("TEXT"):
            column_type = "TEXT"
        elif column_type.startswith("FLOAT"):
            column_type = "FLOAT"
        elif column_type.startswith("DATE"):
            column_type = "DATE"
        
        return column_type
    
    def get_column_default_sql(self, column: Column) -> Optional[str]:
        if column.default is None:
            return None
        
        default_arg = column.default.arg
        
        if hasattr(default_arg, '__call__'):
            return None
        
        if default_arg is None:
            return "NULL"
        
        if isinstance(default_arg, bool):
            return "1" if default_arg else "0"
        
        if isinstance(default_arg, (int, float)):
            return str(default_arg)
        
        if isinstance(default_arg, str):
            return f"'{default_arg}'"
        
        return None
    
    def generate_add_column_sql(self, table_name: str, column: Column) -> str:
        col_type = self.get_column_type_sql(column)
        
        sql_parts = [f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"]
        
        if not column.nullable and not column.primary_key:
            sql_parts.append("NOT NULL")
        
        default_sql = self.get_column_default_sql(column)
        if default_sql is not None:
            sql_parts.append(f"DEFAULT {default_sql}")
        
        return " ".join(sql_parts)
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        try:
            columns = self.inspector.get_columns(table_name)
            return any(col['name'] == column_name for col in columns)
        except Exception:
            return False
    
    def table_exists(self, table_name: str) -> bool:
        return table_name in self.inspector.get_table_names()
    
    def migrate_table(self, table_name: str, table: Table, result: MigrationResult):
        if not self.table_exists(table_name):
            result.add_message(f"Table '{table_name}' does not exist, will be created by create_all()")
            return
        
        result.add_message(f"Checking table: {table_name}")
        
        existing_columns = {col['name'] for col in self.inspector.get_columns(table_name)}
        columns_added = 0
        
        for column in table.columns:
            if column.primary_key:
                continue
            
            if column.name not in existing_columns:
                try:
                    sql = self.generate_add_column_sql(table_name, column)
                    
                    with self.engine.begin() as conn:
                        conn.execute(text(sql))
                    
                    result.add_message(f"  Added column: {table_name}.{column.name}")
                    columns_added += 1
                    
                except Exception as e:
                    result.add_error(f"  Failed to add column {table_name}.{column.name}: {str(e)}")
        
        if columns_added > 0:
            result.add_altered_table(table_name)
    
    def migrate(self) -> MigrationResult:
        result = MigrationResult()
        
        result.add_message(f"Starting database migration at {datetime.utcnow()}")
        
        try:
            existing_tables = set(self.inspector.get_table_names())
            
            if existing_tables:
                result.add_message(f"Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
            else:
                result.add_message("No existing tables found, will create all tables")
            
            for table_name, table in Base.metadata.tables.items():
                self.migrate_table(table_name, table, result)
            
            if result.altered_tables:
                result.add_message(f"Migration completed. Altered tables: {', '.join(result.altered_tables)}")
            else:
                result.add_message("Migration completed. No schema changes needed.")
            
        except Exception as e:
            result.add_error(f"Migration failed with exception: {str(e)}")
        
        return result


def run_migration(engine: Engine) -> MigrationResult:
    migrator = DatabaseMigrator(engine)
    return migrator.migrate()


def init_db_with_migration(engine: Engine):
    migration_result = run_migration(engine)
    
    Base.metadata.create_all(bind=engine)
    
    return migration_result
