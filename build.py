#!/usr/bin/env python3
"""
Build script for Free AugmentCode Data Cleaner
Creates a standalone executable using PyInstaller.
"""

import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            return False


def build_executable():
    """Build the standalone executable."""
    print("Building Free AugmentCode Data Cleaner executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",           # Create a single executable file
        "--windowed",          # Hide console window (GUI app)
        "--name", "FreeAugmentCodeCleaner",  # Executable name
        "--icon", "icon.ico" if Path("icon.ico").exists() else None,  # Icon (if available)
        "main.py"
    ]
    
    # Remove None values
    cmd = [arg for arg in cmd if arg is not None]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print("✓ Build completed successfully!")
        
        # Check if executable was created
        dist_dir = Path("dist")
        if dist_dir.exists():
            executables = list(dist_dir.glob("FreeAugmentCodeCleaner*"))
            if executables:
                exe_path = executables[0]
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✓ Executable created: {exe_path} ({size_mb:.1f} MB)")
                return True
        
        print("✗ Executable not found in dist directory")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False


def cleanup_build_files():
    """Clean up build artifacts."""
    print("Cleaning up build files...")
    
    cleanup_dirs = ["build", "__pycache__"]
    cleanup_files = ["*.spec"]
    
    for dir_name in cleanup_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_name}/")
    
    for pattern in cleanup_files:
        for file_path in Path(".").glob(pattern):
            file_path.unlink()
            print(f"  Removed: {file_path}")


def main():
    """Main build process."""
    print("=" * 60)
    print("FREE AUGMENTCODE DATA CLEANER - BUILD SCRIPT")
    print("=" * 60)
    print()
    
    # Check PyInstaller
    if not check_pyinstaller():
        print("Cannot proceed without PyInstaller")
        return False
    
    print()
    
    # Build executable
    success = build_executable()
    
    print()
    
    # Cleanup
    cleanup_build_files()
    
    print()
    print("=" * 60)
    
    if success:
        print("🎉 Build completed successfully!")
        print("The executable is available in the 'dist' directory.")
        print()
        print("Usage:")
        print("  1. Copy the executable to your desired location")
        print("  2. Run the executable to start the GUI")
        print("  3. Follow the on-screen instructions")
    else:
        print("❌ Build failed. Please check the errors above.")
    
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
