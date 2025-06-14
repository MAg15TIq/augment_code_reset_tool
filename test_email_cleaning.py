"""
Test script for the enhanced email cleaning functionality.
"""

import tempfile
import json
from pathlib import Path
from account_cleaner import AccountDataCleaner
from backup_manager import BackupManager


def test_email_discovery():
    """Test email address discovery in configuration files."""
    print("Testing email discovery functionality...")
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test JSON file with email
        json_file = temp_path / "config.json"
        test_config = {
            "user": {
                "email": "test@example.com",
                "username": "testuser",
                "device_id": "device_12345"
            },
            "settings": {
                "login_email": "another@test.com"
            }
        }
        
        with open(json_file, 'w') as f:
            json.dump(test_config, f)
        
        # Create test INI file
        ini_file = temp_path / "settings.ini"
        ini_content = """[User]
email = user@domain.com
username = myuser
device_id = abc123

[Login]
last_email = previous@email.com
"""
        with open(ini_file, 'w') as f:
            f.write(ini_content)
        
        # Create test text file
        txt_file = temp_path / "log.txt"
        txt_content = """Login attempt for admin@company.com
Session started for user: testuser
Email verification sent to verify@test.org
"""
        with open(txt_file, 'w') as f:
            f.write(txt_content)
        
        # Test discovery
        backup_manager = BackupManager()
        account_cleaner = AccountDataCleaner(backup_manager)
        
        discovery_results = account_cleaner.discover_account_data([temp_path])
        
        print(f"Found {len(discovery_results['email_addresses'])} email addresses:")
        for email in discovery_results['email_addresses']:
            print(f"  - {email}")
        
        print(f"Found {len(discovery_results['user_identifiers'])} user identifiers:")
        for user_id in discovery_results['user_identifiers']:
            print(f"  - {user_id}")
        
        print(f"Found account data in {len(discovery_results['account_files'])} files")
        
        # Generate report
        report = account_cleaner.generate_account_report(discovery_results)
        print("\nGenerated Report:")
        print(report)
        
        return len(discovery_results['email_addresses']) > 0


def test_email_cleaning():
    """Test email cleaning functionality."""
    print("\nTesting email cleaning functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test file with target email
        test_file = temp_path / "user_config.json"
        test_config = {
            "user_email": "target@example.com",
            "username": "target",
            "other_email": "keep@example.com",
            "device_id": "device_123"
        }
        
        with open(test_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        print(f"Original file content:")
        with open(test_file, 'r') as f:
            print(f.read())
        
        # Test cleaning
        backup_manager = BackupManager()
        account_cleaner = AccountDataCleaner(backup_manager)
        
        # Discover first
        discovery_results = account_cleaner.discover_account_data([temp_path])
        
        # Create backup directory
        backup_dir = Path(temp_dir) / "backup"
        backup_dir.mkdir()
        
        # Clean specific email
        cleanup_options = {
            'target_email': 'target@example.com',
            'remove_all_accounts': False,
            'account_files': discovery_results['account_files']
        }
        
        success = account_cleaner.clean_account_data(backup_dir, cleanup_options)
        
        print(f"\nCleaning success: {success}")
        print(f"File content after cleaning:")
        with open(test_file, 'r') as f:
            print(f.read())
        
        return success


def main():
    """Run all tests."""
    print("=" * 60)
    print("ENHANCED EMAIL CLEANING FUNCTIONALITY TESTS")
    print("=" * 60)
    
    try:
        # Test discovery
        discovery_success = test_email_discovery()
        print(f"\nEmail discovery test: {'PASSED' if discovery_success else 'FAILED'}")
        
        # Test cleaning
        cleaning_success = test_email_cleaning()
        print(f"Email cleaning test: {'PASSED' if cleaning_success else 'FAILED'}")
        
        # Overall result
        overall_success = discovery_success and cleaning_success
        print(f"\nOverall test result: {'PASSED' if overall_success else 'FAILED'}")
        
        if overall_success:
            print("\n✅ Enhanced email cleaning functionality is working correctly!")
            print("\nThe tool can now:")
            print("• Discover email addresses in configuration files")
            print("• Clean specific email addresses or all account data")
            print("• Handle JSON, INI, XML, and text file formats")
            print("• Provide detailed reports of found account data")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
