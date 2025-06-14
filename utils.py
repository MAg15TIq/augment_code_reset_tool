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
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


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
