"""
Free AugmentCode Data Cleaner - Account Data Cleaner
Specialized module for cleaning email addresses and user account data.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import json

from backup_manager import BackupManager
from config_manager import ConfigManager
from utils import SafeFileOperations


class AccountDataCleaner:
    """Specialized cleaner for email addresses and user account data."""
    
    def __init__(self, backup_manager: BackupManager):
        self.logger = logging.getLogger('FreeAugmentCode.AccountDataCleaner')
        self.backup_manager = backup_manager
        self.config_manager = ConfigManager()
    
    def discover_account_data(self, augmentcode_paths: List[Path]) -> Dict[str, Any]:
        """Discover email addresses and account data in AugmentCode files."""
        discovery_results = {
            'email_addresses': set(),
            'user_identifiers': set(),
            'account_files': [],
            'total_references': 0
        }
        
        for path in augmentcode_paths:
            if not path.exists():
                continue
                
            # Search configuration files
            config_files = self._find_config_files(path)
            for config_file in config_files:
                account_data = self._extract_account_data_from_file(config_file)
                if account_data:
                    discovery_results['account_files'].append({
                        'file': config_file,
                        'data': account_data
                    })
                    discovery_results['email_addresses'].update(account_data.get('emails', []))
                    discovery_results['user_identifiers'].update(account_data.get('user_ids', []))
        
        # Convert sets to lists for JSON serialization
        discovery_results['email_addresses'] = list(discovery_results['email_addresses'])
        discovery_results['user_identifiers'] = list(discovery_results['user_identifiers'])
        discovery_results['total_references'] = len(discovery_results['email_addresses']) + len(discovery_results['user_identifiers'])
        
        self.logger.info(f"Account discovery complete: {len(discovery_results['email_addresses'])} emails, "
                        f"{len(discovery_results['user_identifiers'])} user IDs found")
        
        return discovery_results
    
    def _find_config_files(self, base_path: Path) -> List[Path]:
        """Find configuration files that might contain account data."""
        config_files = []
        config_extensions = ['.json', '.ini', '.cfg', '.conf', '.xml', '.txt', '.log']
        
        try:
            for file_path in base_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in config_extensions:
                    # Skip obviously non-config files
                    if any(skip in file_path.name.lower() for skip in ['temp', 'cache', 'backup']):
                        continue
                    config_files.append(file_path)
        except PermissionError:
            self.logger.warning(f"Permission denied accessing {base_path}")
        
        return config_files
    
    def _extract_account_data_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Extract email addresses and user identifiers from a file."""
        account_data = {
            'emails': [],
            'user_ids': [],
            'usernames': []
        }
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content)
            account_data['emails'] = list(set(emails))  # Remove duplicates
            
            # Extract potential usernames (alphanumeric strings that might be usernames)
            username_patterns = [
                r'"username":\s*"([^"]+)"',
                r'"user":\s*"([^"]+)"',
                r'"login":\s*"([^"]+)"',
                r'"account":\s*"([^"]+)"',
                r'username\s*[=:]\s*([^\s\n]+)',
                r'user\s*[=:]\s*([^\s\n]+)',
                r'login\s*[=:]\s*([^\s\n]+)'
            ]
            
            for pattern in username_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                account_data['usernames'].extend(matches)
            
            # Remove duplicates and filter out obvious non-usernames
            account_data['usernames'] = list(set([
                username for username in account_data['usernames']
                if len(username) > 2 and not username.isdigit()
            ]))
            
            # Combine usernames into user_ids
            account_data['user_ids'] = account_data['usernames']
            
        except Exception as e:
            self.logger.error(f"Error extracting account data from {file_path}: {e}")
        
        return account_data
    
    def clean_account_data(self, backup_dir: Path, cleanup_options: Dict[str, Any]) -> bool:
        """Clean account data based on specified options."""
        success = True
        
        target_email = cleanup_options.get('target_email', '')
        remove_all_accounts = cleanup_options.get('remove_all_accounts', False)
        account_files = cleanup_options.get('account_files', [])
        
        self.logger.info(f"Starting account data cleanup. Target email: {target_email}")
        
        for file_info in account_files:
            file_path = file_info['file']
            account_data = file_info['data']
            
            # Backup file first
            backup_success = self.backup_manager.backup_file(
                file_path, backup_dir, f"account_files/{file_path.name}"
            )
            if not backup_success:
                self.logger.error(f"Failed to backup {file_path}")
                success = False
                continue
            
            # Clean the file
            clean_success = self._clean_account_file(
                file_path, account_data, target_email, remove_all_accounts
            )
            if not clean_success:
                success = False
        
        return success
    
    def _clean_account_file(self, file_path: Path, account_data: Dict[str, Any], 
                           target_email: str, remove_all: bool) -> bool:
        """Clean account data from a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            
            if remove_all:
                # Remove all found emails and usernames
                for email in account_data.get('emails', []):
                    content = content.replace(email, '[REMOVED]')
                
                for username in account_data.get('usernames', []):
                    # Be careful not to replace common words
                    if len(username) > 4:
                        content = re.sub(rf'\b{re.escape(username)}\b', '[REMOVED]', content)
            
            elif target_email:
                # Remove only the specific email
                content = content.replace(target_email, '[REMOVED]')
                
                # Also remove any usernames that match the email prefix
                email_prefix = target_email.split('@')[0]
                if len(email_prefix) > 3:
                    content = re.sub(rf'\b{re.escape(email_prefix)}\b', '[REMOVED]', content)
            
            # Write back if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"Cleaned account data from {file_path}")
                return True
            else:
                self.logger.info(f"No changes needed for {file_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error cleaning account file {file_path}: {e}")
            return False
    
    def generate_account_report(self, discovery_results: Dict[str, Any]) -> str:
        """Generate a human-readable report of discovered account data."""
        report_lines = []
        
        report_lines.append("=== ACCOUNT DATA DISCOVERY REPORT ===")
        report_lines.append("")
        
        # Summary
        email_count = len(discovery_results['email_addresses'])
        user_id_count = len(discovery_results['user_identifiers'])
        file_count = len(discovery_results['account_files'])
        
        report_lines.append(f"Summary:")
        report_lines.append(f"  Email addresses found: {email_count}")
        report_lines.append(f"  User identifiers found: {user_id_count}")
        report_lines.append(f"  Files containing account data: {file_count}")
        report_lines.append("")
        
        # Email addresses
        if discovery_results['email_addresses']:
            report_lines.append("Found Email Addresses:")
            for email in discovery_results['email_addresses']:
                report_lines.append(f"  • {email}")
            report_lines.append("")
        
        # User identifiers
        if discovery_results['user_identifiers']:
            report_lines.append("Found User Identifiers:")
            for user_id in discovery_results['user_identifiers'][:10]:  # Limit to first 10
                report_lines.append(f"  • {user_id}")
            if len(discovery_results['user_identifiers']) > 10:
                report_lines.append(f"  ... and {len(discovery_results['user_identifiers']) - 10} more")
            report_lines.append("")
        
        # Files
        if discovery_results['account_files']:
            report_lines.append("Files Containing Account Data:")
            for file_info in discovery_results['account_files']:
                file_path = file_info['file']
                data = file_info['data']
                report_lines.append(f"  File: {file_path}")
                if data['emails']:
                    report_lines.append(f"    Emails: {len(data['emails'])}")
                if data['user_ids']:
                    report_lines.append(f"    User IDs: {len(data['user_ids'])}")
                report_lines.append("")
        
        return "\n".join(report_lines)
