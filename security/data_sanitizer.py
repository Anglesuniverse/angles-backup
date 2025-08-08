#!/usr/bin/env python3
"""
Angles AI Universe™ Data Sanitization & Security Module
Advanced data protection and sanitization for sensitive information

Author: Angles AI Universe™ Security Team
Version: 1.0.0
"""

import os
import re
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

class DataSanitizer:
    """Advanced data sanitization for security compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger('data_sanitizer')
        
        # Define sensitive patterns to redact
        self.sensitive_patterns = {
            'api_keys': [
                r'sk-[A-Za-z0-9]{48,}',  # OpenAI API keys
                r'ntn_[A-Za-z0-9]{45,}',  # Notion API keys
                r'ghp_[A-Za-z0-9]{36}',   # GitHub personal access tokens
                r'github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}',  # GitHub fine-grained tokens
                r'supabase\.[a-z0-9]{20}\.[a-z0-9]{27}',  # Supabase keys
                r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'  # JWT tokens
            ],
            'secrets': [
                r'secret_[A-Za-z0-9]{32,}',
                r'key_[A-Za-z0-9]{32,}',
                r'token_[A-Za-z0-9]{32,}'
            ],
            'credentials': [
                r'password["\']?\s*[:=]\s*["\'][^"\']+["\']',
                r'passwd["\']?\s*[:=]\s*["\'][^"\']+["\']',
                r'auth["\']?\s*[:=]\s*["\'][^"\']+["\']'
            ],
            'urls_with_tokens': [
                r'https?://[^@]+@[^/]+/[^\s]+',  # URLs with credentials
                r'postgresql://[^:]+:[^@]+@[^/]+/[^\s]+'  # Database URLs with passwords
            ]
        }
        
        # Safe prefixes for partial exposure
        self.safe_exposure_length = 8
        
    def sanitize_text(self, text: str, preserve_structure: bool = True) -> str:
        """
        Sanitize text by redacting sensitive information
        
        Args:
            text: Text to sanitize
            preserve_structure: Keep structure for readability
            
        Returns:
            Sanitized text with sensitive data redacted
        """
        if not isinstance(text, str):
            return str(text)
        
        sanitized = text
        
        # Process each category of sensitive patterns
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, sanitized, re.IGNORECASE)
                for match in matches:
                    original = match.group(0)
                    
                    if preserve_structure:
                        # Show first few characters + redacted indicator
                        if len(original) > self.safe_exposure_length:
                            safe_prefix = original[:self.safe_exposure_length]
                            redacted = f"{safe_prefix}...{category.upper()}"
                        else:
                            redacted = f"***{category.upper()}***"
                    else:
                        redacted = f"[REDACTED_{category.upper()}]"
                    
                    sanitized = sanitized.replace(original, redacted)
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """
        Sanitize dictionary data recursively
        
        Args:
            data: Dictionary to sanitize
            deep: Whether to recursively sanitize nested structures
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize keys
            clean_key = self.sanitize_text(str(key))
            
            # Sanitize values based on type
            if isinstance(value, str):
                clean_value = self.sanitize_text(value)
            elif isinstance(value, dict) and deep:
                clean_value = self.sanitize_dict(value, deep=True)
            elif isinstance(value, list) and deep:
                clean_value = [
                    self.sanitize_dict(item, deep=True) if isinstance(item, dict)
                    else self.sanitize_text(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    def sanitize_json_file(self, file_path: Path, backup: bool = True) -> bool:
        """
        Sanitize JSON file in-place with optional backup
        
        Args:
            file_path: Path to JSON file
            backup: Whether to create backup before sanitizing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                self.logger.warning(f"File not found: {file_path}")
                return False
            
            # Create backup if requested
            if backup:
                backup_path = file_path.with_suffix(f'{file_path.suffix}.backup')
                backup_path.write_text(file_path.read_text())
                self.logger.info(f"Backup created: {backup_path}")
            
            # Load and sanitize
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            sanitized_data = self.sanitize_dict(data)
            
            # Write back sanitized data
            with open(file_path, 'w') as f:
                json.dump(sanitized_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully sanitized: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sanitize {file_path}: {e}")
            return False
    
    def sanitize_log_file(self, file_path: Path, output_path: Optional[Path] = None) -> bool:
        """
        Sanitize log file by removing sensitive information
        
        Args:
            file_path: Path to log file
            output_path: Output path (defaults to same file with .safe suffix)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                self.logger.warning(f"Log file not found: {file_path}")
                return False
            
            if output_path is None:
                output_path = file_path.with_suffix('.safe' + file_path.suffix)
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            sanitized_content = self.sanitize_text(content)
            
            with open(output_path, 'w') as f:
                f.write(sanitized_content)
            
            self.logger.info(f"Sanitized log saved: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sanitize log {file_path}: {e}")
            return False
    
    def create_secure_hash(self, data: Union[str, Dict[str, Any]]) -> str:
        """
        Create secure hash of data for integrity verification
        
        Args:
            data: Data to hash (string or dictionary)
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        if isinstance(data, dict):
            # Convert dict to sorted JSON string for consistent hashing
            json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            data_bytes = json_str.encode('utf-8')
        else:
            data_bytes = str(data).encode('utf-8')
        
        return hashlib.sha256(data_bytes).hexdigest()
    
    def validate_environment_security(self) -> Dict[str, Any]:
        """
        Validate environment for security best practices
        
        Returns:
            Security validation report
        """
        report = {
            'timestamp': os.popen('date -u').read().strip(),
            'checks': {},
            'warnings': [],
            'critical_issues': [],
            'overall_score': 0
        }
        
        checks = []
        
        # Check 1: Environment file permissions
        env_file = Path('.env')
        if env_file.exists():
            stat_info = env_file.stat()
            permissions = oct(stat_info.st_mode)[-3:]
            
            if permissions == '600':  # Owner read/write only
                checks.append(('env_permissions', True, 'Environment file has secure permissions'))
            else:
                checks.append(('env_permissions', False, f'Environment file permissions too permissive: {permissions}'))
                report['critical_issues'].append('Environment file permissions too permissive')
        else:
            checks.append(('env_permissions', True, 'No .env file found (using secrets management)'))
        
        # Check 2: Log directory permissions
        logs_dir = Path('logs')
        if logs_dir.exists():
            stat_info = logs_dir.stat()
            permissions = oct(stat_info.st_mode)[-3:]
            
            if permissions in ['755', '750', '700']:
                checks.append(('logs_permissions', True, 'Logs directory has appropriate permissions'))
            else:
                checks.append(('logs_permissions', False, f'Logs directory permissions: {permissions}'))
                report['warnings'].append('Logs directory permissions could be more restrictive')
        
        # Check 3: Export directory security
        export_dir = Path('export')
        if export_dir.exists():
            # Check for any files with sensitive data patterns
            sensitive_files = []
            for file_path in export_dir.glob('**/*.json'):
                try:
                    content = file_path.read_text()
                    if any(re.search(pattern, content, re.IGNORECASE) 
                          for patterns in self.sensitive_patterns.values() 
                          for pattern in patterns):
                        sensitive_files.append(file_path.name)
                except Exception:
                    continue
            
            if sensitive_files:
                checks.append(('export_security', False, f'Found {len(sensitive_files)} files with sensitive data'))
                report['warnings'].append(f'Export files may contain sensitive data: {sensitive_files[:3]}')
            else:
                checks.append(('export_security', True, 'Export files appear clean'))
        
        # Check 4: Git security
        git_dir = Path('.git')
        if git_dir.exists():
            # Check if .env is in .gitignore
            gitignore = Path('.gitignore')
            if gitignore.exists():
                gitignore_content = gitignore.read_text()
                if '.env' in gitignore_content:
                    checks.append(('git_security', True, 'Environment file properly ignored by git'))
                else:
                    checks.append(('git_security', False, 'Environment file not in .gitignore'))
                    report['critical_issues'].append('Environment file not in .gitignore')
            else:
                checks.append(('git_security', False, 'No .gitignore file found'))
                report['warnings'].append('No .gitignore file found')
        
        # Calculate overall score
        passed_checks = sum(1 for _, passed, _ in checks if passed)
        total_checks = len(checks)
        report['overall_score'] = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Store check results
        for check_name, passed, message in checks:
            report['checks'][check_name] = {
                'passed': passed,
                'message': message
            }
        
        return report

class SecureFileManager:
    """Secure file operations with integrity checking"""
    
    def __init__(self):
        self.logger = logging.getLogger('secure_file_manager')
        self.sanitizer = DataSanitizer()
    
    def secure_copy(self, src: Path, dst: Path, verify_integrity: bool = True) -> bool:
        """
        Securely copy file with integrity verification
        
        Args:
            src: Source file path
            dst: Destination file path
            verify_integrity: Whether to verify file integrity after copy
            
        Returns:
            True if copy successful and verified, False otherwise
        """
        try:
            if not src.exists():
                self.logger.error(f"Source file not found: {src}")
                return False
            
            # Create destination directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate source hash before copy
            src_hash = None
            if verify_integrity:
                src_content = src.read_bytes()
                src_hash = hashlib.sha256(src_content).hexdigest()
            
            # Copy file
            dst.write_bytes(src.read_bytes())
            
            # Verify integrity after copy
            if verify_integrity:
                dst_content = dst.read_bytes()
                dst_hash = hashlib.sha256(dst_content).hexdigest()
                
                if src_hash != dst_hash:
                    self.logger.error(f"Integrity verification failed for {src} -> {dst}")
                    return False
            
            self.logger.info(f"Secure copy completed: {src} -> {dst}")
            return True
            
        except Exception as e:
            self.logger.error(f"Secure copy failed: {e}")
            return False
    
    def secure_json_write(self, data: Dict[str, Any], file_path: Path, 
                         sanitize: bool = True, backup: bool = True) -> bool:
        """
        Securely write JSON data with optional sanitization and backup
        
        Args:
            data: Data to write
            file_path: Output file path
            sanitize: Whether to sanitize sensitive data
            backup: Whether to create backup of existing file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if file exists and backup requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f'{file_path.suffix}.backup')
                self.secure_copy(file_path, backup_path)
            
            # Sanitize data if requested
            output_data = self.sanitizer.sanitize_dict(data) if sanitize else data
            
            # Write with atomic operation (write to temp, then rename)
            temp_path = file_path.with_suffix(f'{file_path.suffix}.tmp')
            
            with open(temp_path, 'w') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.rename(file_path)
            
            self.logger.info(f"Secure JSON write completed: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Secure JSON write failed: {e}")
            return False

def setup_security_logging():
    """Setup logging for security module"""
    os.makedirs("logs/security", exist_ok=True)
    
    logger = logging.getLogger('data_sanitizer')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler for security logs
        file_handler = logging.FileHandler('logs/security/security.log')
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
    
    return logger

# Initialize security logging
setup_security_logging()