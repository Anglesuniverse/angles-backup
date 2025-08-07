#!/usr/bin/env python3
"""
File Manager for Angles AI Universe™
Internal document and export system for storing and managing files

This module provides comprehensive file management capabilities for:
- Saving text content to organized folders
- Reading, listing, and deleting files
- Appending content to existing files  
- Converting Markdown to PDF (optional)
- Modular design for future extensions

Author: Angles AI Universe™ Backend Team
Version: 1.0.0
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Configure logging for file operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('file_manager')

class FileManager:
    """
    Comprehensive file management system for Angles AI Universe™
    Handles all file operations across organized folder structures
    """
    
    # Define the folder structure for the system
    FOLDERS = {
        'angles_universe': 'angles_universe',
        'memory_logs': 'memory_logs', 
        'decision_exports': 'decision_exports',
        'strategic_docs': 'strategic_docs',
        'agents': 'agents',
        'tmp': 'tmp'
    }
    
    def __init__(self, base_path: str = "."):
        """
        Initialize the File Manager
        
        Args:
            base_path: Base directory path for all operations (default: current directory)
        """
        self.base_path = Path(base_path).resolve()
        logger.info(f"Initializing File Manager with base path: {self.base_path}")
        
        # Ensure all required folders exist
        self._create_folder_structure()
        
        logger.info("File Manager initialized successfully")
    
    def _create_folder_structure(self) -> None:
        """Create all required folders if they don't exist"""
        for folder_name, folder_path in self.FOLDERS.items():
            full_path = self.base_path / folder_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured folder exists: {full_path}")
    
    def _get_folder_path(self, folder: str) -> Path:
        """
        Get the full path for a folder
        
        Args:
            folder: Folder name (key from FOLDERS dict) or custom path
            
        Returns:
            Path object for the folder
        """
        if folder in self.FOLDERS:
            return self.base_path / self.FOLDERS[folder]
        else:
            # Allow custom folder paths
            return self.base_path / folder
    
    def _generate_timestamp_filename(self, base_name: str, extension: str = "txt") -> str:
        """
        Generate a filename with timestamp
        
        Args:
            base_name: Base name for the file
            extension: File extension (without dot)
            
        Returns:
            Timestamped filename
        """
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        return f"{timestamp}-{base_name}.{extension}"
    
    def save_file(self, 
                  folder: str, 
                  content: str, 
                  filename: Optional[str] = None,
                  auto_timestamp: bool = False,
                  encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Save text content to a file in the specified folder
        
        Args:
            folder: Target folder name or path
            content: Text content to save
            filename: Specific filename (if None, will be auto-generated)
            auto_timestamp: Add timestamp to filename automatically
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with operation results
        """
        try:
            folder_path = self._get_folder_path(folder)
            
            # Generate filename if not provided
            if filename is None:
                filename = self._generate_timestamp_filename("document", "txt")
            elif auto_timestamp and not filename.startswith(datetime.now().strftime("%Y-%m-%d")):
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    base_name, extension = name_parts
                    filename = self._generate_timestamp_filename(base_name, extension)
                else:
                    filename = self._generate_timestamp_filename(filename, "txt")
            
            file_path = folder_path / filename
            
            # Save the content
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"File saved successfully: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "folder": folder,
                "size_bytes": len(content.encode(encoding)),
                "message": f"File saved to {folder}/{filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to save file to {folder}/{filename}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "folder": folder,
                "filename": filename
            }
    
    def read_file(self, 
                  folder: str, 
                  filename: str,
                  encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read content from a file
        
        Args:
            folder: Folder name or path
            filename: Name of the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            folder_path = self._get_folder_path(folder)
            file_path = folder_path / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {folder}/{filename}",
                    "file_path": str(file_path)
                }
            
            # Read the file content
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Get file stats
            stats = file_path.stat()
            
            logger.info(f"File read successfully: {file_path}")
            
            return {
                "success": True,
                "content": content,
                "file_path": str(file_path),
                "filename": filename,
                "folder": folder,
                "size_bytes": stats.st_size,
                "modified_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "message": f"File read from {folder}/{filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to read file {folder}/{filename}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "folder": folder,
                "filename": filename
            }
    
    def append_to_file(self,
                      folder: str,
                      filename: str,
                      content: str,
                      separator: str = "\n\n",
                      encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Append content to an existing file
        
        Args:
            folder: Folder name or path
            filename: Name of the file to append to
            content: Content to append
            separator: Separator to add before new content
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with operation results
        """
        try:
            folder_path = self._get_folder_path(folder)
            file_path = folder_path / filename
            
            # If file doesn't exist, create it
            if not file_path.exists():
                logger.info(f"File doesn't exist, creating new file: {file_path}")
                return self.save_file(folder, content, filename, encoding=encoding)
            
            # Append to existing file
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(separator + content)
            
            # Get updated file stats
            stats = file_path.stat()
            
            logger.info(f"Content appended successfully: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "folder": folder,
                "size_bytes": stats.st_size,
                "appended_bytes": len(content.encode(encoding)),
                "message": f"Content appended to {folder}/{filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to append to file {folder}/{filename}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "folder": folder,
                "filename": filename
            }
    
    def list_files(self, 
                   folder: str,
                   pattern: str = "*",
                   include_stats: bool = True) -> Dict[str, Any]:
        """
        List files in a folder
        
        Args:
            folder: Folder name or path
            pattern: File pattern to match (default: all files)
            include_stats: Include file statistics
            
        Returns:
            Dictionary with list of files and metadata
        """
        try:
            folder_path = self._get_folder_path(folder)
            
            if not folder_path.exists():
                return {
                    "success": False,
                    "error": f"Folder not found: {folder}",
                    "folder_path": str(folder_path)
                }
            
            # Get matching files
            files = list(folder_path.glob(pattern))
            file_list = []
            
            for file_path in files:
                if file_path.is_file():
                    file_info = {
                        "filename": file_path.name,
                        "path": str(file_path)
                    }
                    
                    if include_stats:
                        stats = file_path.stat()
                        file_info["size_bytes"] = stats.st_size
                        file_info["modified_time"] = datetime.fromtimestamp(stats.st_mtime).isoformat()
                        file_info["created_time"] = datetime.fromtimestamp(stats.st_ctime).isoformat()
                    
                    file_list.append(file_info)
            
            # Sort by modification time (newest first)
            if include_stats:
                file_list.sort(key=lambda x: x["modified_time"], reverse=True)
            else:
                file_list.sort(key=lambda x: x["filename"])
            
            logger.info(f"Listed {len(file_list)} files in {folder}")
            
            return {
                "success": True,
                "files": file_list,
                "count": len(file_list),
                "folder": folder,
                "folder_path": str(folder_path),
                "pattern": pattern,
                "message": f"Found {len(file_list)} files in {folder}"
            }
            
        except Exception as e:
            error_msg = f"Failed to list files in {folder}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "folder": folder
            }
    
    def delete_file(self, 
                    folder: str, 
                    filename: str) -> Dict[str, Any]:
        """
        Delete a file from a folder
        
        Args:
            folder: Folder name or path
            filename: Name of the file to delete
            
        Returns:
            Dictionary with operation results
        """
        try:
            folder_path = self._get_folder_path(folder)
            file_path = folder_path / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {folder}/{filename}",
                    "file_path": str(file_path)
                }
            
            # Delete the file
            file_path.unlink()
            
            logger.info(f"File deleted successfully: {file_path}")
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "folder": folder,
                "message": f"File deleted: {folder}/{filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to delete file {folder}/{filename}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "folder": folder,
                "filename": filename
            }
    
    def markdown_to_pdf(self, 
                       folder: str, 
                       markdown_filename: str,
                       pdf_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert Markdown file to PDF (optional feature)
        
        Args:
            folder: Folder containing the markdown file
            markdown_filename: Name of the markdown file
            pdf_filename: Output PDF filename (auto-generated if None)
            
        Returns:
            Dictionary with conversion results
        """
        try:
            # Try to import required libraries
            try:
                import markdown
                from fpdf import FPDF
            except ImportError as ie:
                return {
                    "success": False,
                    "error": f"Required libraries not installed: {ie}. Install with: pip install markdown fpdf2",
                    "feature": "markdown_to_pdf"
                }
            
            # Read the markdown file
            md_result = self.read_file(folder, markdown_filename)
            if not md_result["success"]:
                return md_result
            
            markdown_content = md_result["content"]
            
            # Convert markdown to HTML
            html_content = markdown.markdown(markdown_content)
            
            # Create PDF filename if not provided
            if pdf_filename is None:
                base_name = markdown_filename.rsplit('.', 1)[0]
                pdf_filename = f"{base_name}.pdf"
            
            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Simple text conversion (HTML tags will be visible - this is basic)
            # For better HTML to PDF conversion, consider using libraries like weasyprint
            for line in html_content.split('\n'):
                if line.strip():
                    pdf.cell(200, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=1, align='L')
            
            # Save PDF
            folder_path = self._get_folder_path(folder)
            pdf_path = folder_path / pdf_filename
            pdf.output(str(pdf_path))
            
            logger.info(f"Markdown converted to PDF: {pdf_path}")
            
            return {
                "success": True,
                "source_file": markdown_filename,
                "pdf_file": pdf_filename,
                "pdf_path": str(pdf_path),
                "folder": folder,
                "message": f"Converted {markdown_filename} to {pdf_filename}"
            }
            
        except Exception as e:
            error_msg = f"Failed to convert markdown to PDF: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "source_file": markdown_filename,
                "folder": folder
            }
    
    def get_folder_structure(self) -> Dict[str, Any]:
        """
        Get information about the folder structure
        
        Returns:
            Dictionary with folder structure and statistics
        """
        try:
            structure = {}
            total_files = 0
            total_size = 0
            
            for folder_name, folder_path in self.FOLDERS.items():
                full_path = self.base_path / folder_path
                
                if full_path.exists():
                    files = list(full_path.glob("*"))
                    file_count = len([f for f in files if f.is_file()])
                    folder_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    structure[folder_name] = {
                        "path": str(full_path),
                        "exists": True,
                        "file_count": file_count,
                        "size_bytes": folder_size
                    }
                    
                    total_files += file_count
                    total_size += folder_size
                else:
                    structure[folder_name] = {
                        "path": str(full_path),
                        "exists": False,
                        "file_count": 0,
                        "size_bytes": 0
                    }
            
            return {
                "success": True,
                "folders": structure,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "base_path": str(self.base_path),
                "message": f"Folder structure contains {total_files} files across {len(self.FOLDERS)} folders"
            }
            
        except Exception as e:
            error_msg = f"Failed to get folder structure: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

# Convenience functions for direct usage
def save_memory_log(content: str, filename: Optional[str] = None, auto_timestamp: bool = True) -> Dict[str, Any]:
    """Save content to memory_logs folder"""
    fm = FileManager()
    return fm.save_file("memory_logs", content, filename, auto_timestamp)

def save_decision_export(content: str, filename: Optional[str] = None, auto_timestamp: bool = True) -> Dict[str, Any]:
    """Save content to decision_exports folder"""
    fm = FileManager()
    return fm.save_file("decision_exports", content, filename, auto_timestamp)

def save_strategic_doc(content: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Save content to strategic_docs folder"""
    fm = FileManager()
    return fm.save_file("strategic_docs", content, filename)

def save_agent_log(content: str, agent_name: str, auto_timestamp: bool = True) -> Dict[str, Any]:
    """Save agent log to agents folder"""
    fm = FileManager()
    filename = f"{agent_name}.log" if not auto_timestamp else None
    return fm.save_file("agents", content, filename, auto_timestamp)

def list_all_files() -> Dict[str, Any]:
    """Get overview of all files across all folders"""
    fm = FileManager()
    return fm.get_folder_structure()

# Example usage and testing
if __name__ == "__main__":
    print("Angles AI Universe™ File Manager")
    print("=" * 50)
    
    # Initialize file manager
    fm = FileManager()
    
    # Show folder structure
    structure = fm.get_folder_structure()
    print(f"Folder structure: {structure['message']}")
    
    # Example operations
    print("\nExample Operations:")
    
    # Save a test file
    test_content = "This is a test document for the Angles AI Universe™ system."
    result = fm.save_file("memory_logs", test_content, "test-document.txt")
    print(f"Save result: {result['message']}")
    
    # List files
    files = fm.list_files("memory_logs")
    print(f"Files in memory_logs: {files['count']} files found")
    
    # Read the file back
    read_result = fm.read_file("memory_logs", "test-document.txt")
    if read_result["success"]:
        print(f"File content preview: {read_result['content'][:50]}...")
    
    print("\nFile Manager ready for use!")