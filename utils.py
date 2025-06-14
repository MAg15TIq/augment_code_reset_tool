"""
Free AugmentCode Data Cleaner - Utility Functions
Provides cross-platform utilities, OS detection, and common helper functions.
"""

import os
import platform
import logging
import uuid
import random
import string
import subprocess
import psutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import json
import re


class OSDetector:
    """Detect operating system and provide platform-specific paths."""
    
    @staticmethod
    def get_os_type() -> str:
        """Get the current operating system type."""
        return platform.system().lower()
    
    @staticmethod
    def is_windows() -> bool:
        return platform.system().lower() == 'windows'
    
    @staticmethod
    def is_macos() -> bool:
        return platform.system().lower() == 'darwin'
    
    @staticmethod
    def is_linux() -> bool:
        return platform.system().lower() == 'linux'


class PathFinder:
    """Find common application data directories across platforms."""
    
    @staticmethod
    def get_app_data_paths() -> List[Path]:
        """Get list of common application data directories for current OS."""
        paths = []
        
        if OSDetector.is_windows():
            # Windows paths
            if 'APPDATA' in os.environ:
                paths.append(Path(os.environ['APPDATA']))
            if 'LOCALAPPDATA' in os.environ:
                paths.append(Path(os.environ['LOCALAPPDATA']))
            if 'PROGRAMDATA' in os.environ:
                paths.append(Path(os.environ['PROGRAMDATA']))
            if 'PROGRAMFILES' in os.environ:
                paths.append(Path(os.environ['PROGRAMFILES']))
                
        elif OSDetector.is_macos():
            # macOS paths
            home = Path.home()
            paths.extend([
                home / 'Library' / 'Application Support',
                Path('/Library/Application Support'),
                home / 'Library' / 'Preferences',
                home / '.config'
            ])
            
        elif OSDetector.is_linux():
            # Linux paths
            home = Path.home()
            paths.extend([
                home / '.config',
                home / '.local' / 'share',
                Path('/etc'),
                Path('/usr/share'),
                Path('/opt')
            ])
        
        # Filter to only existing paths
        return [path for path in paths if path.exists()]


class IDEDetector:
    """Advanced IDE detection and process management for AugmentCode."""

    # Known IDEs that support AugmentCode
    SUPPORTED_IDES = {
        'vscode': {
            'name': 'Visual Studio Code',
            'process_names': ['code.exe', 'code', 'Code.exe', 'Code'],
            'config_paths': {
                'windows': ['AppData/Roaming/Code/User', 'AppData/Local/Programs/Microsoft VS Code'],
                'macos': ['Library/Application Support/Code/User', '/Applications/Visual Studio Code.app'],
                'linux': ['.config/Code/User', '.vscode']
            },
            'extension_patterns': ['augmentcode', 'augment-code', 'augment_code']
        },
        'cursor': {
            'name': 'Cursor',
            'process_names': ['cursor.exe', 'cursor', 'Cursor.exe', 'Cursor'],
            'config_paths': {
                'windows': ['AppData/Roaming/Cursor/User', 'AppData/Local/Programs/Cursor'],
                'macos': ['Library/Application Support/Cursor/User', '/Applications/Cursor.app'],
                'linux': ['.config/Cursor/User', '.cursor']
            },
            'extension_patterns': ['augmentcode', 'augment-code', 'augment_code']
        },
        'windsurf': {
            'name': 'Windsurf',
            'process_names': ['windsurf.exe', 'windsurf', 'Windsurf.exe', 'Windsurf'],
            'config_paths': {
                'windows': ['AppData/Roaming/Windsurf/User', 'AppData/Local/Programs/Windsurf'],
                'macos': ['Library/Application Support/Windsurf/User', '/Applications/Windsurf.app'],
                'linux': ['.config/Windsurf/User', '.windsurf']
            },
            'extension_patterns': ['augmentcode', 'augment-code', 'augment_code']
        },
        'zed': {
            'name': 'Zed',
            'process_names': ['zed.exe', 'zed', 'Zed.exe', 'Zed'],
            'config_paths': {
                'windows': ['AppData/Roaming/Zed', 'AppData/Local/Programs/Zed'],
                'macos': ['Library/Application Support/Zed', '/Applications/Zed.app'],
                'linux': ['.config/zed', '.zed']
            },
            'extension_patterns': ['augmentcode', 'augment-code', 'augment_code']
        },
        'sublime': {
            'name': 'Sublime Text',
            'process_names': ['sublime_text.exe', 'sublime_text', 'subl.exe', 'subl'],
            'config_paths': {
                'windows': ['AppData/Roaming/Sublime Text', 'AppData/Local/Sublime Text'],
                'macos': ['Library/Application Support/Sublime Text', '/Applications/Sublime Text.app'],
                'linux': ['.config/sublime-text', '.sublime-text']
            },
            'extension_patterns': ['augmentcode', 'augment-code', 'augment_code']
        }
    }

    @staticmethod
    def detect_running_augmentcode_processes() -> List[Dict[str, Any]]:
        """Detect all running processes that might be using AugmentCode."""
        running_processes = []

        try:
            for process in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    process_info = process.info
                    process_name = process_info.get('name', '').lower()
                    process_exe = process_info.get('exe', '')
                    cmdline = ' '.join(process_info.get('cmdline', [])).lower()

                    # Check if this process is related to any known IDE
                    for ide_key, ide_info in IDEDetector.SUPPORTED_IDES.items():
                        for proc_name in ide_info['process_names']:
                            if proc_name.lower() in process_name:
                                # Check if this IDE instance has AugmentCode loaded
                                has_augmentcode = IDEDetector._check_process_for_augmentcode(
                                    process, ide_key, cmdline
                                )

                                if has_augmentcode:
                                    running_processes.append({
                                        'pid': process_info['pid'],
                                        'name': process_info['name'],
                                        'exe': process_exe,
                                        'ide': ide_info['name'],
                                        'ide_key': ide_key,
                                        'augmentcode_detected': True,
                                        'cmdline': cmdline
                                    })
                                break

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            logging.error(f"Error detecting processes: {e}")

        return running_processes

    @staticmethod
    def _check_process_for_augmentcode(process, ide_key: str, cmdline: str) -> bool:
        """Check if a specific process has AugmentCode loaded."""
        try:
            # Check command line arguments for AugmentCode-related flags
            augmentcode_indicators = [
                'augmentcode', 'augment-code', 'augment_code',
                '--enable-augmentcode', '--augmentcode-enabled',
                'augment.extension', 'augment.plugin'
            ]

            for indicator in augmentcode_indicators:
                if indicator in cmdline:
                    return True

            # Check if the process has AugmentCode extension files open
            try:
                open_files = process.open_files()
                for file_info in open_files:
                    file_path = file_info.path.lower()
                    if any(pattern in file_path for pattern in ['augmentcode', 'augment-code', 'augment_code']):
                        return True
            except (psutil.AccessDenied, AttributeError):
                pass

            return False

        except Exception:
            return False

    @staticmethod
    def detect_ide_installations() -> Dict[str, List[Dict[str, Any]]]:
        """Detect all IDE installations that might have AugmentCode."""
        installations = {}
        os_type = OSDetector.get_os_type()
        home = Path.home()

        for ide_key, ide_info in IDEDetector.SUPPORTED_IDES.items():
            installations[ide_key] = []

            # Get OS-specific config paths
            config_paths = ide_info['config_paths'].get(os_type, [])

            for config_path in config_paths:
                if config_path.startswith('/'):
                    # Absolute path
                    full_path = Path(config_path)
                else:
                    # Relative to home directory
                    full_path = home / config_path

                if full_path.exists():
                    # Check for AugmentCode extensions/plugins
                    augmentcode_data = IDEDetector._find_augmentcode_in_ide(full_path, ide_info)

                    if augmentcode_data:
                        installations[ide_key].append({
                            'path': full_path,
                            'ide_name': ide_info['name'],
                            'augmentcode_data': augmentcode_data
                        })

        return installations

    @staticmethod
    def _find_augmentcode_in_ide(ide_path: Path, ide_info: Dict[str, Any]) -> Dict[str, Any]:
        """Find AugmentCode-related data in an IDE installation."""
        augmentcode_data = {
            'extensions': [],
            'config_files': [],
            'workspace_data': [],
            'cache_files': []
        }

        try:
            # Search for extensions
            extensions_dirs = [
                ide_path / 'extensions',
                ide_path / 'plugins',
                ide_path / 'addons'
            ]

            for ext_dir in extensions_dirs:
                if ext_dir.exists():
                    for item in ext_dir.iterdir():
                        if item.is_dir():
                            for pattern in ide_info['extension_patterns']:
                                if pattern in item.name.lower():
                                    augmentcode_data['extensions'].append({
                                        'path': item,
                                        'name': item.name,
                                        'type': 'extension'
                                    })
                                    break

            # Search for config files
            config_patterns = ['augmentcode', 'augment-code', 'augment_code']
            for config_file in ide_path.rglob('*'):
                if config_file.is_file():
                    file_name_lower = config_file.name.lower()
                    for pattern in config_patterns:
                        if pattern in file_name_lower:
                            augmentcode_data['config_files'].append({
                                'path': config_file,
                                'name': config_file.name,
                                'size': config_file.stat().st_size
                            })
                            break

            # Search for workspace data
            workspace_dirs = [
                ide_path / 'workspaceStorage',
                ide_path / 'workspace',
                ide_path / 'projects'
            ]

            for workspace_dir in workspace_dirs:
                if workspace_dir.exists():
                    for item in workspace_dir.rglob('*augment*'):
                        if item.is_file():
                            augmentcode_data['workspace_data'].append({
                                'path': item,
                                'name': item.name,
                                'size': item.stat().st_size
                            })

            # Search for cache files
            cache_dirs = [
                ide_path / 'CachedExtensions',
                ide_path / 'cache',
                ide_path / 'logs'
            ]

            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    for item in cache_dir.rglob('*augment*'):
                        if item.is_file():
                            augmentcode_data['cache_files'].append({
                                'path': item,
                                'name': item.name,
                                'size': item.stat().st_size
                            })

        except PermissionError:
            logging.warning(f"Permission denied accessing {ide_path}")
        except Exception as e:
            logging.error(f"Error searching IDE path {ide_path}: {e}")

        return augmentcode_data if any(augmentcode_data.values()) else None

    @staticmethod
    def terminate_augmentcode_processes(process_list: List[Dict[str, Any]], force: bool = False) -> Dict[str, Any]:
        """Safely terminate AugmentCode-related processes."""
        results = {
            'terminated': [],
            'failed': [],
            'warnings': []
        }

        for proc_info in process_list:
            try:
                pid = proc_info['pid']
                process = psutil.Process(pid)

                if process.is_running():
                    ide_name = proc_info.get('ide', 'Unknown IDE')

                    if force:
                        # Force kill the process
                        process.kill()
                        results['terminated'].append({
                            'pid': pid,
                            'ide': ide_name,
                            'method': 'force_kill'
                        })
                    else:
                        # Try graceful termination first
                        process.terminate()

                        # Wait for graceful termination
                        try:
                            process.wait(timeout=10)
                            results['terminated'].append({
                                'pid': pid,
                                'ide': ide_name,
                                'method': 'graceful'
                            })
                        except psutil.TimeoutExpired:
                            # If graceful termination fails, force kill
                            process.kill()
                            results['terminated'].append({
                                'pid': pid,
                                'ide': ide_name,
                                'method': 'force_kill_after_timeout'
                            })
                            results['warnings'].append(f"Had to force kill {ide_name} (PID: {pid})")

            except psutil.NoSuchProcess:
                # Process already terminated
                results['terminated'].append({
                    'pid': proc_info['pid'],
                    'ide': proc_info.get('ide', 'Unknown'),
                    'method': 'already_terminated'
                })
            except psutil.AccessDenied:
                results['failed'].append({
                    'pid': proc_info['pid'],
                    'ide': proc_info.get('ide', 'Unknown'),
                    'error': 'Access denied - try running as administrator'
                })
            except Exception as e:
                results['failed'].append({
                    'pid': proc_info['pid'],
                    'ide': proc_info.get('ide', 'Unknown'),
                    'error': str(e)
                })

        return results

    @staticmethod
    def generate_ide_report(installations: Dict[str, List[Dict[str, Any]]],
                           running_processes: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive report of IDE installations and AugmentCode usage."""
        report_lines = []

        report_lines.append("=" * 80)
        report_lines.append("AUGMENTCODE IDE DETECTION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Running processes section
        report_lines.append("🔄 RUNNING PROCESSES WITH AUGMENTCODE:")
        if running_processes:
            for proc in running_processes:
                report_lines.append(f"  • {proc['ide']} (PID: {proc['pid']})")
                report_lines.append(f"    Process: {proc['name']}")
                if proc.get('exe'):
                    report_lines.append(f"    Executable: {proc['exe']}")
        else:
            report_lines.append("  ✅ No AugmentCode processes currently running")
        report_lines.append("")

        # IDE installations section
        report_lines.append("💻 IDE INSTALLATIONS WITH AUGMENTCODE:")
        total_installations = sum(len(installs) for installs in installations.values())

        if total_installations > 0:
            for ide_key, installs in installations.items():
                if installs:
                    ide_name = IDEDetector.SUPPORTED_IDES[ide_key]['name']
                    report_lines.append(f"  📁 {ide_name}:")

                    for install in installs:
                        report_lines.append(f"    Path: {install['path']}")
                        data = install['augmentcode_data']

                        if data['extensions']:
                            report_lines.append(f"    Extensions: {len(data['extensions'])} found")
                        if data['config_files']:
                            report_lines.append(f"    Config files: {len(data['config_files'])} found")
                        if data['workspace_data']:
                            report_lines.append(f"    Workspace data: {len(data['workspace_data'])} files")
                        if data['cache_files']:
                            report_lines.append(f"    Cache files: {len(data['cache_files'])} files")
                        report_lines.append("")
        else:
            report_lines.append("  ✅ No IDE installations with AugmentCode detected")

        report_lines.append("")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)


class IDGenerator:
    """Generate various types of unique identifiers."""
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID4 as a 32-character hex string."""
        return uuid.uuid4().hex
    
    @staticmethod
    def generate_random_string(length: int = 16) -> str:
        """Generate a random alphanumeric string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def generate_device_id() -> str:
        """Generate a device ID in common format."""
        return f"device_{IDGenerator.generate_uuid()}"
    
    @staticmethod
    def generate_machine_id() -> str:
        """Generate a machine ID in common format."""
        return f"machine_{IDGenerator.generate_uuid()}"


class FileSearcher:
    """Search for files and patterns across directories."""
    
    @staticmethod
    def find_augmentcode_directories(search_paths: List[Path]) -> List[Path]:
        """Find directories that might contain AugmentCode data."""
        found_dirs = []
        search_patterns = [
            'augmentcode', 'AugmentCode', 'Augment Code', 'augment_code',
            'augment', 'Augment'
        ]
        
        for base_path in search_paths:
            if not base_path.exists():
                continue
                
            try:
                for item in base_path.iterdir():
                    if item.is_dir():
                        for pattern in search_patterns:
                            if pattern.lower() in item.name.lower():
                                found_dirs.append(item)
                                break
            except PermissionError:
                logging.warning(f"Permission denied accessing {base_path}")
                continue
        
        return found_dirs
    
    @staticmethod
    def find_config_files(directory: Path) -> List[Path]:
        """Find configuration files in a directory."""
        config_extensions = ['.json', '.ini', '.xml', '.cfg', '.conf', '.config']
        config_files = []
        
        if not directory.exists():
            return config_files
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in config_extensions:
                    config_files.append(file_path)
        except PermissionError:
            logging.warning(f"Permission denied searching {directory}")
        
        return config_files
    
    @staticmethod
    def find_database_files(directory: Path) -> List[Path]:
        """Find SQLite database files in a directory."""
        db_extensions = ['.db', '.sqlite', '.sqlite3']
        db_files = []
        
        if not directory.exists():
            return db_files
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in db_extensions:
                    db_files.append(file_path)
        except PermissionError:
            logging.warning(f"Permission denied searching {directory}")
        
        return db_files


class Logger:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('FreeAugmentCode')
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        return logger


class SafeFileOperations:
    """Safe file operations with error handling."""
    
    @staticmethod
    def safe_read_json(file_path: Path) -> Optional[Dict[str, Any]]:
        """Safely read a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            logging.error(f"Failed to read JSON file {file_path}: {e}")
            return None
    
    @staticmethod
    def safe_write_json(file_path: Path, data: Dict[str, Any]) -> bool:
        """Safely write a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to write JSON file {file_path}: {e}")
            return False
    
    @staticmethod
    def safe_copy_file(src: Path, dst: Path) -> bool:
        """Safely copy a file."""
        try:
            import shutil
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except (PermissionError, OSError, FileNotFoundError) as e:
            logging.error(f"Failed to copy file {src} to {dst}: {e}")
            return False
