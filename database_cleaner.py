"""
Free AugmentCode Data Cleaner - Database Cleaner
Handles SQLite database operations for cleaning AugmentCode data.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

from backup_manager import BackupManager


class DatabaseCleaner:
    """Manages SQLite database cleaning operations."""
    
    def __init__(self, backup_manager: BackupManager):
        self.logger = logging.getLogger('FreeAugmentCode.DatabaseCleaner')
        self.backup_manager = backup_manager
    
    def analyze_database(self, db_path: Path) -> Dict[str, Any]:
        """Analyze a SQLite database to understand its structure."""
        if not db_path.exists():
            self.logger.error(f"Database file does not exist: {db_path}")
            return {}
        
        analysis = {
            'file_path': db_path,
            'file_size': db_path.stat().st_size,
            'tables': [],
            'potential_cleanup_targets': []
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                table_names = [row[0] for row in cursor.fetchall()]
                
                for table_name in table_names:
                    table_info = self._analyze_table(cursor, table_name)
                    analysis['tables'].append(table_info)
                    
                    # Check if this table might contain data we want to clean
                    if self._is_potential_cleanup_target(table_info):
                        analysis['potential_cleanup_targets'].append(table_info)
                
                self.logger.info(f"Analyzed database {db_path}: {len(table_names)} tables, "
                               f"{len(analysis['potential_cleanup_targets'])} potential cleanup targets")
        
        except sqlite3.Error as e:
            self.logger.error(f"Error analyzing database {db_path}: {e}")
        
        return analysis
    
    def _analyze_table(self, cursor: sqlite3.Cursor, table_name: str) -> Dict[str, Any]:
        """Analyze a single table structure and content."""
        table_info = {
            'name': table_name,
            'columns': [],
            'row_count': 0,
            'text_columns': [],
            'potential_id_columns': []
        }
        
        try:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            for col in columns:
                col_info = {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                table_info['columns'].append(col_info)
                
                # Track text columns for keyword searching
                if 'TEXT' in col[2].upper() or 'VARCHAR' in col[2].upper() or 'CHAR' in col[2].upper():
                    table_info['text_columns'].append(col[1])
                
                # Track potential ID columns
                if self._is_potential_id_column(col[1]):
                    table_info['potential_id_columns'].append(col[1])
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            table_info['row_count'] = cursor.fetchone()[0]
            
        except sqlite3.Error as e:
            self.logger.error(f"Error analyzing table {table_name}: {e}")
        
        return table_info
    
    def _is_potential_id_column(self, column_name: str) -> bool:
        """Check if a column name suggests it might contain IDs."""
        id_patterns = [
            r'.*id$', r'.*_id$', r'.*Id$',
            r'device.*', r'machine.*', r'client.*',
            r'telemetry.*', r'session.*', r'user.*',
            r'guid.*', r'uuid.*', r'unique.*'
        ]
        
        for pattern in id_patterns:
            if re.search(pattern, column_name, re.IGNORECASE):
                return True
        return False
    
    def _is_potential_cleanup_target(self, table_info: Dict[str, Any]) -> bool:
        """Determine if a table is a potential target for cleanup."""
        table_name = table_info['name'].lower()
        
        # Tables that commonly contain user/session data
        target_patterns = [
            'account', 'user', 'session', 'login', 'auth',
            'telemetry', 'analytics', 'log', 'history',
            'workspace', 'project', 'setting', 'preference'
        ]
        
        for pattern in target_patterns:
            if pattern in table_name:
                return True
        
        # Tables with potential ID columns
        if table_info['potential_id_columns']:
            return True
        
        # Tables with text columns (for keyword search)
        if table_info['text_columns'] and table_info['row_count'] > 0:
            return True
        
        return False
    
    def search_for_augment_records(self, db_path: Path, 
                                  tables_to_search: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for records containing 'augment' keyword in the database."""
        found_records = []
        
        if not db_path.exists():
            self.logger.error(f"Database file does not exist: {db_path}")
            return found_records
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get tables to search
                if tables_to_search is None:
                    analysis = self.analyze_database(db_path)
                    tables_to_search = [t['name'] for t in analysis['potential_cleanup_targets']]
                
                for table_name in tables_to_search:
                    table_records = self._search_table_for_keyword(cursor, table_name, 'augment')
                    found_records.extend(table_records)
                
                self.logger.info(f"Found {len(found_records)} records containing 'augment' keyword")
        
        except sqlite3.Error as e:
            self.logger.error(f"Error searching database {db_path}: {e}")
        
        return found_records
    
    def _search_table_for_keyword(self, cursor: sqlite3.Cursor, table_name: str, 
                                 keyword: str) -> List[Dict[str, Any]]:
        """Search a specific table for records containing a keyword."""
        found_records = []
        
        try:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            text_columns = [col[1] for col in columns if 'TEXT' in col[2].upper() or 
                           'VARCHAR' in col[2].upper() or 'CHAR' in col[2].upper()]
            
            if not text_columns:
                return found_records
            
            # Build WHERE clause for text columns
            where_conditions = []
            for col in text_columns:
                where_conditions.append(f"{col} LIKE ?")
            
            where_clause = " OR ".join(where_conditions)
            query = f"SELECT rowid, * FROM {table_name} WHERE {where_clause};"
            
            # Execute search
            search_params = [f'%{keyword}%'] * len(text_columns)
            cursor.execute(query, search_params)
            
            # Get column names for result mapping
            column_names = ['rowid'] + [col[1] for col in columns]
            
            for row in cursor.fetchall():
                record = {
                    'table': table_name,
                    'rowid': row[0],
                    'data': dict(zip(column_names[1:], row[1:])),
                    'matching_columns': []
                }
                
                # Identify which columns contain the keyword
                for i, col_name in enumerate(column_names[1:], 1):
                    if col_name in text_columns and row[i] and keyword.lower() in str(row[i]).lower():
                        record['matching_columns'].append(col_name)
                
                found_records.append(record)
        
        except sqlite3.Error as e:
            self.logger.error(f"Error searching table {table_name}: {e}")
        
        return found_records
    
    def clean_database(self, db_path: Path, backup_dir: Path, 
                      cleanup_options: Dict[str, Any]) -> bool:
        """Clean the database based on specified options."""
        if not db_path.exists():
            self.logger.error(f"Database file does not exist: {db_path}")
            return False
        
        # Backup database first
        if not self.backup_manager.backup_file(db_path, backup_dir, f"database/{db_path.name}"):
            self.logger.error("Failed to backup database before cleaning")
            return False
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                success = True
                
                # Remove records containing 'augment' keyword
                if cleanup_options.get('remove_augment_records', False):
                    success &= self._remove_augment_records(cursor, cleanup_options)
                
                # Remove specific account data
                if cleanup_options.get('remove_account_data', False):
                    success &= self._remove_account_data(cursor, cleanup_options)
                
                # Reset telemetry IDs in database
                if cleanup_options.get('reset_telemetry_ids', False):
                    success &= self._reset_database_telemetry_ids(cursor, cleanup_options)
                
                # Clear session data
                if cleanup_options.get('clear_session_data', False):
                    success &= self._clear_session_data(cursor, cleanup_options)
                
                if success:
                    # Vacuum database to reclaim space
                    cursor.execute("VACUUM;")
                    conn.commit()
                    self.logger.info("Database cleaning completed successfully")
                else:
                    self.logger.warning("Database cleaning completed with some errors")
                
                return success
        
        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning database {db_path}: {e}")
            return False
    
    def _remove_augment_records(self, cursor: sqlite3.Cursor, 
                               options: Dict[str, Any]) -> bool:
        """Remove records containing 'augment' keyword."""
        try:
            tables_to_clean = options.get('tables_to_clean', [])
            if not tables_to_clean:
                # Auto-detect tables
                analysis = self.analyze_database(Path(cursor.connection.execute("PRAGMA database_list").fetchone()[2]))
                tables_to_clean = [t['name'] for t in analysis['potential_cleanup_targets']]
            
            total_deleted = 0
            
            for table_name in tables_to_clean:
                deleted_count = self._delete_records_with_keyword(cursor, table_name, 'augment')
                total_deleted += deleted_count
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted {deleted_count} records from {table_name}")
            
            self.logger.info(f"Total records deleted: {total_deleted}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error removing augment records: {e}")
            return False
    
    def _delete_records_with_keyword(self, cursor: sqlite3.Cursor, 
                                   table_name: str, keyword: str) -> int:
        """Delete records containing a keyword from a specific table."""
        try:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            text_columns = [col[1] for col in columns if 'TEXT' in col[2].upper() or 
                           'VARCHAR' in col[2].upper() or 'CHAR' in col[2].upper()]
            
            if not text_columns:
                return 0
            
            # Build WHERE clause
            where_conditions = []
            for col in text_columns:
                where_conditions.append(f"{col} LIKE ?")
            
            where_clause = " OR ".join(where_conditions)
            delete_query = f"DELETE FROM {table_name} WHERE {where_clause};"
            
            # Execute deletion
            search_params = [f'%{keyword}%'] * len(text_columns)
            cursor.execute(delete_query, search_params)
            
            return cursor.rowcount
        
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting records from {table_name}: {e}")
            return 0
    
    def _remove_account_data(self, cursor: sqlite3.Cursor, options: Dict[str, Any]) -> bool:
        """Remove specific account data including emails and user identifiers."""
        try:
            total_deleted = 0

            # Get target email if specified
            target_email = options.get('target_email', '')

            # Common account-related table patterns
            account_table_patterns = [
                'account', 'user', 'profile', 'login', 'auth', 'credential',
                'identity', 'member', 'person', 'contact'
            ]

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [row[0] for row in cursor.fetchall()]

            # Find account-related tables
            account_tables = []
            for table in all_tables:
                table_lower = table.lower()
                for pattern in account_table_patterns:
                    if pattern in table_lower:
                        account_tables.append(table)
                        break

            # Remove data from account tables
            for table_name in account_tables:
                deleted_count = self._clean_account_table(cursor, table_name, target_email)
                total_deleted += deleted_count

                if deleted_count > 0:
                    self.logger.info(f"Deleted {deleted_count} account records from {table_name}")

            # Also clean email addresses from any table
            if target_email:
                email_deleted = self._remove_email_references(cursor, all_tables, target_email)
                total_deleted += email_deleted

            self.logger.info(f"Total account records deleted: {total_deleted}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing account data: {e}")
            return False

    def _clean_account_table(self, cursor: sqlite3.Cursor, table_name: str, target_email: str = '') -> int:
        """Clean account data from a specific table."""
        try:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [row[1] for row in cursor.fetchall()]

            # Find email and user identifier columns
            email_columns = []
            user_id_columns = []

            for col in columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in ['email', 'mail', 'e_mail']):
                    email_columns.append(col)
                elif any(pattern in col_lower for pattern in ['user', 'account', 'login', 'username']):
                    user_id_columns.append(col)

            deleted_count = 0

            if target_email and email_columns:
                # Remove specific email
                for email_col in email_columns:
                    cursor.execute(f"DELETE FROM {table_name} WHERE {email_col} = ?;", (target_email,))
                    deleted_count += cursor.rowcount
            else:
                # Remove all account data if no specific email
                cursor.execute(f"DELETE FROM {table_name};")
                deleted_count = cursor.rowcount

            return deleted_count

        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning account table {table_name}: {e}")
            return 0

    def _remove_email_references(self, cursor: sqlite3.Cursor, tables: List[str], email: str) -> int:
        """Remove email references from all tables."""
        total_deleted = 0

        for table_name in tables:
            try:
                # Get table structure
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [row[1] for row in cursor.fetchall()]

                # Find text columns that might contain emails
                text_columns = []
                for col in columns:
                    cursor.execute(f"SELECT {col} FROM {table_name} LIMIT 1;")
                    sample = cursor.fetchone()
                    if sample and isinstance(sample[0], str):
                        text_columns.append(col)

                # Remove records containing the email
                if text_columns:
                    where_conditions = [f"{col} LIKE ?" for col in text_columns]
                    where_clause = " OR ".join(where_conditions)
                    delete_query = f"DELETE FROM {table_name} WHERE {where_clause};"

                    search_params = [f'%{email}%'] * len(text_columns)
                    cursor.execute(delete_query, search_params)
                    total_deleted += cursor.rowcount

            except sqlite3.Error:
                # Skip tables that cause errors
                continue

        return total_deleted
    
    def _reset_database_telemetry_ids(self, cursor: sqlite3.Cursor, 
                                    options: Dict[str, Any]) -> bool:
        """Reset telemetry IDs stored in the database."""
        # This would be implemented based on the specific database schema
        # For now, it's a placeholder
        self.logger.info("Database telemetry ID reset not yet implemented")
        return True
    
    def _clear_session_data(self, cursor: sqlite3.Cursor, options: Dict[str, Any]) -> bool:
        """Clear session data from the database."""
        try:
            # Common session table names
            session_tables = ['sessions', 'session', 'user_sessions', 'login_sessions']
            
            deleted_count = 0
            for table_name in session_tables:
                try:
                    cursor.execute(f"DELETE FROM {table_name};")
                    deleted_count += cursor.rowcount
                    self.logger.info(f"Cleared {cursor.rowcount} records from {table_name}")
                except sqlite3.OperationalError:
                    # Table doesn't exist, continue
                    continue
            
            self.logger.info(f"Total session records cleared: {deleted_count}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error clearing session data: {e}")
            return False
