"""
Free AugmentCode Data Cleaner - Backup Manager
Handles backup and restore operations for AugmentCode data.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from utils import SafeFileOperations, OSDetector


class BackupManager:
    """Manages backup and restore operations for AugmentCode data."""
    
    def __init__(self, backup_root: Optional[Path] = None):
        """Initialize backup manager with optional custom backup root."""
        self.logger = logging.getLogger('FreeAugmentCode.BackupManager')
        
        if backup_root:
            self.backup_root = backup_root
        else:
            # Default backup location
            if OSDetector.is_windows():
                documents = Path.home() / 'Documents'
            else:
                documents = Path.home()
            
            self.backup_root = documents / 'FreeAugmentCode_Backups'
        
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Backup root directory: {self.backup_root}")
    
    def create_timestamped_backup_dir(self) -> Path:
        """Create a new timestamped backup directory."""
        timestamp = datetime.now().strftime("Backup_%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a manifest file to track what was backed up
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'backup_type': 'AugmentCode_Data_Cleanup',
            'items': []
        }
        
        manifest_path = backup_dir / 'backup_manifest.json'
        SafeFileOperations.safe_write_json(manifest_path, manifest)
        
        self.logger.info(f"Created backup directory: {backup_dir}")
        return backup_dir
    
    def backup_file(self, source_file: Path, backup_dir: Path, 
                   relative_path: Optional[str] = None) -> bool:
        """Backup a single file to the backup directory."""
        if not source_file.exists():
            self.logger.error(f"Source file does not exist: {source_file}")
            return False
        
        if relative_path:
            dest_file = backup_dir / relative_path
        else:
            dest_file = backup_dir / 'files' / source_file.name
        
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(source_file, dest_file)
            self.logger.info(f"Backed up file: {source_file} -> {dest_file}")
            
            # Update manifest
            self._update_manifest(backup_dir, {
                'type': 'file',
                'source': str(source_file),
                'destination': str(dest_file),
                'size': source_file.stat().st_size
            })
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup file {source_file}: {e}")
            return False
    
    def backup_directory(self, source_dir: Path, backup_dir: Path, 
                        relative_path: Optional[str] = None) -> bool:
        """Backup an entire directory to the backup directory."""
        if not source_dir.exists():
            self.logger.error(f"Source directory does not exist: {source_dir}")
            return False
        
        if relative_path:
            dest_dir = backup_dir / relative_path
        else:
            dest_dir = backup_dir / 'directories' / source_dir.name
        
        try:
            shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            self.logger.info(f"Backed up directory: {source_dir} -> {dest_dir}")
            
            # Calculate directory size
            total_size = sum(f.stat().st_size for f in source_dir.rglob('*') if f.is_file())
            
            # Update manifest
            self._update_manifest(backup_dir, {
                'type': 'directory',
                'source': str(source_dir),
                'destination': str(dest_dir),
                'size': total_size
            })
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup directory {source_dir}: {e}")
            return False
    
    def backup_registry_key(self, backup_dir: Path, key_path: str, 
                           key_data: Dict[str, Any]) -> bool:
        """Backup Windows registry key data (stored as JSON)."""
        if not OSDetector.is_windows():
            self.logger.warning("Registry backup requested on non-Windows system")
            return False
        
        registry_backup_dir = backup_dir / 'registry'
        registry_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize key path for filename
        safe_filename = key_path.replace('\\', '_').replace('/', '_').replace(':', '_')
        backup_file = registry_backup_dir / f"{safe_filename}.json"
        
        registry_data = {
            'key_path': key_path,
            'backup_timestamp': datetime.now().isoformat(),
            'data': key_data
        }
        
        if SafeFileOperations.safe_write_json(backup_file, registry_data):
            self.logger.info(f"Backed up registry key: {key_path}")
            
            # Update manifest
            self._update_manifest(backup_dir, {
                'type': 'registry',
                'key_path': key_path,
                'backup_file': str(backup_file)
            })
            
            return True
        else:
            return False
    
    def _update_manifest(self, backup_dir: Path, item_info: Dict[str, Any]) -> None:
        """Update the backup manifest with new item information."""
        manifest_path = backup_dir / 'backup_manifest.json'
        
        manifest = SafeFileOperations.safe_read_json(manifest_path)
        if manifest:
            manifest['items'].append(item_info)
            SafeFileOperations.safe_write_json(manifest_path, manifest)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with their information."""
        backups = []
        
        if not self.backup_root.exists():
            return backups
        
        for backup_dir in self.backup_root.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith('Backup_'):
                manifest_path = backup_dir / 'backup_manifest.json'
                
                backup_info = {
                    'name': backup_dir.name,
                    'path': backup_dir,
                    'timestamp': None,
                    'items_count': 0,
                    'total_size': 0
                }
                
                if manifest_path.exists():
                    manifest = SafeFileOperations.safe_read_json(manifest_path)
                    if manifest:
                        backup_info['timestamp'] = manifest.get('timestamp')
                        backup_info['items_count'] = len(manifest.get('items', []))
                        backup_info['total_size'] = sum(
                            item.get('size', 0) for item in manifest.get('items', [])
                        )
                
                backups.append(backup_info)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return backups
    
    def restore_from_backup(self, backup_dir: Path) -> bool:
        """Restore data from a backup directory."""
        manifest_path = backup_dir / 'backup_manifest.json'
        
        if not manifest_path.exists():
            self.logger.error(f"No manifest found in backup directory: {backup_dir}")
            return False
        
        manifest = SafeFileOperations.safe_read_json(manifest_path)
        if not manifest:
            self.logger.error(f"Failed to read manifest from: {manifest_path}")
            return False
        
        success_count = 0
        total_items = len(manifest.get('items', []))
        
        for item in manifest.get('items', []):
            try:
                if item['type'] == 'file':
                    source = Path(item['destination'])
                    dest = Path(item['source'])
                    
                    if source.exists():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        success_count += 1
                        self.logger.info(f"Restored file: {dest}")
                    else:
                        self.logger.warning(f"Backup file not found: {source}")
                
                elif item['type'] == 'directory':
                    source = Path(item['destination'])
                    dest = Path(item['source'])
                    
                    if source.exists():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                        success_count += 1
                        self.logger.info(f"Restored directory: {dest}")
                    else:
                        self.logger.warning(f"Backup directory not found: {source}")
                
                elif item['type'] == 'registry':
                    # Registry restoration would require additional implementation
                    self.logger.warning("Registry restoration not yet implemented")
                
            except Exception as e:
                self.logger.error(f"Failed to restore item {item}: {e}")
        
        self.logger.info(f"Restoration complete: {success_count}/{total_items} items restored")
        return success_count > 0
    
    def delete_backup(self, backup_dir: Path) -> bool:
        """Delete a backup directory."""
        try:
            shutil.rmtree(backup_dir)
            self.logger.info(f"Deleted backup: {backup_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_dir}: {e}")
            return False
