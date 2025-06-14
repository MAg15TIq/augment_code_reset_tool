"""
Free AugmentCode Data Cleaner - Workspace Cleaner
Handles workspace storage management and cleanup operations.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from utils import OSDetector, FileSearcher, SafeFileOperations
from backup_manager import BackupManager


class WorkspaceCleaner:
    """Manages workspace storage cleanup operations."""
    
    def __init__(self, backup_manager: BackupManager):
        self.logger = logging.getLogger('FreeAugmentCode.WorkspaceCleaner')
        self.backup_manager = backup_manager
    
    def discover_workspace_locations(self, augmentcode_paths: List[Path]) -> List[Dict[str, Any]]:
        """Discover potential workspace locations."""
        workspace_locations = []
        
        # Common workspace directory names
        workspace_patterns = [
            'workspace', 'workspaces', 'projects', 'documents',
            'files', 'data', 'storage', 'user_data'
        ]
        
        # Search in AugmentCode directories
        for base_path in augmentcode_paths:
            if not base_path.exists():
                continue
            
            try:
                for item in base_path.rglob('*'):
                    if item.is_dir():
                        for pattern in workspace_patterns:
                            if pattern.lower() in item.name.lower():
                                workspace_info = self._analyze_workspace_directory(item)
                                if workspace_info:
                                    workspace_locations.append(workspace_info)
                                break
            except PermissionError:
                self.logger.warning(f"Permission denied accessing {base_path}")
                continue
        
        # Check common user directories
        user_workspace_paths = self._get_common_user_workspace_paths()
        for path in user_workspace_paths:
            if path.exists():
                workspace_info = self._analyze_workspace_directory(path)
                if workspace_info:
                    workspace_locations.append(workspace_info)
        
        # Check for workspace paths in configuration files
        config_workspace_paths = self._find_workspace_paths_in_configs(augmentcode_paths)
        for path in config_workspace_paths:
            if path.exists():
                workspace_info = self._analyze_workspace_directory(path)
                if workspace_info:
                    workspace_locations.append(workspace_info)
        
        # Remove duplicates
        unique_workspaces = []
        seen_paths = set()
        for workspace in workspace_locations:
            path_str = str(workspace['path'])
            if path_str not in seen_paths:
                seen_paths.add(path_str)
                unique_workspaces.append(workspace)
        
        self.logger.info(f"Discovered {len(unique_workspaces)} potential workspace locations")
        return unique_workspaces
    
    def _get_common_user_workspace_paths(self) -> List[Path]:
        """Get common user workspace directory paths."""
        paths = []
        home = Path.home()
        
        if OSDetector.is_windows():
            paths.extend([
                home / 'Documents' / 'AugmentCode',
                home / 'Documents' / 'AugmentCode Projects',
                home / 'Documents' / 'Augment Code',
                home / 'AppData' / 'Roaming' / 'AugmentCode' / 'Workspace',
                home / 'AppData' / 'Local' / 'AugmentCode' / 'Workspace',
            ])
        elif OSDetector.is_macos():
            paths.extend([
                home / 'Documents' / 'AugmentCode',
                home / 'Documents' / 'AugmentCode Projects',
                home / 'Library' / 'Application Support' / 'AugmentCode' / 'Workspace',
                home / '.augmentcode' / 'workspace',
            ])
        elif OSDetector.is_linux():
            paths.extend([
                home / 'Documents' / 'AugmentCode',
                home / 'augmentcode-workspace',
                home / '.augmentcode' / 'workspace',
                home / '.local' / 'share' / 'AugmentCode' / 'workspace',
            ])
        
        return paths
    
    def _find_workspace_paths_in_configs(self, augmentcode_paths: List[Path]) -> List[Path]:
        """Find workspace paths mentioned in configuration files."""
        workspace_paths = []
        
        for base_path in augmentcode_paths:
            config_files = FileSearcher.find_config_files(base_path)
            
            for config_file in config_files:
                try:
                    if config_file.suffix.lower() == '.json':
                        data = SafeFileOperations.safe_read_json(config_file)
                        if data:
                            paths = self._extract_paths_from_json(data)
                            workspace_paths.extend(paths)
                except Exception as e:
                    self.logger.error(f"Error reading config file {config_file}: {e}")
        
        return [Path(p) for p in workspace_paths if Path(p).exists()]
    
    def _extract_paths_from_json(self, data: Any, current_path: str = "") -> List[str]:
        """Extract file paths from JSON data."""
        paths = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self._looks_like_path(value):
                    if any(keyword in key.lower() for keyword in ['workspace', 'project', 'directory', 'path', 'folder']):
                        paths.append(value)
                elif isinstance(value, (dict, list)):
                    paths.extend(self._extract_paths_from_json(value, f"{current_path}.{key}"))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    paths.extend(self._extract_paths_from_json(item, f"{current_path}[{i}]"))
        
        return paths
    
    def _looks_like_path(self, value: str) -> bool:
        """Check if a string looks like a file path."""
        if len(value) < 3:
            return False
        
        # Check for common path patterns
        path_indicators = ['/', '\\', ':', 'C:', 'D:', '/home', '/Users', 'Documents', 'AppData']
        return any(indicator in value for indicator in path_indicators)
    
    def _analyze_workspace_directory(self, workspace_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a workspace directory to determine its contents and cleanable items."""
        if not workspace_path.exists() or not workspace_path.is_dir():
            return None
        
        workspace_info = {
            'path': workspace_path,
            'name': workspace_path.name,
            'total_size': 0,
            'file_count': 0,
            'cleanable_items': [],
            'project_folders': [],
            'cache_folders': [],
            'temp_files': [],
            'session_files': []
        }
        
        try:
            # Analyze directory contents
            for item in workspace_path.rglob('*'):
                if item.is_file():
                    workspace_info['file_count'] += 1
                    try:
                        workspace_info['total_size'] += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
                    
                    # Categorize files
                    self._categorize_workspace_item(item, workspace_info)
                elif item.is_dir():
                    self._categorize_workspace_directory(item, workspace_info)
        
        except PermissionError:
            self.logger.warning(f"Permission denied analyzing workspace: {workspace_path}")
            return None
        
        # Determine cleanable items
        workspace_info['cleanable_items'] = self._identify_cleanable_items(workspace_info)
        
        return workspace_info
    
    def _categorize_workspace_item(self, item_path: Path, workspace_info: Dict[str, Any]) -> None:
        """Categorize a workspace file item."""
        file_name = item_path.name.lower()
        file_suffix = item_path.suffix.lower()
        
        # Temporary files
        if (file_name.startswith('tmp') or file_name.startswith('temp') or 
            file_suffix in ['.tmp', '.temp', '.bak', '.backup']):
            workspace_info['temp_files'].append(item_path)
        
        # Session files
        elif ('session' in file_name or 'cache' in file_name or 
              file_suffix in ['.session', '.cache', '.lock']):
            workspace_info['session_files'].append(item_path)
    
    def _categorize_workspace_directory(self, dir_path: Path, workspace_info: Dict[str, Any]) -> None:
        """Categorize a workspace directory."""
        dir_name = dir_path.name.lower()
        
        # Cache directories
        if any(keyword in dir_name for keyword in ['cache', 'tmp', 'temp', '.cache', '__pycache__']):
            workspace_info['cache_folders'].append(dir_path)
        
        # Project directories (contain project files)
        elif self._looks_like_project_directory(dir_path):
            workspace_info['project_folders'].append(dir_path)
    
    def _looks_like_project_directory(self, dir_path: Path) -> bool:
        """Check if a directory looks like a project directory."""
        if not dir_path.exists():
            return False
        
        # Look for common project file indicators
        project_indicators = [
            '.git', '.gitignore', 'package.json', 'requirements.txt',
            'Cargo.toml', 'pom.xml', 'build.gradle', 'Makefile',
            'README.md', 'README.txt', '.project', '.vscode'
        ]
        
        try:
            for item in dir_path.iterdir():
                if item.name in project_indicators:
                    return True
        except PermissionError:
            pass
        
        return False
    
    def _identify_cleanable_items(self, workspace_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify items that can be safely cleaned."""
        cleanable_items = []
        
        # Cache folders
        for cache_folder in workspace_info['cache_folders']:
            cleanable_items.append({
                'type': 'cache_folder',
                'path': cache_folder,
                'description': f"Cache folder: {cache_folder.name}",
                'risk_level': 'low',
                'size_estimate': self._estimate_directory_size(cache_folder)
            })
        
        # Temporary files
        for temp_file in workspace_info['temp_files']:
            cleanable_items.append({
                'type': 'temp_file',
                'path': temp_file,
                'description': f"Temporary file: {temp_file.name}",
                'risk_level': 'low',
                'size_estimate': self._get_file_size(temp_file)
            })
        
        # Session files
        for session_file in workspace_info['session_files']:
            cleanable_items.append({
                'type': 'session_file',
                'path': session_file,
                'description': f"Session file: {session_file.name}",
                'risk_level': 'medium',
                'size_estimate': self._get_file_size(session_file)
            })
        
        return cleanable_items
    
    def _estimate_directory_size(self, dir_path: Path) -> int:
        """Estimate the size of a directory."""
        total_size = 0
        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except PermissionError:
            pass
        return total_size
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get the size of a file."""
        try:
            return file_path.stat().st_size
        except (OSError, PermissionError):
            return 0
    
    def clean_workspace(self, workspace_info: Dict[str, Any], backup_dir: Path,
                       cleanup_options: Dict[str, Any]) -> bool:
        """Clean workspace based on specified options."""
        workspace_path = workspace_info['path']
        
        # Backup workspace if requested
        if cleanup_options.get('backup_workspace', True):
            backup_success = self.backup_manager.backup_directory(
                workspace_path, backup_dir, f"workspace/{workspace_path.name}"
            )
            if not backup_success:
                self.logger.error(f"Failed to backup workspace: {workspace_path}")
                return False
        
        success = True
        cleaned_items = 0
        
        # Clean selected items
        selected_items = cleanup_options.get('selected_items', [])
        
        for item_info in workspace_info['cleanable_items']:
            if item_info['type'] in selected_items:
                item_path = item_info['path']
                
                try:
                    if item_path.is_file():
                        item_path.unlink()
                        self.logger.info(f"Deleted file: {item_path}")
                    elif item_path.is_dir():
                        shutil.rmtree(item_path)
                        self.logger.info(f"Deleted directory: {item_path}")
                    
                    cleaned_items += 1
                
                except Exception as e:
                    self.logger.error(f"Failed to delete {item_path}: {e}")
                    success = False
        
        # Additional cleanup options
        if cleanup_options.get('clear_all_cache', False):
            success &= self._clear_all_cache_directories(workspace_path)
        
        if cleanup_options.get('remove_lock_files', False):
            success &= self._remove_lock_files(workspace_path)
        
        self.logger.info(f"Workspace cleanup completed: {cleaned_items} items cleaned")
        return success
    
    def _clear_all_cache_directories(self, workspace_path: Path) -> bool:
        """Clear all cache directories in the workspace."""
        try:
            cache_patterns = ['*cache*', '*tmp*', '*temp*', '__pycache__']
            
            for pattern in cache_patterns:
                for cache_dir in workspace_path.rglob(pattern):
                    if cache_dir.is_dir():
                        try:
                            shutil.rmtree(cache_dir)
                            self.logger.info(f"Cleared cache directory: {cache_dir}")
                        except Exception as e:
                            self.logger.error(f"Failed to clear cache directory {cache_dir}: {e}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error clearing cache directories: {e}")
            return False
    
    def _remove_lock_files(self, workspace_path: Path) -> bool:
        """Remove lock files from the workspace."""
        try:
            lock_patterns = ['*.lock', '*.lck', '.lock*']
            
            for pattern in lock_patterns:
                for lock_file in workspace_path.rglob(pattern):
                    if lock_file.is_file():
                        try:
                            lock_file.unlink()
                            self.logger.info(f"Removed lock file: {lock_file}")
                        except Exception as e:
                            self.logger.error(f"Failed to remove lock file {lock_file}: {e}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error removing lock files: {e}")
            return False
    
    def generate_workspace_report(self, workspace_locations: List[Dict[str, Any]]) -> str:
        """Generate a human-readable report of discovered workspace locations."""
        report_lines = []
        
        report_lines.append("=== WORKSPACE DISCOVERY REPORT ===")
        report_lines.append("")
        
        if not workspace_locations:
            report_lines.append("No workspace locations found.")
            return "\n".join(report_lines)
        
        # Summary
        total_size = sum(ws['total_size'] for ws in workspace_locations)
        total_files = sum(ws['file_count'] for ws in workspace_locations)
        total_cleanable = sum(len(ws['cleanable_items']) for ws in workspace_locations)
        
        report_lines.append(f"Summary:")
        report_lines.append(f"  Workspace locations: {len(workspace_locations)}")
        report_lines.append(f"  Total files: {total_files}")
        report_lines.append(f"  Total size: {self._format_size(total_size)}")
        report_lines.append(f"  Cleanable items: {total_cleanable}")
        report_lines.append("")
        
        # Detailed information
        for i, workspace in enumerate(workspace_locations, 1):
            report_lines.append(f"{i}. {workspace['name']}")
            report_lines.append(f"   Path: {workspace['path']}")
            report_lines.append(f"   Size: {self._format_size(workspace['total_size'])}")
            report_lines.append(f"   Files: {workspace['file_count']}")
            report_lines.append(f"   Cleanable items: {len(workspace['cleanable_items'])}")
            
            if workspace['cleanable_items']:
                report_lines.append("   Cleanable:")
                for item in workspace['cleanable_items'][:5]:  # Show first 5
                    size_str = self._format_size(item['size_estimate'])
                    report_lines.append(f"     - {item['description']} ({size_str})")
                
                if len(workspace['cleanable_items']) > 5:
                    remaining = len(workspace['cleanable_items']) - 5
                    report_lines.append(f"     ... and {remaining} more items")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
