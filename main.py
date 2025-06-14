"""
Free AugmentCode Data Cleaner - Main GUI Application
A comprehensive tool for cleaning AugmentCode data to enable unlimited logins.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
import sys

from data_cleaner import FreeAugmentCodeCleaner, DataCleanerStatus
from utils import OSDetector


class FreeAugmentCodeGUI:
    """Main GUI application for the Free AugmentCode Data Cleaner."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Free AugmentCode Data Cleaner v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Initialize data cleaner
        self.cleaner = FreeAugmentCodeCleaner()
        self.discovery_complete = False
        self.cleanup_thread = None
        
        # GUI variables
        self.augmentcode_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        # Cleanup options
        self.modify_telemetry_var = tk.BooleanVar(value=True)
        self.clean_database_var = tk.BooleanVar(value=True)
        self.clean_workspace_var = tk.BooleanVar(value=True)
        self.clean_account_data_var = tk.BooleanVar(value=True)
        self.backup_enabled_var = tk.BooleanVar(value=True)

        # Email-specific options
        self.target_email_var = tk.StringVar()
        self.remove_all_accounts_var = tk.BooleanVar(value=False)
        
        self.setup_gui()
        self.update_status_loop()
    
    def setup_gui(self):
        """Setup the main GUI layout."""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Main")
        self.setup_main_tab(main_frame)
        
        # Discovery tab
        discovery_frame = ttk.Frame(notebook)
        notebook.add(discovery_frame, text="Discovery")
        self.setup_discovery_tab(discovery_frame)
        
        # Backup tab
        backup_frame = ttk.Frame(notebook)
        notebook.add(backup_frame, text="Backups")
        self.setup_backup_tab(backup_frame)
        
        # About tab
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="About")
        self.setup_about_tab(about_frame)
    
    def setup_main_tab(self, parent):
        """Setup the main operations tab."""
        # Title
        title_label = ttk.Label(parent, text="Free AugmentCode Data Cleaner", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # AugmentCode path selection
        path_frame = ttk.LabelFrame(parent, text="AugmentCode Location", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X)
        
        ttk.Label(path_entry_frame, text="Path:").pack(side=tk.LEFT)
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.augmentcode_path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Button(path_entry_frame, text="Browse", 
                  command=self.browse_augmentcode_path).pack(side=tk.RIGHT)
        ttk.Button(path_entry_frame, text="Auto-Detect", 
                  command=self.auto_detect_path).pack(side=tk.RIGHT, padx=(0, 5))
        
        # Cleanup options
        options_frame = ttk.LabelFrame(parent, text="Cleanup Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(options_frame, text="Modify Telemetry IDs (Device/Machine IDs)",
                       variable=self.modify_telemetry_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Clean Database (Remove 'augment' records)",
                       variable=self.clean_database_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Clean Workspace Storage",
                       variable=self.clean_workspace_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Clean Account Data (Email addresses & user data)",
                       variable=self.clean_account_data_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Create Backup Before Cleaning",
                       variable=self.backup_enabled_var).pack(anchor=tk.W)

        # Email-specific options
        email_frame = ttk.LabelFrame(parent, text="Email-Specific Options", padding=10)
        email_frame.pack(fill=tk.X, padx=10, pady=5)

        email_entry_frame = ttk.Frame(email_frame)
        email_entry_frame.pack(fill=tk.X)

        ttk.Label(email_entry_frame, text="Target Email (leave empty to remove all):").pack(side=tk.LEFT)
        email_entry = ttk.Entry(email_entry_frame, textvariable=self.target_email_var, width=40)
        email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        ttk.Checkbutton(email_frame, text="Remove ALL account data (not just target email)",
                       variable=self.remove_all_accounts_var).pack(anchor=tk.W, pady=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Discover AugmentCode Data", 
                  command=self.start_discovery).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Run Cleanup", 
                  command=self.start_cleanup).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Generate Report", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress and status
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W)
        
        # Log area
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_discovery_tab(self, parent):
        """Setup the discovery results tab."""
        ttk.Label(parent, text="Discovery Results", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        self.discovery_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD)
        self.discovery_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Refresh Discovery", 
                  command=self.start_discovery).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save Report", 
                  command=self.save_discovery_report).pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_backup_tab(self, parent):
        """Setup the backup management tab."""
        ttk.Label(parent, text="Backup Management", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Backup list
        list_frame = ttk.LabelFrame(parent, text="Available Backups", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for backup list
        columns = ("Name", "Date", "Items", "Size")
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=150)
        
        backup_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Backup buttons
        backup_button_frame = ttk.Frame(parent)
        backup_button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(backup_button_frame, text="Refresh List", 
                  command=self.refresh_backup_list).pack(side=tk.LEFT)
        ttk.Button(backup_button_frame, text="Restore Selected", 
                  command=self.restore_backup).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(backup_button_frame, text="Delete Selected", 
                  command=self.delete_backup).pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_about_tab(self, parent):
        """Setup the about tab."""
        about_text = """
Free AugmentCode Data Cleaner v1.1 - Enhanced Email Support

A comprehensive tool for cleaning AugmentCode-related data to enable
unlimited logins with different accounts on the same computer.

Features:
• Automatic discovery of AugmentCode data locations
• Safe backup system before any modifications
• Telemetry ID modification (Device/Machine IDs)
• Database cleaning (removes 'augment' keyword records)
• Email address and account data cleaning
• Workspace storage management
• Cross-platform support (Windows, macOS, Linux)

Safety Features:
• Comprehensive backup system with timestamped backups
• Detailed logging of all operations
• Confirmation dialogs for destructive operations
• Restore functionality from backups

Disclaimer:
This tool is provided as-is for educational and personal use only. 
Always backup your data before use. The authors are not responsible 
for any data loss or issues that may arise from using this tool.

Operating System: {}
        """.format(OSDetector.get_os_type().title())
        
        about_label = ttk.Label(parent, text=about_text, justify=tk.LEFT, wraplength=600)
        about_label.pack(padx=20, pady=20)
    
    def browse_augmentcode_path(self):
        """Browse for AugmentCode installation directory."""
        directory = filedialog.askdirectory(title="Select AugmentCode Directory")
        if directory:
            self.augmentcode_path_var.set(directory)
    
    def auto_detect_path(self):
        """Auto-detect AugmentCode installation path."""
        self.log_message("Auto-detecting AugmentCode paths...")
        
        def detect_thread():
            try:
                discovery_results = self.cleaner.discover_augmentcode_data()
                paths = discovery_results.get('augmentcode_paths', [])
                
                if paths:
                    # Use the first found path
                    self.augmentcode_path_var.set(str(paths[0]))
                    self.log_message(f"Auto-detected path: {paths[0]}")
                    if len(paths) > 1:
                        self.log_message(f"Found {len(paths)} additional paths. Check Discovery tab for details.")
                else:
                    self.log_message("No AugmentCode paths found automatically. Please browse manually.")
                    messagebox.showwarning("Auto-Detection", 
                                         "No AugmentCode installation found automatically.\n"
                                         "Please use the Browse button to select the directory manually.")
            except Exception as e:
                self.log_message(f"Error during auto-detection: {str(e)}")
                messagebox.showerror("Error", f"Auto-detection failed: {str(e)}")
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def start_discovery(self):
        """Start the discovery process."""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            messagebox.showwarning("Operation in Progress", 
                                 "Please wait for the current operation to complete.")
            return
        
        self.log_message("Starting AugmentCode data discovery...")
        
        def discovery_thread():
            try:
                custom_paths = []
                if self.augmentcode_path_var.get().strip():
                    custom_paths = [Path(self.augmentcode_path_var.get().strip())]
                
                discovery_results = self.cleaner.discover_augmentcode_data(custom_paths)
                self.discovery_complete = True
                
                # Update discovery tab
                report = self.cleaner.generate_discovery_report()
                self.root.after(0, lambda: self.update_discovery_display(report))
                
                self.log_message("Discovery completed successfully!")
                
            except Exception as e:
                error_msg = f"Discovery failed: {str(e)}"
                self.log_message(error_msg)
                self.root.after(0, lambda: messagebox.showerror("Discovery Error", error_msg))
        
        self.cleanup_thread = threading.Thread(target=discovery_thread, daemon=True)
        self.cleanup_thread.start()
    
    def start_cleanup(self):
        """Start the cleanup process."""
        if not self.discovery_complete:
            messagebox.showwarning("Discovery Required", 
                                 "Please run discovery first to identify AugmentCode data locations.")
            return
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            messagebox.showwarning("Operation in Progress", 
                                 "Please wait for the current operation to complete.")
            return
        
        # Confirmation dialog
        if not self.backup_enabled_var.get():
            if not messagebox.askyesno("No Backup Warning", 
                                     "You have disabled backup creation. This is not recommended.\n"
                                     "Are you sure you want to proceed without backup?"):
                return
        
        confirm_msg = "This will modify AugmentCode data based on your selected options:\n\n"
        if self.modify_telemetry_var.get():
            confirm_msg += "• Modify telemetry IDs\n"
        if self.clean_database_var.get():
            confirm_msg += "• Clean database records\n"
        if self.clean_workspace_var.get():
            confirm_msg += "• Clean workspace storage\n"
        if self.clean_account_data_var.get():
            target_email = self.target_email_var.get().strip()
            if target_email:
                confirm_msg += f"• Clean account data for email: {target_email}\n"
            elif self.remove_all_accounts_var.get():
                confirm_msg += "• Remove ALL account data\n"
            else:
                confirm_msg += "• Clean account data\n"

        confirm_msg += "\nDo you want to proceed?"
        
        if not messagebox.askyesno("Confirm Cleanup", confirm_msg):
            return
        
        self.log_message("Starting data cleanup...")
        
        cleanup_options = {
            'modify_telemetry_ids': self.modify_telemetry_var.get(),
            'clean_database': self.clean_database_var.get(),
            'clean_workspace': self.clean_workspace_var.get(),
            'clean_account_data': self.clean_account_data_var.get(),
            'backup_enabled': self.backup_enabled_var.get(),
            'remove_augment_records': True,
            'remove_account_data': self.clean_account_data_var.get(),
            'clear_session_data': True,
            'workspace_items_to_clean': ['cache_folder', 'temp_file', 'session_file'],
            'remove_lock_files': True,
            'target_email': self.target_email_var.get().strip(),
            'remove_all_accounts': self.remove_all_accounts_var.get()
        }
        
        self.cleanup_thread = self.cleaner.perform_cleanup_async(cleanup_options)
    
    def generate_report(self):
        """Generate and display discovery report."""
        if not self.discovery_complete:
            messagebox.showwarning("Discovery Required", 
                                 "Please run discovery first to generate a report.")
            return
        
        report = self.cleaner.generate_discovery_report()
        self.update_discovery_display(report)
        
        # Switch to discovery tab
        notebook = self.root.children['!notebook']
        notebook.select(1)  # Discovery tab
    
    def save_discovery_report(self):
        """Save discovery report to file."""
        if not self.discovery_complete:
            messagebox.showwarning("No Report", "No discovery report available to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Discovery Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                report = self.cleaner.generate_discovery_report()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.log_message(f"Report saved to: {file_path}")
                messagebox.showinfo("Report Saved", f"Discovery report saved to:\n{file_path}")
            except Exception as e:
                error_msg = f"Failed to save report: {str(e)}"
                self.log_message(error_msg)
                messagebox.showerror("Save Error", error_msg)
    
    def refresh_backup_list(self):
        """Refresh the backup list display."""
        try:
            # Clear existing items
            for item in self.backup_tree.get_children():
                self.backup_tree.delete(item)
            
            # Get backup list
            backups = self.cleaner.get_backup_list()
            
            for backup in backups:
                name = backup['name']
                timestamp = backup.get('timestamp', 'Unknown')
                items_count = backup.get('items_count', 0)
                total_size = backup.get('total_size', 0)
                
                # Format size
                size_str = self.format_size(total_size)
                
                # Format timestamp
                if timestamp and timestamp != 'Unknown':
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = timestamp
                else:
                    date_str = 'Unknown'
                
                self.backup_tree.insert('', tk.END, values=(name, date_str, items_count, size_str))
            
            self.log_message(f"Backup list refreshed: {len(backups)} backups found")
            
        except Exception as e:
            error_msg = f"Failed to refresh backup list: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("Refresh Error", error_msg)
    
    def restore_backup(self):
        """Restore selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore.")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Restore", 
                                 f"Are you sure you want to restore backup '{backup_name}'?\n"
                                 "This will overwrite current AugmentCode data."):
            return
        
        try:
            backup_path = self.cleaner.backup_manager.backup_root / backup_name
            success = self.cleaner.restore_from_backup(backup_path)
            
            if success:
                self.log_message(f"Backup '{backup_name}' restored successfully")
                messagebox.showinfo("Restore Complete", "Backup restored successfully!")
            else:
                self.log_message(f"Failed to restore backup '{backup_name}'")
                messagebox.showerror("Restore Failed", "Failed to restore backup. Check log for details.")
        
        except Exception as e:
            error_msg = f"Error restoring backup: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("Restore Error", error_msg)
    
    def delete_backup(self):
        """Delete selected backup."""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to delete.")
            return
        
        item = self.backup_tree.item(selection[0])
        backup_name = item['values'][0]
        
        if not messagebox.askyesno("Confirm Delete", 
                                 f"Are you sure you want to delete backup '{backup_name}'?\n"
                                 "This action cannot be undone."):
            return
        
        try:
            backup_path = self.cleaner.backup_manager.backup_root / backup_name
            success = self.cleaner.backup_manager.delete_backup(backup_path)
            
            if success:
                self.log_message(f"Backup '{backup_name}' deleted successfully")
                self.refresh_backup_list()
            else:
                self.log_message(f"Failed to delete backup '{backup_name}'")
                messagebox.showerror("Delete Failed", "Failed to delete backup. Check log for details.")
        
        except Exception as e:
            error_msg = f"Error deleting backup: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("Delete Error", error_msg)
    
    def update_discovery_display(self, report: str):
        """Update the discovery tab with the report."""
        self.discovery_text.delete(1.0, tk.END)
        self.discovery_text.insert(1.0, report)
    
    def log_message(self, message: str):
        """Add a message to the log display."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status_loop(self):
        """Update status and progress from the cleaner."""
        try:
            status = self.cleaner.status
            
            # Update status text
            if status.current_operation:
                self.status_var.set(status.current_operation)
            
            # Update progress bar
            progress_percent = status.progress * 100
            self.progress_var.set(progress_percent)
            
            # Update log with new entries
            if hasattr(status, 'detailed_log') and status.detailed_log:
                # Only show new log entries (simple approach)
                current_log_lines = self.log_text.get(1.0, tk.END).count('\n')
                if len(status.detailed_log) > current_log_lines - 1:
                    for log_entry in status.detailed_log[current_log_lines - 1:]:
                        self.log_text.insert(tk.END, f"{log_entry}\n")
                    self.log_text.see(tk.END)
            
            # Check for errors
            if not status.success and status.error_message:
                messagebox.showerror("Operation Error", status.error_message)
                status.error_message = ""  # Clear to avoid repeated dialogs
        
        except Exception as e:
            pass  # Ignore errors in status update
        
        # Schedule next update
        self.root.after(500, self.update_status_loop)
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def run(self):
        """Run the GUI application."""
        # Initialize backup list
        self.refresh_backup_list()
        
        # Start the main loop
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = FreeAugmentCodeGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
