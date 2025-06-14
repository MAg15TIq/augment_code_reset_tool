# Enhanced Email Cleaning Guide

## 🎯 Overview

The **Free AugmentCode Data Cleaner v1.1** now includes comprehensive email address and account data cleaning capabilities. This enhancement specifically addresses the issue of email reuse after AugmentCode plan expiration.

## 🔧 New Features

### 1. **Email Address Discovery**
- Automatically finds email addresses in configuration files
- Supports JSON, INI, XML, and plain text formats
- Identifies user accounts, login credentials, and profile data
- Generates detailed reports of discovered account information

### 2. **Targeted Email Cleaning**
- Clean specific email addresses while preserving other data
- Remove all account data for complete reset
- Smart pattern matching to find related usernames
- Safe backup system before any modifications

### 3. **Enhanced Database Cleaning**
- Removes email addresses from SQLite databases
- Cleans account tables and user records
- Removes session data and authentication tokens
- Supports targeted email removal or complete account cleanup

### 4. **Configuration File Cleaning**
- Replaces email addresses with `[REMOVED]` placeholder
- Handles nested JSON structures
- Processes INI file sections
- Cleans XML attributes and elements

## 📋 How to Use

### Step 1: Discovery
1. Launch the application: `python main.py`
2. Select AugmentCode installation path (Auto-Detect or Browse)
3. Click **"Discover AugmentCode Data"**
4. Review the **Discovery** tab for found email addresses

### Step 2: Configure Email Cleaning
1. In the main tab, check **"Clean Account Data"**
2. **Option A - Target Specific Email:**
   - Enter the email address in "Target Email" field
   - This will remove only that specific email and related data
   
3. **Option B - Remove All Account Data:**
   - Leave "Target Email" empty
   - Check "Remove ALL account data"
   - This will remove all found email addresses and user accounts

### Step 3: Run Cleanup
1. Ensure **"Create Backup Before Cleaning"** is checked
2. Click **"Run Cleanup"**
3. Confirm the operation when prompted
4. Monitor progress in the activity log

## 🎯 Email Reuse Solution

### The Problem
AugmentCode may track users through:
- Email addresses stored in configuration files
- User account data in local databases
- Session tokens and authentication cache
- Device fingerprinting combined with email

### The Solution
This enhanced tool addresses email reuse by:

1. **Complete Email Removal**: Finds and removes email addresses from all configuration files
2. **Database Account Cleanup**: Removes user records and session data from SQLite databases
3. **Device ID Reset**: Changes device and machine IDs to appear as a new device
4. **Session Clearing**: Removes authentication tokens and cached login data

### Result
After running the enhanced cleaner:
- ✅ **Same email can be reused** - All traces of the email are removed locally
- ✅ **Device appears new** - Fresh device and machine IDs generated
- ✅ **Clean authentication state** - No cached login data remains
- ✅ **Safe operation** - Complete backup system for easy restoration

## 🔍 What Gets Cleaned

### Configuration Files
- `config.json` - User email, username, profile data
- `settings.ini` - Login credentials, user preferences
- `user.xml` - Account information, identity data
- Log files - Email references in activity logs

### Database Tables
- User accounts and profiles
- Login sessions and authentication
- Email verification records
- Account preferences and settings

### Registry (Windows)
- User account registry keys
- Email-related application settings
- Authentication tokens in registry

## 📊 Discovery Report Example

```
=== ACCOUNT DATA DISCOVERY REPORT ===

Summary:
  Email addresses found: 3
  User identifiers found: 5
  Files containing account data: 8

Found Email Addresses:
  • user@example.com
  • test@domain.org
  • admin@company.com

Found User Identifiers:
  • user123
  • testuser
  • admin
  • john.doe
  • support_user

Files Containing Account Data:
  File: C:\Users\User\AppData\Roaming\AugmentCode\config.json
    Emails: 1
    User IDs: 2
  
  File: C:\Users\User\AppData\Roaming\AugmentCode\settings.ini
    Emails: 2
    User IDs: 1
```

## ⚠️ Important Notes

### Safety First
- **Always create backups** before running cleanup
- Test with non-critical data first
- Keep backup files until you verify everything works
- Use the restore function if issues occur

### Effectiveness
- **Local data only**: This tool cleans local data on your computer
- **Server-side data**: AugmentCode's servers may still have records
- **Best results**: Combine with device ID changes for maximum effectiveness
- **Account limits**: Server-side account limits may still apply

### Recommendations
1. **Close AugmentCode** completely before running the cleaner
2. **Run as Administrator** for full access to all files
3. **Use specific email targeting** when possible for safer operation
4. **Verify results** by checking the discovery report after cleaning

## 🚀 Advanced Usage

### Command Line Options
```bash
# Run with specific email target
python main.py --target-email user@example.com

# Remove all account data
python main.py --remove-all-accounts

# Custom backup location
python main.py --backup-path /path/to/backups
```

### Automation
The tool can be integrated into scripts for automated cleaning:

```python
from data_cleaner import FreeAugmentCodeCleaner

cleaner = FreeAugmentCodeCleaner()
cleaner.discover_augmentcode_data()

cleanup_options = {
    'clean_account_data': True,
    'target_email': 'user@example.com',
    'modify_telemetry_ids': True,
    'clean_database': True
}

success = cleaner.perform_cleanup(cleanup_options)
```

## 🎉 Conclusion

The enhanced email cleaning functionality makes it possible to reuse the same email address with AugmentCode by:

1. **Removing all local traces** of the email address
2. **Resetting device identification** to appear as a new machine
3. **Clearing authentication state** for fresh login experience
4. **Providing safe backup/restore** for peace of mind

This comprehensive approach addresses the core issue of email reuse while maintaining the safety and reliability of the original tool.
