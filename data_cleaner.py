"""
Free AugmentCode Data Cleaner - Main Data Cleaner
Coordinates all cleaning operations and provides the main API.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading
import time

from utils import OSDetector, PathFinder, FileSearcher, Logger, IDEDetector
from backup_manager import BackupManager
from config_manager import ConfigManager
from database_cleaner import DatabaseCleaner
from telemetry_manager import TelemetryManager
from workspace_cleaner import WorkspaceCleaner
from account_cleaner import AccountDataCleaner
from ide_manager import AugmentCodeIDEManager


class DataCleanerStatus:
    """Status tracking for data cleaning operations."""
    
    def __init__(self):
        self.current_operation = ""
        self.progress = 0.0
        self.total_steps = 0
        self.completed_steps = 0
        self.is_running = False
        self.success = True
        self.error_message = ""
        self.detailed_log = []
    
    def update(self, operation: str, progress: float = None, step_completed: bool = False):
        """Update the status."""
        self.current_operation = operation
        if progress is not None:
            self.progress = progress
        if step_completed:
            self.completed_steps += 1
            if self.total_steps > 0:
                self.progress = self.completed_steps / self.total_steps
        
        self.detailed_log.append(f"{time.strftime('%H:%M:%S')} - {operation}")
    
    def set_error(self, error_message: str):
        """Set error status."""
        self.success = False
        self.error_message = error_message
        self.detailed_log.append(f"{time.strftime('%H:%M:%S')} - ERROR: {error_message}")


class FreeAugmentCodeCleaner:
    """Main data cleaner class that coordinates all operations."""
    
    def __init__(self, custom_backup_path: Optional[Path] = None):
        """Initialize the data cleaner."""
        self.logger = Logger.setup_logging()
        self.logger.info("Initializing Free AugmentCode Data Cleaner")
        
        # Initialize managers
        self.backup_manager = BackupManager(custom_backup_path)
        self.config_manager = ConfigManager()
        self.database_cleaner = DatabaseCleaner(self.backup_manager)
        self.telemetry_manager = TelemetryManager(self.backup_manager)
        self.workspace_cleaner = WorkspaceCleaner(self.backup_manager)
        self.account_cleaner = AccountDataCleaner(self.backup_manager)
        self.ide_manager = AugmentCodeIDEManager()
        
        # Discovery results
        self.augmentcode_paths = []
        self.telemetry_data = {}
        self.database_files = []
        self.workspace_locations = []
        self.account_data = {}
        
        # Status tracking
        self.status = DataCleanerStatus()
        
        self.logger.info("Data cleaner initialized successfully")
    
    def discover_augmentcode_data(self, custom_paths: Optional[List[Path]] = None) -> Dict[str, Any]:
        """Discover all AugmentCode data locations."""
        self.status.update("Starting AugmentCode data discovery...")
        self.status.total_steps = 7  # Added IDE scanning step
        self.status.completed_steps = 0

        discovery_results = {
            'augmentcode_paths': [],
            'telemetry_data': {},
            'database_files': [],
            'workspace_locations': [],
            'account_data': {},
            'ide_scan_results': {},
            'total_locations_found': 0
        }
        
        try:
            # Step 1: Find AugmentCode directories
            self.status.update("Searching for AugmentCode directories...")
            if custom_paths:
                self.augmentcode_paths = custom_paths
            else:
                app_data_paths = PathFinder.get_app_data_paths()
                self.augmentcode_paths = FileSearcher.find_augmentcode_directories(app_data_paths)
            
            discovery_results['augmentcode_paths'] = self.augmentcode_paths
            self.status.update("Found AugmentCode directories", step_completed=True)
            
            # Step 2: Discover telemetry data
            self.status.update("Discovering telemetry data...")
            self.telemetry_data = self.telemetry_manager.discover_telemetry_data(self.augmentcode_paths)
            discovery_results['telemetry_data'] = self.telemetry_data
            self.status.update("Telemetry data discovery complete", step_completed=True)
            
            # Step 3: Find database files
            self.status.update("Searching for database files...")
            self.database_files = []
            for path in self.augmentcode_paths:
                db_files = FileSearcher.find_database_files(path)
                self.database_files.extend(db_files)
            discovery_results['database_files'] = self.database_files
            self.status.update("Database file search complete", step_completed=True)
            
            # Step 4: Discover workspace locations
            self.status.update("Discovering workspace locations...")
            self.workspace_locations = self.workspace_cleaner.discover_workspace_locations(self.augmentcode_paths)
            discovery_results['workspace_locations'] = self.workspace_locations
            self.status.update("Workspace discovery complete", step_completed=True)

            # Step 5: Discover account data
            self.status.update("Discovering account data...")
            self.account_data = self.account_cleaner.discover_account_data(self.augmentcode_paths)
            discovery_results['account_data'] = self.account_data
            self.status.update("Account data discovery complete", step_completed=True)

            # Step 6: Perform comprehensive IDE scan
            self.status.update("Scanning IDEs for AugmentCode installations...")
            ide_scan_results = self.ide_manager.perform_comprehensive_scan()
            discovery_results['ide_scan_results'] = ide_scan_results
            self.status.update("IDE scan complete", step_completed=True)

            # Step 7: Calculate totals
            self.status.update("Finalizing discovery results...")
            total_locations = (
                len(self.augmentcode_paths) +
                len(self.database_files) +
                len(self.workspace_locations) +
                len(self.telemetry_data.get('found_ids', [])) +
                len(self.account_data.get('email_addresses', [])) +
                len(self.account_data.get('account_files', []))
            )
            discovery_results['total_locations_found'] = total_locations
            self.status.update("Discovery complete", step_completed=True)
            
            self.logger.info(f"Discovery complete: {total_locations} total locations found")
            
        except Exception as e:
            error_msg = f"Error during discovery: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_error(error_msg)
        
        return discovery_results
    
    def perform_cleanup(self, cleanup_options: Dict[str, Any]) -> bool:
        """Perform the actual data cleanup based on options."""
        self.status.update("Starting data cleanup...")
        self.status.is_running = True
        
        # Calculate total steps
        total_steps = 1  # Backup creation
        if cleanup_options.get('modify_telemetry_ids', False):
            total_steps += 1
        if cleanup_options.get('clean_database', False):
            total_steps += len(self.database_files)
        if cleanup_options.get('clean_workspace', False):
            total_steps += len(self.workspace_locations)
        if cleanup_options.get('clean_account_data', False):
            total_steps += 1
        
        self.status.total_steps = total_steps
        self.status.completed_steps = 0
        
        try:
            # Create backup directory
            self.status.update("Creating backup directory...")
            backup_dir = self.backup_manager.create_timestamped_backup_dir()
            self.status.update("Backup directory created", step_completed=True)
            
            success = True
            
            # Modify telemetry IDs
            if cleanup_options.get('modify_telemetry_ids', False):
                self.status.update("Modifying telemetry IDs...")
                telemetry_success = self.telemetry_manager.modify_telemetry_ids(
                    backup_dir, 
                    {
                        'found_ids': self.telemetry_data.get('found_ids', []),
                        'registry_keys': self.telemetry_data.get('registry_keys', []),
                        'modify_config_files': cleanup_options.get('modify_config_files', True),
                        'modify_registry': cleanup_options.get('modify_registry', True)
                    }
                )
                success &= telemetry_success
                self.status.update("Telemetry ID modification complete", step_completed=True)
            
            # Clean databases
            if cleanup_options.get('clean_database', False):
                for db_file in self.database_files:
                    self.status.update(f"Cleaning database: {db_file.name}")
                    db_success = self.database_cleaner.clean_database(
                        db_file,
                        backup_dir,
                        {
                            'remove_augment_records': cleanup_options.get('remove_augment_records', True),
                            'remove_account_data': cleanup_options.get('remove_account_data', False),
                            'target_email': cleanup_options.get('target_email', ''),
                            'reset_telemetry_ids': cleanup_options.get('reset_db_telemetry_ids', False),
                            'clear_session_data': cleanup_options.get('clear_session_data', True)
                        }
                    )
                    success &= db_success
                    self.status.update(f"Database {db_file.name} cleaned", step_completed=True)
            
            # Clean workspaces
            if cleanup_options.get('clean_workspace', False):
                for workspace in self.workspace_locations:
                    workspace_name = workspace['name']
                    self.status.update(f"Cleaning workspace: {workspace_name}")
                    
                    workspace_success = self.workspace_cleaner.clean_workspace(
                        workspace,
                        backup_dir,
                        {
                            'backup_workspace': cleanup_options.get('backup_workspace', True),
                            'selected_items': cleanup_options.get('workspace_items_to_clean', ['cache_folder', 'temp_file']),
                            'clear_all_cache': cleanup_options.get('clear_all_cache', False),
                            'remove_lock_files': cleanup_options.get('remove_lock_files', True)
                        }
                    )
                    success &= workspace_success
                    self.status.update(f"Workspace {workspace_name} cleaned", step_completed=True)

            # Clean account data
            if cleanup_options.get('clean_account_data', False):
                self.status.update("Cleaning account data...")
                account_success = self.account_cleaner.clean_account_data(
                    backup_dir,
                    {
                        'target_email': cleanup_options.get('target_email', ''),
                        'remove_all_accounts': cleanup_options.get('remove_all_accounts', False),
                        'account_files': self.account_data.get('account_files', [])
                    }
                )
                success &= account_success
                self.status.update("Account data cleaning complete", step_completed=True)

            if success:
                self.status.update("Data cleanup completed successfully!")
                self.logger.info("Data cleanup completed successfully")
            else:
                self.status.update("Data cleanup completed with some errors")
                self.logger.warning("Data cleanup completed with some errors")
            
            self.status.is_running = False
            return success
            
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_error(error_msg)
            self.status.is_running = False
            return False
    
    def perform_cleanup_async(self, cleanup_options: Dict[str, Any]) -> threading.Thread:
        """Perform cleanup in a separate thread."""
        def cleanup_thread():
            self.perform_cleanup(cleanup_options)
        
        thread = threading.Thread(target=cleanup_thread, daemon=True)
        thread.start()
        return thread
    
    def generate_discovery_report(self) -> str:
        """Generate a comprehensive discovery report."""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("FREE AUGMENTCODE DATA CLEANER - DISCOVERY REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # System information
        report_lines.append(f"Operating System: {OSDetector.get_os_type().title()}")
        report_lines.append(f"Discovery Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # AugmentCode directories
        report_lines.append(f"AugmentCode Directories Found: {len(self.augmentcode_paths)}")
        for i, path in enumerate(self.augmentcode_paths, 1):
            report_lines.append(f"  {i}. {path}")
        report_lines.append("")
        
        # Telemetry data
        if self.telemetry_data:
            telemetry_report = self.telemetry_manager.generate_telemetry_report(self.telemetry_data)
            report_lines.append(telemetry_report)
            report_lines.append("")
        
        # Database files
        report_lines.append(f"Database Files Found: {len(self.database_files)}")
        for i, db_file in enumerate(self.database_files, 1):
            try:
                size = db_file.stat().st_size
                size_str = self._format_size(size)
                report_lines.append(f"  {i}. {db_file} ({size_str})")
            except OSError:
                report_lines.append(f"  {i}. {db_file} (size unknown)")
        report_lines.append("")
        
        # Workspace locations
        if self.workspace_locations:
            workspace_report = self.workspace_cleaner.generate_workspace_report(self.workspace_locations)
            report_lines.append(workspace_report)

        # Account data
        if self.account_data:
            account_report = self.account_cleaner.generate_account_report(self.account_data)
            report_lines.append(account_report)

        # IDE scan results
        ide_report = self.ide_manager.generate_detailed_report()
        if ide_report:
            report_lines.append("")
            report_lines.append(ide_report)

        return "\n".join(report_lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        return self.backup_manager.list_backups()
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """Restore data from a backup."""
        try:
            self.status.update("Restoring from backup...")
            success = self.backup_manager.restore_from_backup(backup_path)
            
            if success:
                self.status.update("Backup restoration completed successfully")
                self.logger.info("Backup restoration completed successfully")
            else:
                self.status.update("Backup restoration failed")
                self.logger.error("Backup restoration failed")
            
            return success
            
        except Exception as e:
            error_msg = f"Error during backup restoration: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_error(error_msg)
            return False

    def terminate_augmentcode_processes(self, force: bool = False) -> Dict[str, Any]:
        """Terminate running AugmentCode processes across all IDEs."""
        try:
            self.status.update("Terminating AugmentCode processes...")
            result = self.ide_manager.safe_terminate_processes(force=force)

            if result['status'] == 'success':
                self.status.update("All AugmentCode processes terminated successfully")
                self.logger.info("AugmentCode processes terminated successfully")
            else:
                self.status.update("Some AugmentCode processes could not be terminated")
                self.logger.warning("Some AugmentCode processes could not be terminated")

            return result

        except Exception as e:
            error_msg = f"Error terminating processes: {str(e)}"
            self.logger.error(error_msg)
            self.status.set_error(error_msg)
            return {'status': 'error', 'message': error_msg}

    def get_ide_scan_results(self) -> Dict[str, Any]:
        """Get the latest IDE scan results."""
        return getattr(self, 'ide_scan_results', {})

    def get_supported_ides(self) -> Dict[str, str]:
        """Get list of supported IDEs."""
        return self.ide_manager.get_supported_ides()
