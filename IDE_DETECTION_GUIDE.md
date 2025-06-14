# 🔍 Enhanced IDE Detection Guide

## The Problem: Multiple IDEs, One AugmentCode

With the explosion of AI-powered IDEs in the market, users often have multiple code editors installed:
- **VS Code** (Microsoft's popular editor)
- **Cursor** (AI-first code editor)
- **Windsurf** (Codeium's AI editor)
- **Zed** (High-performance editor)
- **Sublime Text** (Classic text editor)
- And many more emerging daily!

Each IDE can have AugmentCode extensions/plugins installed, creating multiple instances of AugmentCode data across your system.

## 🎯 Our Solution: Intelligent Multi-IDE Detection

### Advanced Process Detection
The enhanced tool now uses **psutil** to detect running processes and identify which IDEs are currently using AugmentCode:

```python
# Detects running processes like:
# - code.exe (VS Code)
# - cursor.exe (Cursor)
# - windsurf.exe (Windsurf)
# - zed.exe (Zed)
```

### IDE-Specific Path Detection
Each IDE stores data in different locations. Our tool knows where to look:

**Windows:**
- VS Code: `%APPDATA%\Code\User`
- Cursor: `%APPDATA%\Cursor\User`
- Windsurf: `%APPDATA%\Windsurf\User`

**macOS:**
- VS Code: `~/Library/Application Support/Code/User`
- Cursor: `~/Library/Application Support/Cursor/User`
- Windsurf: `~/Library/Application Support/Windsurf/User`

**Linux:**
- VS Code: `~/.config/Code/User`
- Cursor: `~/.config/Cursor/User`
- Windsurf: `~/.config/Windsurf/User`

### Extension Pattern Recognition
The tool searches for AugmentCode-related patterns:
- Extension folders containing "augmentcode", "augment-code", "augment_code"
- Configuration files with AugmentCode settings
- Workspace data with AugmentCode projects
- Cache files from AugmentCode operations

## 🚀 How It Works

### 1. Comprehensive Scanning
```python
ide_manager = AugmentCodeIDEManager()
scan_results = ide_manager.perform_comprehensive_scan()
```

The scan process:
1. **Process Detection**: Finds all running IDE processes
2. **Installation Discovery**: Locates IDE installations on your system
3. **AugmentCode Analysis**: Checks each IDE for AugmentCode data
4. **Conflict Resolution**: Identifies potential conflicts between IDEs

### 2. Smart Differentiation
The tool can distinguish between:
- **Active AugmentCode instances** (currently running)
- **Installed but inactive** AugmentCode extensions
- **Cached data** from previous AugmentCode usage
- **Configuration remnants** from uninstalled extensions

### 3. Selective Cleanup
Users can choose:
- **Which IDEs** to clean AugmentCode data from
- **What types of data** to remove (extensions, config, cache)
- **Whether to preserve** certain IDE configurations

## 📊 Detection Report Example

```
================================================================================
AUGMENTCODE IDE DETECTION REPORT
================================================================================

🔄 RUNNING PROCESSES WITH AUGMENTCODE:
  • Visual Studio Code (PID: 12345)
    Process: code.exe
    Executable: C:\Users\User\AppData\Local\Programs\Microsoft VS Code\Code.exe
  • Cursor (PID: 67890)
    Process: cursor.exe
    Executable: C:\Users\User\AppData\Local\Programs\Cursor\Cursor.exe

💻 IDE INSTALLATIONS WITH AUGMENTCODE:
  📁 Visual Studio Code:
    Path: C:\Users\User\AppData\Roaming\Code\User
    Extensions: 1 found
    Config files: 3 found
    Workspace data: 5 files
    Cache files: 12 files

  📁 Cursor:
    Path: C:\Users\User\AppData\Roaming\Cursor\User
    Extensions: 1 found
    Config files: 2 found
    Workspace data: 3 files
    Cache files: 8 files
```

## ⚠️ Safety Features

### Process Management
- **Graceful termination** first (allows IDEs to save work)
- **Force termination** as fallback (if graceful fails)
- **Process validation** (ensures we're targeting the right processes)

### Data Protection
- **Selective targeting** (only AugmentCode-related data)
- **Backup creation** before any cleanup
- **Rollback capability** if something goes wrong

### User Control
- **IDE selection** (choose which IDEs to clean)
- **Data type selection** (choose what to clean)
- **Confirmation prompts** for destructive operations

## 🔧 Advanced Usage

### Command Line Interface
```bash
# Scan all IDEs
python main.py --scan-ides

# Clean specific IDE
python main.py --clean-ide vscode

# Clean multiple IDEs
python main.py --clean-ide vscode,cursor,windsurf

# Force terminate processes
python main.py --force-terminate
```

### Programmatic Usage
```python
from ide_manager import AugmentCodeIDEManager

# Initialize manager
manager = AugmentCodeIDEManager()

# Perform scan
results = manager.perform_comprehensive_scan()

# Get cleanup targets for specific IDEs
targets = manager.get_cleanup_targets(['vscode', 'cursor'])

# Safely terminate processes
termination_result = manager.safe_terminate_processes()
```

## 🎯 Benefits of Enhanced Detection

### 1. **Precision Targeting**
- No more guessing which IDE has AugmentCode
- Exact identification of data locations
- Minimal impact on non-AugmentCode data

### 2. **Multi-IDE Support**
- Works with all popular IDEs
- Easily extensible for new IDEs
- Handles multiple installations gracefully

### 3. **Conflict Resolution**
- Identifies which IDE is actively using AugmentCode
- Prevents data corruption from simultaneous access
- Provides clear recommendations for cleanup

### 4. **User-Friendly**
- Clear reports of what was found
- Easy selection of what to clean
- Comprehensive feedback on operations

## 🔮 Future-Proof Design

The detection system is designed to be easily extensible:
- **New IDE support** can be added by updating the IDE configuration
- **Detection patterns** can be refined based on user feedback
- **Process detection** adapts to new IDE naming conventions

This ensures the tool remains effective as new IDEs enter the market!
