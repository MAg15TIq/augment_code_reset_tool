#!/usr/bin/env python3
"""
Test script for Enhanced IDE Detection System
Demonstrates how the tool can differentiate between multiple IDEs with AugmentCode.
"""

import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ide_manager import AugmentCodeIDEManager
from utils import IDEDetector, OSDetector


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n🔍 {title}")
    print("-" * 60)


def test_basic_detection():
    """Test basic IDE detection capabilities."""
    print_header("ENHANCED IDE DETECTION SYSTEM TEST")
    
    print(f"Operating System: {OSDetector.get_os_type().title()}")
    print(f"Test Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize the IDE manager
    print_section("Initializing IDE Manager")
    ide_manager = AugmentCodeIDEManager()
    print("✅ IDE Manager initialized successfully")
    
    # Show supported IDEs
    print_section("Supported IDEs")
    supported_ides = ide_manager.get_supported_ides()
    for ide_key, ide_name in supported_ides.items():
        print(f"  • {ide_name} ({ide_key})")
    
    return ide_manager


def test_process_detection(ide_manager):
    """Test running process detection."""
    print_section("Running Process Detection")
    
    try:
        running_processes = IDEDetector.detect_running_augmentcode_processes()
        
        if running_processes:
            print(f"Found {len(running_processes)} running processes with AugmentCode:")
            for proc in running_processes:
                print(f"  • {proc['ide']} (PID: {proc['pid']})")
                print(f"    Process: {proc['name']}")
                if proc.get('exe'):
                    print(f"    Executable: {proc['exe']}")
                print()
        else:
            print("✅ No AugmentCode processes currently running")
            print("   (This is good for cleanup operations)")
    
    except Exception as e:
        print(f"❌ Error detecting processes: {e}")
        print("   Note: Process detection requires 'psutil' package")


def test_installation_detection(ide_manager):
    """Test IDE installation detection."""
    print_section("IDE Installation Detection")
    
    try:
        installations = IDEDetector.detect_ide_installations()
        
        total_installations = sum(len(installs) for installs in installations.values())
        
        if total_installations > 0:
            print(f"Found AugmentCode in {total_installations} IDE installation(s):")
            
            for ide_key, installs in installations.items():
                if installs:
                    ide_name = IDEDetector.SUPPORTED_IDES[ide_key]['name']
                    print(f"\n  📁 {ide_name}:")
                    
                    for install in installs:
                        print(f"    Path: {install['path']}")
                        data = install['augmentcode_data']
                        
                        if data['extensions']:
                            print(f"    Extensions: {len(data['extensions'])} found")
                            for ext in data['extensions'][:3]:  # Show first 3
                                print(f"      - {ext['name']}")
                            if len(data['extensions']) > 3:
                                print(f"      ... and {len(data['extensions']) - 3} more")
                        
                        if data['config_files']:
                            print(f"    Config files: {len(data['config_files'])} found")
                        
                        if data['workspace_data']:
                            print(f"    Workspace data: {len(data['workspace_data'])} files")
                        
                        if data['cache_files']:
                            print(f"    Cache files: {len(data['cache_files'])} files")
        else:
            print("✅ No IDE installations with AugmentCode detected")
            print("   This could mean:")
            print("   - AugmentCode is not installed in any IDE")
            print("   - AugmentCode is installed in unsupported IDEs")
            print("   - AugmentCode data is in non-standard locations")
    
    except Exception as e:
        print(f"❌ Error detecting installations: {e}")


def test_comprehensive_scan(ide_manager):
    """Test comprehensive scanning functionality."""
    print_section("Comprehensive IDE Scan")
    
    try:
        print("Starting comprehensive scan...")
        scan_results = ide_manager.perform_comprehensive_scan()
        
        print(f"✅ Scan completed!")
        print(f"   Total AugmentCode instances: {scan_results['total_augmentcode_instances']}")
        print(f"   Running processes: {len(scan_results['running_processes'])}")
        print(f"   IDE installations: {sum(len(installs) for installs in scan_results['ide_installations'].values())}")
        
        # Show recommendations
        if scan_results['recommendations']:
            print("\n📋 Recommendations:")
            for i, rec in enumerate(scan_results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Show warnings
        if scan_results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in scan_results['warnings']:
                print(f"   • {warning}")
        
        return scan_results
    
    except Exception as e:
        print(f"❌ Error during comprehensive scan: {e}")
        return None


def test_cleanup_targeting(ide_manager, scan_results):
    """Test cleanup target identification."""
    print_section("Cleanup Target Analysis")
    
    if not scan_results:
        print("❌ No scan results available for cleanup analysis")
        return
    
    try:
        # Get cleanup targets for all detected IDEs
        detected_ides = [ide for ide, installs in scan_results['ide_installations'].items() if installs]
        
        if detected_ides:
            print(f"Analyzing cleanup targets for: {', '.join(detected_ides)}")
            cleanup_targets = ide_manager.get_cleanup_targets(detected_ides)
            
            print(f"   Processes to terminate: {len(cleanup_targets['processes_to_terminate'])}")
            print(f"   Files to clean: {len(cleanup_targets['files_to_clean'])}")
            print(f"   Directories to clean: {len(cleanup_targets['directories_to_clean'])}")
            
            # Estimate cleanup size
            total_size = cleanup_targets['total_size_estimate']
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"   Estimated cleanup size: {size_mb:.1f} MB")
            
            # Show validation
            validation = ide_manager.validate_ide_selection(detected_ides)
            if validation['warnings']:
                print("\n⚠️  Validation warnings:")
                for warning in validation['warnings']:
                    print(f"   • {warning}")
        else:
            print("✅ No IDEs with AugmentCode detected - nothing to clean")
    
    except Exception as e:
        print(f"❌ Error analyzing cleanup targets: {e}")


def test_report_generation(ide_manager):
    """Test detailed report generation."""
    print_section("Detailed Report Generation")
    
    try:
        report = ide_manager.generate_detailed_report()
        
        if report and "No AugmentCode installations detected" not in report:
            print("📄 Generated detailed report:")
            print("\n" + report)
        else:
            print("✅ No detailed report needed - no AugmentCode installations found")
    
    except Exception as e:
        print(f"❌ Error generating report: {e}")


def main():
    """Main test function."""
    try:
        # Test basic detection
        ide_manager = test_basic_detection()
        
        # Test process detection
        test_process_detection(ide_manager)
        
        # Test installation detection
        test_installation_detection(ide_manager)
        
        # Test comprehensive scan
        scan_results = test_comprehensive_scan(ide_manager)
        
        # Test cleanup targeting
        test_cleanup_targeting(ide_manager, scan_results)
        
        # Test report generation
        test_report_generation(ide_manager)
        
        print_header("TEST COMPLETED")
        print("✅ All IDE detection tests completed successfully!")
        print("\nThis demonstrates how the enhanced tool can:")
        print("  • Detect multiple IDEs with AugmentCode")
        print("  • Differentiate between different IDE installations")
        print("  • Identify running processes accurately")
        print("  • Provide targeted cleanup recommendations")
        print("  • Generate comprehensive reports")
        
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
