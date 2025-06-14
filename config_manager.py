"""
Free AugmentCode Data Cleaner - Configuration Manager
Handles reading and writing various configuration file formats.
"""

import logging
import configparser
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import re

from utils import SafeFileOperations


class ConfigManager:
    """Manages configuration files in various formats (JSON, INI, XML)."""
    
    def __init__(self):
        self.logger = logging.getLogger('FreeAugmentCode.ConfigManager')
    
    def search_for_telemetry_ids(self, config_files: List[Path]) -> List[Dict[str, Any]]:
        """Search for telemetry IDs in configuration files."""
        found_ids = []

        # Common patterns for telemetry IDs
        id_patterns = [
            r'device[_-]?id',
            r'machine[_-]?id',
            r'telemetry[_-]?id',
            r'client[_-]?id',
            r'unique[_-]?id',
            r'installation[_-]?id',
            r'session[_-]?id',
            r'user[_-]?id',
            r'guid',
            r'uuid'
        ]
        
        for config_file in config_files:
            self.logger.info(f"Searching for telemetry IDs in: {config_file}")
            
            try:
                if config_file.suffix.lower() == '.json':
                    ids = self._search_json_for_ids(config_file, id_patterns)
                elif config_file.suffix.lower() in ['.ini', '.cfg', '.conf']:
                    ids = self._search_ini_for_ids(config_file, id_patterns)
                elif config_file.suffix.lower() == '.xml':
                    ids = self._search_xml_for_ids(config_file, id_patterns)
                else:
                    # Try to search as plain text
                    ids = self._search_text_for_ids(config_file, id_patterns)
                
                if ids:
                    found_ids.extend(ids)
                    
            except Exception as e:
                self.logger.error(f"Error searching {config_file}: {e}")
        
        return found_ids

    def search_for_account_data(self, config_files: List[Path]) -> List[Dict[str, Any]]:
        """Search for email addresses and account data in configuration files."""
        found_accounts = []

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Account-related patterns
        account_patterns = [
            r'email',
            r'username',
            r'user[_-]?name',
            r'login',
            r'account',
            r'profile',
            r'identity'
        ]

        for config_file in config_files:
            self.logger.info(f"Searching for account data in: {config_file}")

            try:
                if config_file.suffix.lower() == '.json':
                    accounts = self._search_json_for_accounts(config_file, email_pattern, account_patterns)
                elif config_file.suffix.lower() in ['.ini', '.cfg', '.conf']:
                    accounts = self._search_ini_for_accounts(config_file, email_pattern, account_patterns)
                elif config_file.suffix.lower() == '.xml':
                    accounts = self._search_xml_for_accounts(config_file, email_pattern, account_patterns)
                else:
                    # Try to search as plain text
                    accounts = self._search_text_for_accounts(config_file, email_pattern, account_patterns)

                if accounts:
                    found_accounts.extend(accounts)

            except Exception as e:
                self.logger.error(f"Error searching {config_file}: {e}")

        return found_accounts

    def _search_json_for_ids(self, file_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for ID patterns in JSON files."""
        found_ids = []
        data = SafeFileOperations.safe_read_json(file_path)
        
        if not data:
            return found_ids
        
        def search_dict(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if key matches any pattern
                    for pattern in patterns:
                        if re.search(pattern, key, re.IGNORECASE):
                            found_ids.append({
                                'file': file_path,
                                'format': 'json',
                                'key_path': current_path,
                                'key': key,
                                'value': value,
                                'pattern_matched': pattern
                            })
                            break
                    
                    # Recursively search nested objects
                    search_dict(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_dict(item, f"{path}[{i}]")
        
        search_dict(data)
        return found_ids
    
    def _search_ini_for_ids(self, file_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for ID patterns in INI files."""
        found_ids = []
        
        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')
            
            for section_name in config.sections():
                section = config[section_name]
                for key, value in section.items():
                    for pattern in patterns:
                        if re.search(pattern, key, re.IGNORECASE):
                            found_ids.append({
                                'file': file_path,
                                'format': 'ini',
                                'section': section_name,
                                'key': key,
                                'value': value,
                                'pattern_matched': pattern
                            })
                            break
        except Exception as e:
            self.logger.error(f"Error parsing INI file {file_path}: {e}")
        
        return found_ids
    
    def _search_xml_for_ids(self, file_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for ID patterns in XML files."""
        found_ids = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            def search_element(element: ET.Element, path: str = "") -> None:
                current_path = f"{path}/{element.tag}" if path else element.tag
                
                # Check element tag
                for pattern in patterns:
                    if re.search(pattern, element.tag, re.IGNORECASE):
                        found_ids.append({
                            'file': file_path,
                            'format': 'xml',
                            'element_path': current_path,
                            'tag': element.tag,
                            'value': element.text,
                            'pattern_matched': pattern,
                            'type': 'element'
                        })
                        break
                
                # Check attributes
                for attr_name, attr_value in element.attrib.items():
                    for pattern in patterns:
                        if re.search(pattern, attr_name, re.IGNORECASE):
                            found_ids.append({
                                'file': file_path,
                                'format': 'xml',
                                'element_path': current_path,
                                'attribute': attr_name,
                                'value': attr_value,
                                'pattern_matched': pattern,
                                'type': 'attribute'
                            })
                            break
                
                # Recursively search child elements
                for child in element:
                    search_element(child, current_path)
            
            search_element(root)
            
        except Exception as e:
            self.logger.error(f"Error parsing XML file {file_path}: {e}")
        
        return found_ids
    
    def _search_text_for_ids(self, file_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for ID patterns in plain text files."""
        found_ids = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    # Look for key=value or key:value patterns
                    match = re.search(rf'({pattern})\s*[=:]\s*([^\s\n]+)', line, re.IGNORECASE)
                    if match:
                        found_ids.append({
                            'file': file_path,
                            'format': 'text',
                            'line_number': line_num,
                            'key': match.group(1),
                            'value': match.group(2),
                            'pattern_matched': pattern,
                            'full_line': line.strip()
                        })
        
        except Exception as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")
        
        return found_ids
    
    def modify_telemetry_id(self, id_info: Dict[str, Any], new_value: str) -> bool:
        """Modify a telemetry ID in its configuration file."""
        file_path = id_info['file']
        format_type = id_info['format']
        
        self.logger.info(f"Modifying ID in {file_path} (format: {format_type})")
        
        try:
            if format_type == 'json':
                return self._modify_json_id(id_info, new_value)
            elif format_type == 'ini':
                return self._modify_ini_id(id_info, new_value)
            elif format_type == 'xml':
                return self._modify_xml_id(id_info, new_value)
            elif format_type == 'text':
                return self._modify_text_id(id_info, new_value)
            else:
                self.logger.error(f"Unsupported format: {format_type}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error modifying ID: {e}")
            return False
    
    def _modify_json_id(self, id_info: Dict[str, Any], new_value: str) -> bool:
        """Modify an ID in a JSON file."""
        file_path = id_info['file']
        key_path = id_info['key_path']
        
        data = SafeFileOperations.safe_read_json(file_path)
        if not data:
            return False
        
        # Navigate to the key using the path
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                self.logger.error(f"Key path not found: {key_path}")
                return False
        
        # Modify the final key
        final_key = keys[-1]
        if final_key in current:
            old_value = current[final_key]
            current[final_key] = new_value
            self.logger.info(f"Changed {final_key}: {old_value} -> {new_value}")
            
            return SafeFileOperations.safe_write_json(file_path, data)
        else:
            self.logger.error(f"Final key not found: {final_key}")
            return False
    
    def _modify_ini_id(self, id_info: Dict[str, Any], new_value: str) -> bool:
        """Modify an ID in an INI file."""
        file_path = id_info['file']
        section_name = id_info['section']
        key = id_info['key']
        
        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')
        
        if section_name in config and key in config[section_name]:
            old_value = config[section_name][key]
            config[section_name][key] = new_value
            self.logger.info(f"Changed [{section_name}] {key}: {old_value} -> {new_value}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                config.write(f)
            return True
        else:
            self.logger.error(f"Section/key not found: [{section_name}] {key}")
            return False
    
    def _modify_xml_id(self, id_info: Dict[str, Any], new_value: str) -> bool:
        """Modify an ID in an XML file."""
        file_path = id_info['file']
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # This is a simplified implementation
        # In practice, you'd need to navigate to the specific element
        # based on the stored path information
        
        if id_info['type'] == 'element':
            # Find and modify element text
            for elem in root.iter():
                if elem.tag == id_info['tag'] and elem.text == id_info['value']:
                    old_value = elem.text
                    elem.text = new_value
                    self.logger.info(f"Changed element {elem.tag}: {old_value} -> {new_value}")
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)
                    return True
        
        elif id_info['type'] == 'attribute':
            # Find and modify attribute
            for elem in root.iter():
                if id_info['attribute'] in elem.attrib:
                    if elem.attrib[id_info['attribute']] == id_info['value']:
                        old_value = elem.attrib[id_info['attribute']]
                        elem.attrib[id_info['attribute']] = new_value
                        self.logger.info(f"Changed attribute {id_info['attribute']}: {old_value} -> {new_value}")
                        tree.write(file_path, encoding='utf-8', xml_declaration=True)
                        return True
        
        return False
    
    def _modify_text_id(self, id_info: Dict[str, Any], new_value: str) -> bool:
        """Modify an ID in a plain text file."""
        file_path = id_info['file']
        line_number = id_info['line_number']
        key = id_info['key']
        old_value = id_info['value']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if line_number <= len(lines):
                old_line = lines[line_number - 1]
                new_line = old_line.replace(f"{key}={old_value}", f"{key}={new_value}")
                new_line = new_line.replace(f"{key}:{old_value}", f"{key}:{new_value}")
                
                if new_line != old_line:
                    lines[line_number - 1] = new_line
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    self.logger.info(f"Changed {key}: {old_value} -> {new_value}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error modifying text file: {e}")
            return False

    def _search_json_for_accounts(self, file_path: Path, email_pattern: str, account_patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for account data in JSON files."""
        found_accounts = []
        data = SafeFileOperations.safe_read_json(file_path)

        if not data:
            return found_accounts

        def search_dict(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    # Check if key matches account patterns
                    for pattern in account_patterns:
                        if re.search(pattern, key, re.IGNORECASE):
                            found_accounts.append({
                                'file': file_path,
                                'format': 'json',
                                'key_path': current_path,
                                'key': key,
                                'value': value,
                                'pattern_matched': pattern,
                                'data_type': 'account_field'
                            })
                            break

                    # Check if value is an email
                    if isinstance(value, str) and re.match(email_pattern, value):
                        found_accounts.append({
                            'file': file_path,
                            'format': 'json',
                            'key_path': current_path,
                            'key': key,
                            'value': value,
                            'pattern_matched': 'email',
                            'data_type': 'email'
                        })

                    # Recursively search nested objects
                    search_dict(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_dict(item, f"{path}[{i}]")

        search_dict(data)
        return found_accounts

    def _search_ini_for_accounts(self, file_path: Path, email_pattern: str, account_patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for account data in INI files."""
        found_accounts = []

        try:
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')

            for section_name in config.sections():
                section = config[section_name]
                for key, value in section.items():
                    # Check for account patterns
                    for pattern in account_patterns:
                        if re.search(pattern, key, re.IGNORECASE):
                            found_accounts.append({
                                'file': file_path,
                                'format': 'ini',
                                'section': section_name,
                                'key': key,
                                'value': value,
                                'pattern_matched': pattern,
                                'data_type': 'account_field'
                            })
                            break

                    # Check for email values
                    if re.match(email_pattern, value):
                        found_accounts.append({
                            'file': file_path,
                            'format': 'ini',
                            'section': section_name,
                            'key': key,
                            'value': value,
                            'pattern_matched': 'email',
                            'data_type': 'email'
                        })
        except Exception as e:
            self.logger.error(f"Error parsing INI file {file_path}: {e}")

        return found_accounts

    def _search_xml_for_accounts(self, file_path: Path, email_pattern: str, account_patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for account data in XML files."""
        found_accounts = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            def search_element(element: ET.Element, path: str = "") -> None:
                current_path = f"{path}/{element.tag}" if path else element.tag

                # Check element tag for account patterns
                for pattern in account_patterns:
                    if re.search(pattern, element.tag, re.IGNORECASE):
                        found_accounts.append({
                            'file': file_path,
                            'format': 'xml',
                            'element_path': current_path,
                            'tag': element.tag,
                            'value': element.text,
                            'pattern_matched': pattern,
                            'type': 'element',
                            'data_type': 'account_field'
                        })
                        break

                # Check element text for emails
                if element.text and re.match(email_pattern, element.text.strip()):
                    found_accounts.append({
                        'file': file_path,
                        'format': 'xml',
                        'element_path': current_path,
                        'tag': element.tag,
                        'value': element.text,
                        'pattern_matched': 'email',
                        'type': 'element',
                        'data_type': 'email'
                    })

                # Check attributes
                for attr_name, attr_value in element.attrib.items():
                    # Check attribute names for account patterns
                    for pattern in account_patterns:
                        if re.search(pattern, attr_name, re.IGNORECASE):
                            found_accounts.append({
                                'file': file_path,
                                'format': 'xml',
                                'element_path': current_path,
                                'attribute': attr_name,
                                'value': attr_value,
                                'pattern_matched': pattern,
                                'type': 'attribute',
                                'data_type': 'account_field'
                            })
                            break

                    # Check attribute values for emails
                    if re.match(email_pattern, attr_value):
                        found_accounts.append({
                            'file': file_path,
                            'format': 'xml',
                            'element_path': current_path,
                            'attribute': attr_name,
                            'value': attr_value,
                            'pattern_matched': 'email',
                            'type': 'attribute',
                            'data_type': 'email'
                        })

                # Recursively search child elements
                for child in element:
                    search_element(child, current_path)

            search_element(root)

        except Exception as e:
            self.logger.error(f"Error parsing XML file {file_path}: {e}")

        return found_accounts

    def _search_text_for_accounts(self, file_path: Path, email_pattern: str, account_patterns: List[str]) -> List[Dict[str, Any]]:
        """Search for account data in plain text files."""
        found_accounts = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # Search for emails
                email_matches = re.finditer(email_pattern, line)
                for match in email_matches:
                    found_accounts.append({
                        'file': file_path,
                        'format': 'text',
                        'line_number': line_num,
                        'value': match.group(),
                        'pattern_matched': 'email',
                        'full_line': line.strip(),
                        'data_type': 'email'
                    })

                # Search for account patterns
                for pattern in account_patterns:
                    # Look for key=value or key:value patterns
                    match = re.search(rf'({pattern})\s*[=:]\s*([^\s\n]+)', line, re.IGNORECASE)
                    if match:
                        found_accounts.append({
                            'file': file_path,
                            'format': 'text',
                            'line_number': line_num,
                            'key': match.group(1),
                            'value': match.group(2),
                            'pattern_matched': pattern,
                            'full_line': line.strip(),
                            'data_type': 'account_field'
                        })

        except Exception as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")

        return found_accounts
