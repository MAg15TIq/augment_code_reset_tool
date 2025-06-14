"""
Free AugmentCode Data Cleaner - Telemetry Manager
Handles telemetry ID discovery and modification across different storage methods.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    import winreg
except ImportError:
    winreg = None  # Not available on non-Windows systems
from utils import OSDetector, IDGenerator, FileSearcher
from config_manager import ConfigManager
from backup_manager import BackupManager


class TelemetryManager:
    """Manages telemetry ID discovery and modification."""
    
    def __init__(self, backup_manager: BackupManager):
        self.logger = logging.getLogger('FreeAugmentCode.TelemetryManager')
        self.backup_manager = backup_manager
        self.config_manager = ConfigManager()
    
    def discover_telemetry_data(self, augmentcode_paths: List[Path]) -> Dict[str, Any]:
        """Discover telemetry data across all possible storage locations."""
        discovery_results = {
            'config_files': [],
            'registry_keys': [],
            'found_ids': [],
            'total_locations': 0
        }
        
        # Search configuration files
        for path in augmentcode_paths:
            config_files = FileSearcher.find_config_files(path)
            discovery_results['config_files'].extend(config_files)
            
            # Search for telemetry IDs in config files
            found_ids = self.config_manager.search_for_telemetry_ids(config_files)
            discovery_results['found_ids'].extend(found_ids)
        
        # Search Windows registry (if on Windows)
        if OSDetector.is_windows():
            registry_data = self._search_registry_for_telemetry()
            discovery_results['registry_keys'] = registry_data
        
        discovery_results['total_locations'] = (
            len(discovery_results['config_files']) + 
            len(discovery_results['registry_keys'])
        )
        
        self.logger.info(f"Telemetry discovery complete: {len(discovery_results['found_ids'])} IDs found "
                        f"across {discovery_results['total_locations']} locations")
        
        return discovery_results
    
    def _search_registry_for_telemetry(self) -> List[Dict[str, Any]]:
        """Search Windows registry for AugmentCode telemetry data."""
        registry_data = []
        
        if not OSDetector.is_windows():
            return registry_data
        
        # Common registry paths where applications store data
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\AugmentCode"),
            (winreg.HKEY_CURRENT_USER, r"Software\Augment Code"),
            (winreg.HKEY_CURRENT_USER, r"Software\augmentcode"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AugmentCode"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Augment Code"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\augmentcode"),
        ]
        
        for hive, key_path in registry_paths:
            try:
                with winreg.OpenKey(hive, key_path) as key:
                    key_data = self._read_registry_key(key, key_path)
                    if key_data['values']:
                        registry_data.append({
                            'hive': hive,
                            'path': key_path,
                            'data': key_data
                        })
                        self.logger.info(f"Found registry key: {key_path}")
            
            except FileNotFoundError:
                # Key doesn't exist, continue
                continue
            except PermissionError:
                self.logger.warning(f"Permission denied accessing registry key: {key_path}")
                continue
            except Exception as e:
                self.logger.error(f"Error accessing registry key {key_path}: {e}")
                continue
        
        return registry_data
    
    def _read_registry_key(self, key: Any, key_path: str) -> Dict[str, Any]:
        """Read all values from a registry key."""
        key_data = {
            'path': key_path,
            'values': {},
            'subkeys': []
        }
        
        try:
            # Read values
            i = 0
            while True:
                try:
                    value_name, value_data, value_type = winreg.EnumValue(key, i)
                    key_data['values'][value_name] = {
                        'data': value_data,
                        'type': value_type
                    }
                    i += 1
                except OSError:
                    break
            
            # Read subkey names
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    key_data['subkeys'].append(subkey_name)
                    i += 1
                except OSError:
                    break
        
        except Exception as e:
            self.logger.error(f"Error reading registry key data: {e}")
        
        return key_data
    
    def modify_telemetry_ids(self, backup_dir: Path, 
                           modification_options: Dict[str, Any]) -> bool:
        """Modify telemetry IDs based on specified options."""
        success = True
        
        # Generate new IDs
        new_device_id = IDGenerator.generate_device_id()
        new_machine_id = IDGenerator.generate_machine_id()
        new_session_id = IDGenerator.generate_uuid()
        
        self.logger.info(f"Generated new IDs:")
        self.logger.info(f"  Device ID: {new_device_id}")
        self.logger.info(f"  Machine ID: {new_machine_id}")
        self.logger.info(f"  Session ID: {new_session_id}")
        
        # Modify configuration files
        if modification_options.get('modify_config_files', True):
            config_success = self._modify_config_file_ids(
                modification_options.get('found_ids', []),
                backup_dir,
                {
                    'device_id': new_device_id,
                    'machine_id': new_machine_id,
                    'session_id': new_session_id
                }
            )
            success &= config_success
        
        # Modify registry (Windows only)
        if OSDetector.is_windows() and modification_options.get('modify_registry', True):
            registry_success = self._modify_registry_ids(
                modification_options.get('registry_keys', []),
                backup_dir,
                {
                    'device_id': new_device_id,
                    'machine_id': new_machine_id,
                    'session_id': new_session_id
                }
            )
            success &= registry_success
        
        return success
    
    def _modify_config_file_ids(self, found_ids: List[Dict[str, Any]], 
                               backup_dir: Path, new_ids: Dict[str, str]) -> bool:
        """Modify telemetry IDs in configuration files."""
        success = True
        modified_files = set()
        
        for id_info in found_ids:
            file_path = id_info['file']
            
            # Backup file if not already backed up
            if file_path not in modified_files:
                backup_success = self.backup_manager.backup_file(
                    file_path, backup_dir, f"config_files/{file_path.name}"
                )
                if not backup_success:
                    self.logger.error(f"Failed to backup {file_path}")
                    success = False
                    continue
                modified_files.add(file_path)
            
            # Determine which new ID to use based on the pattern matched
            pattern = id_info.get('pattern_matched', '').lower()
            new_value = None
            
            if 'device' in pattern:
                new_value = new_ids['device_id']
            elif 'machine' in pattern:
                new_value = new_ids['machine_id']
            elif 'session' in pattern:
                new_value = new_ids['session_id']
            else:
                # Default to device ID for generic patterns
                new_value = new_ids['device_id']
            
            # Modify the ID
            modify_success = self.config_manager.modify_telemetry_id(id_info, new_value)
            if not modify_success:
                self.logger.error(f"Failed to modify ID in {file_path}")
                success = False
        
        self.logger.info(f"Modified telemetry IDs in {len(modified_files)} configuration files")
        return success
    
    def _modify_registry_ids(self, registry_keys: List[Dict[str, Any]], 
                           backup_dir: Path, new_ids: Dict[str, str]) -> bool:
        """Modify telemetry IDs in Windows registry."""
        if not OSDetector.is_windows():
            return True
        
        success = True
        
        for registry_entry in registry_keys:
            hive = registry_entry['hive']
            key_path = registry_entry['path']
            key_data = registry_entry['data']
            
            # Backup registry key data
            backup_success = self.backup_manager.backup_registry_key(
                backup_dir, key_path, key_data
            )
            if not backup_success:
                self.logger.error(f"Failed to backup registry key {key_path}")
                success = False
                continue
            
            # Modify registry values
            modify_success = self._modify_registry_key_values(
                hive, key_path, key_data['values'], new_ids
            )
            if not modify_success:
                success = False
        
        return success
    
    def _modify_registry_key_values(self, hive: int, key_path: str, 
                                   values: Dict[str, Any], new_ids: Dict[str, str]) -> bool:
        """Modify specific values in a registry key."""
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_SET_VALUE) as key:
                for value_name, value_info in values.items():
                    value_name_lower = value_name.lower()
                    
                    # Determine which ID to use based on value name
                    new_value = None
                    if 'device' in value_name_lower:
                        new_value = new_ids['device_id']
                    elif 'machine' in value_name_lower:
                        new_value = new_ids['machine_id']
                    elif 'session' in value_name_lower:
                        new_value = new_ids['session_id']
                    elif any(pattern in value_name_lower for pattern in ['id', 'guid', 'uuid']):
                        new_value = new_ids['device_id']  # Default
                    
                    if new_value:
                        old_value = value_info['data']
                        value_type = value_info['type']
                        
                        winreg.SetValueEx(key, value_name, 0, value_type, new_value)
                        self.logger.info(f"Modified registry value {value_name}: {old_value} -> {new_value}")
            
            return True
        
        except PermissionError:
            self.logger.error(f"Permission denied modifying registry key: {key_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error modifying registry key {key_path}: {e}")
            return False
    
    def generate_telemetry_report(self, discovery_results: Dict[str, Any]) -> str:
        """Generate a human-readable report of discovered telemetry data."""
        report_lines = []
        
        report_lines.append("=== TELEMETRY DISCOVERY REPORT ===")
        report_lines.append("")
        
        # Summary
        total_ids = len(discovery_results['found_ids'])
        total_files = len(discovery_results['config_files'])
        total_registry = len(discovery_results['registry_keys'])
        
        report_lines.append(f"Summary:")
        report_lines.append(f"  Total IDs found: {total_ids}")
        report_lines.append(f"  Configuration files: {total_files}")
        report_lines.append(f"  Registry keys: {total_registry}")
        report_lines.append("")
        
        # Configuration files
        if discovery_results['found_ids']:
            report_lines.append("Found Telemetry IDs:")
            for id_info in discovery_results['found_ids']:
                file_path = id_info['file']
                key = id_info.get('key', 'N/A')
                value = id_info.get('value', 'N/A')
                pattern = id_info.get('pattern_matched', 'N/A')
                
                report_lines.append(f"  File: {file_path}")
                report_lines.append(f"    Key: {key}")
                report_lines.append(f"    Value: {value}")
                report_lines.append(f"    Pattern: {pattern}")
                report_lines.append("")
        
        # Registry keys
        if discovery_results['registry_keys']:
            report_lines.append("Registry Keys:")
            for reg_entry in discovery_results['registry_keys']:
                key_path = reg_entry['path']
                values = reg_entry['data']['values']
                
                report_lines.append(f"  Key: {key_path}")
                for value_name, value_info in values.items():
                    report_lines.append(f"    {value_name}: {value_info['data']}")
                report_lines.append("")
        
        return "\n".join(report_lines)
