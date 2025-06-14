"""
Enhanced IDE Detection and Management for AugmentCode Reset Tool
Handles multiple IDEs and provides precise AugmentCode detection and cleanup.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils import IDEDetector, OSDetector


class AugmentCodeIDEManager:
    """Manages AugmentCode detection and cleanup across multiple IDEs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.detected_installations = {}
        self.running_processes = []
        
    def perform_comprehensive_scan(self) -> Dict[str, Any]:
        """Perform a comprehensive scan for AugmentCode across all supported IDEs."""
        self.logger.info("Starting comprehensive AugmentCode IDE scan...")
        
        scan_results = {
            'running_processes': [],
            'ide_installations': {},
            'total_augmentcode_instances': 0,
            'recommendations': [],
            'warnings': []
        }
        
        try:
            # Step 1: Detect running processes
            self.logger.info("Scanning for running AugmentCode processes...")
            self.running_processes = IDEDetector.detect_running_augmentcode_processes()
            scan_results['running_processes'] = self.running_processes
            
            if self.running_processes:
                scan_results['warnings'].append(
                    f"Found {len(self.running_processes)} running processes with AugmentCode. "
                    "These should be closed before cleanup."
                )
            
            # Step 2: Detect IDE installations
            self.logger.info("Scanning IDE installations for AugmentCode...")
            self.detected_installations = IDEDetector.detect_ide_installations()
            scan_results['ide_installations'] = self.detected_installations
            
            # Step 3: Calculate totals and generate recommendations
            total_instances = len(self.running_processes)
            for ide_installs in self.detected_installations.values():
                total_instances += len(ide_installs)
            
            scan_results['total_augmentcode_instances'] = total_instances
            
            # Generate recommendations
            scan_results['recommendations'] = self._generate_recommendations()
            
            self.logger.info(f"Scan completed. Found {total_instances} AugmentCode instances across all IDEs.")
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive scan: {e}")
            scan_results['warnings'].append(f"Scan error: {str(e)}")
        
        return scan_results
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on scan results."""
        recommendations = []
        
        # Check for running processes
        if self.running_processes:
            ide_names = set(proc['ide'] for proc in self.running_processes)
            recommendations.append(
                f"Close the following IDEs before cleanup: {', '.join(ide_names)}"
            )
        
        # Check for multiple IDE installations
        active_ides = [ide for ide, installs in self.detected_installations.items() if installs]
        if len(active_ides) > 1:
            ide_names = [IDEDetector.SUPPORTED_IDES[ide]['name'] for ide in active_ides]
            recommendations.append(
                f"Multiple IDEs detected with AugmentCode: {', '.join(ide_names)}. "
                "Consider which one you want to keep AugmentCode data for."
            )
        
        # Check for specific IDE recommendations
        for ide_key, installs in self.detected_installations.items():
            if installs:
                ide_name = IDEDetector.SUPPORTED_IDES[ide_key]['name']
                total_files = sum(
                    len(install['augmentcode_data']['config_files']) + 
                    len(install['augmentcode_data']['workspace_data']) + 
                    len(install['augmentcode_data']['cache_files'])
                    for install in installs
                )
                if total_files > 50:
                    recommendations.append(
                        f"{ide_name} has extensive AugmentCode data ({total_files} files). "
                        "Cleanup may take longer."
                    )
        
        return recommendations
    
    def get_cleanup_targets(self, selected_ides: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get specific cleanup targets based on user selection."""
        if selected_ides is None:
            selected_ides = list(self.detected_installations.keys())
        
        cleanup_targets = {
            'processes_to_terminate': [],
            'files_to_clean': [],
            'directories_to_clean': [],
            'total_size_estimate': 0
        }
        
        # Add running processes for selected IDEs
        for process in self.running_processes:
            if process['ide_key'] in selected_ides:
                cleanup_targets['processes_to_terminate'].append(process)
        
        # Add files and directories for selected IDEs
        for ide_key in selected_ides:
            if ide_key in self.detected_installations:
                for installation in self.detected_installations[ide_key]:
                    data = installation['augmentcode_data']
                    
                    # Add all AugmentCode-related files
                    for file_list in [data['config_files'], data['workspace_data'], data['cache_files']]:
                        for file_info in file_list:
                            cleanup_targets['files_to_clean'].append(file_info)
                            cleanup_targets['total_size_estimate'] += file_info.get('size', 0)
                    
                    # Add extension directories
                    for ext_info in data['extensions']:
                        cleanup_targets['directories_to_clean'].append(ext_info)
        
        return cleanup_targets
    
    def safe_terminate_processes(self, force: bool = False) -> Dict[str, Any]:
        """Safely terminate AugmentCode processes with user confirmation."""
        if not self.running_processes:
            return {'status': 'success', 'message': 'No processes to terminate'}
        
        self.logger.info(f"Terminating {len(self.running_processes)} AugmentCode processes...")
        
        # Group processes by IDE for better user experience
        processes_by_ide = {}
        for process in self.running_processes:
            ide_name = process['ide']
            if ide_name not in processes_by_ide:
                processes_by_ide[ide_name] = []
            processes_by_ide[ide_name].append(process)
        
        # Terminate processes
        termination_results = IDEDetector.terminate_augmentcode_processes(
            self.running_processes, force=force
        )
        
        # Update our process list
        self.running_processes = []
        
        return {
            'status': 'success' if not termination_results['failed'] else 'partial',
            'results': termination_results,
            'processes_by_ide': processes_by_ide
        }
    
    def generate_detailed_report(self) -> str:
        """Generate a detailed report for user review."""
        if not self.detected_installations and not self.running_processes:
            return "No AugmentCode installations detected across any supported IDEs."
        
        return IDEDetector.generate_ide_report(
            self.detected_installations, 
            self.running_processes
        )
    
    def get_supported_ides(self) -> Dict[str, str]:
        """Get list of supported IDEs."""
        return {
            ide_key: ide_info['name'] 
            for ide_key, ide_info in IDEDetector.SUPPORTED_IDES.items()
        }
    
    def validate_ide_selection(self, selected_ides: List[str]) -> Dict[str, Any]:
        """Validate user's IDE selection and provide warnings."""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check if selected IDEs have AugmentCode data
        for ide_key in selected_ides:
            if ide_key not in IDEDetector.SUPPORTED_IDES:
                validation_result['errors'].append(f"Unknown IDE: {ide_key}")
                validation_result['valid'] = False
                continue
            
            if ide_key not in self.detected_installations or not self.detected_installations[ide_key]:
                ide_name = IDEDetector.SUPPORTED_IDES[ide_key]['name']
                validation_result['warnings'].append(
                    f"No AugmentCode data found for {ide_name}"
                )
        
        return validation_result
