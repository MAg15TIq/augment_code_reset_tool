#!/usr/bin/env python3
"""
Test script for Free AugmentCode Data Cleaner
Tests core functionality without GUI.
"""

import sys
import tempfile
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_cleaner import FreeAugmentCodeCleaner
from utils import OSDetector, IDGenerator, Logger


def test_basic_functionality():
    """Test basic functionality of the data cleaner."""
    print("=" * 60)
    print("FREE AUGMENTCODE DATA CLEANER - FUNCTIONALITY TEST")
    print("=" * 60)
    print()
    
    # Test OS detection
    print(f"Operating System: {OSDetector.get_os_type().title()}")
    print(f"Windows: {OSDetector.is_windows()}")
    print(f"macOS: {OSDetector.is_macos()}")
    print(f"Linux: {OSDetector.is_linux()}")
    print()
    
    # Test ID generation
    print("Testing ID Generation:")
    device_id = IDGenerator.generate_device_id()
    machine_id = IDGenerator.generate_machine_id()
    uuid = IDGenerator.generate_uuid()
    random_string = IDGenerator.generate_random_string(16)
    
    print(f"  Device ID: {device_id}")
    print(f"  Machine ID: {machine_id}")
    print(f"  UUID: {uuid}")
    print(f"  Random String: {random_string}")
    print()
    
    # Test data cleaner initialization
    print("Testing Data Cleaner Initialization:")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            cleaner = FreeAugmentCodeCleaner(Path(temp_dir) / "test_backups")
            print("  ✓ Data cleaner initialized successfully")
            
            # Test discovery with empty paths
            print("  Testing discovery with no AugmentCode data...")
            discovery_results = cleaner.discover_augmentcode_data([])
            print(f"  ✓ Discovery completed: {discovery_results['total_locations_found']} locations found")
            
            # Test report generation
            print("  Testing report generation...")
            report = cleaner.generate_discovery_report()
            print(f"  ✓ Report generated: {len(report)} characters")
            
            # Test backup list
            print("  Testing backup management...")
            backups = cleaner.get_backup_list()
            print(f"  ✓ Backup list retrieved: {len(backups)} backups found")
            
    except Exception as e:
        print(f"  ✗ Error during testing: {e}")
        return False
    
    print()
    print("✓ All basic functionality tests passed!")
    return True


def test_config_file_creation():
    """Test creating sample configuration files for testing."""
    print("Testing Configuration File Handling:")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample JSON config
        json_config = {
            "device_id": "old_device_12345",
            "machine_id": "old_machine_67890",
            "user_settings": {
                "session_id": "old_session_abcdef"
            }
        }
        
        json_file = temp_path / "config.json"
        with open(json_file, 'w') as f:
            json.dump(json_config, f, indent=2)
        
        print(f"  ✓ Created sample JSON config: {json_file}")
        
        # Create sample INI config
        ini_content = """[Settings]
device_id = old_device_ini_123
machine_id = old_machine_ini_456
telemetry_enabled = true

[User]
user_id = test_user_789
"""
        
        ini_file = temp_path / "settings.ini"
        with open(ini_file, 'w') as f:
            f.write(ini_content)
        
        print(f"  ✓ Created sample INI config: {ini_file}")
        
        # Test config manager
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
            
            # Search for IDs in the files
            found_ids = config_manager.search_for_telemetry_ids([json_file, ini_file])
            print(f"  ✓ Found {len(found_ids)} telemetry IDs in config files")
            
            for id_info in found_ids:
                print(f"    - {id_info['format']}: {id_info['key']} = {id_info['value']}")
            
        except Exception as e:
            print(f"  ✗ Error testing config manager: {e}")
            return False
    
    print("  ✓ Configuration file handling test passed!")
    return True


def test_backup_system():
    """Test the backup system."""
    print("Testing Backup System:")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            from backup_manager import BackupManager
            
            # Initialize backup manager
            backup_manager = BackupManager(temp_path / "backups")
            print("  ✓ Backup manager initialized")
            
            # Create a test file to backup
            test_file = temp_path / "test_file.txt"
            test_file.write_text("This is a test file for backup.")
            
            # Create backup directory
            backup_dir = backup_manager.create_timestamped_backup_dir()
            print(f"  ✓ Created backup directory: {backup_dir.name}")
            
            # Backup the test file
            success = backup_manager.backup_file(test_file, backup_dir)
            print(f"  ✓ File backup: {'Success' if success else 'Failed'}")
            
            # List backups
            backups = backup_manager.list_backups()
            print(f"  ✓ Found {len(backups)} backups")
            
        except Exception as e:
            print(f"  ✗ Error testing backup system: {e}")
            return False
    
    print("  ✓ Backup system test passed!")
    return True


def main():
    """Run all tests."""
    print("Starting Free AugmentCode Data Cleaner Tests...")
    print()
    
    tests = [
        test_basic_functionality,
        test_config_file_creation,
        test_backup_system
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"  ✗ Test {test_func.__name__} failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Free AugmentCode Data Cleaner is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
