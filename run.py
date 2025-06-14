#!/usr/bin/env python3
"""
Simple launcher for Free AugmentCode Data Cleaner
Handles common startup issues and provides helpful error messages.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        print("Please upgrade Python and try again.")
        return False
    return True


def check_dependencies():
    """Check if required modules are available."""
    required_modules = [
        'tkinter',
        'sqlite3',
        'pathlib',
        'threading',
        'logging',
        'json',
        'configparser'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Error: Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print()
        print("Please install the missing modules and try again.")
        if 'tkinter' in missing_modules:
            print("Note: tkinter is usually included with Python.")
            print("On Linux, you may need to install python3-tk package.")
        return False
    
    return True


def check_permissions():
    """Check if we have necessary permissions."""
    current_dir = Path(__file__).parent
    
    # Check if we can write to current directory (for logs)
    try:
        test_file = current_dir / "test_write_permission.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        print("⚠️  Warning: Limited write permissions in current directory.")
        print("Some features (like logging) may not work properly.")
        print("Consider running as administrator or from a writable location.")
    
    return True


def main():
    """Main launcher function."""
    print("Free AugmentCode Data Cleaner - Launcher")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return False
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return False
    
    # Check permissions
    check_permissions()
    
    # Try to import and run the main application
    try:
        print("Starting Free AugmentCode Data Cleaner...")
        print()
        
        # Import main application
        from main import main as run_app
        
        # Run the application
        run_app()
        
        return True
        
    except ImportError as e:
        print(f"❌ Error: Failed to import application modules: {e}")
        print("Please ensure all files are in the same directory.")
        input("Press Enter to exit...")
        return False
        
    except Exception as e:
        print(f"❌ Error: Application failed to start: {e}")
        print()
        print("Troubleshooting tips:")
        print("1. Ensure all Python files are in the same directory")
        print("2. Check that you have the required permissions")
        print("3. Try running as administrator (Windows) or with sudo (Linux/macOS)")
        print("4. Verify that AugmentCode is not currently running")
        print()
        input("Press Enter to exit...")
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        input("Press Enter to exit...")
    
    sys.exit(0)
