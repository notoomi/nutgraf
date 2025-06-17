"""
Bookmark Parser Service

This service handles parsing browser bookmark files (HTML format) to extract URLs.
Supports exports from Chrome, Firefox, Safari, Edge, and other browsers.
"""

import re
import html
from urllib.parse import urlparse
from datetime import datetime
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class BookmarkParser:
    """Parser for browser bookmark files"""
    
    def __init__(self):
        # Regex patterns for different bookmark formats
        self.bookmark_patterns = [
            # Standard Netscape bookmark format (Chrome, Firefox, etc.)
            r'<DT><A[^>]*HREF="([^"]+)"[^>]*>([^<]+)</A>',
            # Alternative format with different attribute order
            r'<A[^>]*HREF="([^"]+)"[^>]*><[^>]*>([^<]+)</A>',
            # Simple format
            r'<A[^>]*HREF=["\']([^"\']+)["\'][^>]*>([^<]+)</A>',
        ]
        
        # Folder detection pattern
        self.folder_pattern = r'<DT><H3[^>]*>([^<]+)</H3>'
        
        # Add date pattern for bookmark timestamps
        self.add_date_pattern = r'ADD_DATE="(\d+)"'
    
    def parse_bookmark_file(self, file_content: str) -> Dict[str, Union[List[Dict], str]]:
        """
        Parse a bookmark file and extract URLs with metadata
        
        Args:
            file_content: String content of the bookmark file
            
        Returns:
            Dictionary containing parsed bookmarks and metadata
        """
        try:
            result = {
                'bookmarks': [],
                'folders': [],
                'total_count': 0,
                'parsing_errors': [],
                'file_type': 'html_bookmarks'
            }
            
            # Clean up the content
            content = self._clean_html_content(file_content)
            
            # Extract bookmarks using multiple patterns
            bookmarks = self._extract_bookmarks(content)
            
            # Extract folder structure (optional)
            folders = self._extract_folders(content)
            
            result['bookmarks'] = bookmarks
            result['folders'] = folders
            result['total_count'] = len(bookmarks)
            
            logger.info(f"Successfully parsed {len(bookmarks)} bookmarks from file")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing bookmark file: {str(e)}")
            return {
                'bookmarks': [],
                'folders': [],
                'total_count': 0,
                'parsing_errors': [str(e)],
                'file_type': 'unknown'
            }
    
    def _clean_html_content(self, content: str) -> str:
        """Clean and normalize HTML content"""
        # Remove extra whitespace and normalize line endings
        content = re.sub(r'\s+', ' ', content)
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Decode HTML entities
        content = html.unescape(content)
        
        return content
    
    def _extract_bookmarks(self, content: str) -> List[Dict]:
        """Extract bookmarks from HTML content"""
        bookmarks = []
        
        for pattern in self.bookmark_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                try:
                    url = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    # Skip if URL is empty or invalid
                    if not url or not self._is_valid_url(url):
                        continue
                    
                    # Remove HTML tags from title
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    # Extract additional metadata from the full match
                    full_match = match.group(0)
                    add_date = self._extract_add_date(full_match)
                    
                    bookmark = {
                        'url': url,
                        'title': title or 'Untitled',
                        'add_date': add_date,
                        'folder': self._extract_folder_context(content, match.start()),
                        'source': 'browser_bookmarks'
                    }
                    
                    # Avoid duplicates
                    if not any(b['url'] == url for b in bookmarks):
                        bookmarks.append(bookmark)
                        
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Error parsing bookmark: {str(e)}")
                    continue
        
        return bookmarks
    
    def _extract_folders(self, content: str) -> List[str]:
        """Extract folder names from bookmark file"""
        folders = []
        
        folder_matches = re.finditer(self.folder_pattern, content, re.IGNORECASE)
        for match in folder_matches:
            folder_name = match.group(1).strip()
            # Remove HTML tags
            folder_name = re.sub(r'<[^>]+>', '', folder_name).strip()
            if folder_name and folder_name not in folders:
                folders.append(folder_name)
        
        return folders
    
    def _extract_add_date(self, bookmark_html: str) -> Optional[datetime]:
        """Extract ADD_DATE timestamp from bookmark HTML"""
        try:
            match = re.search(self.add_date_pattern, bookmark_html)
            if match:
                timestamp = int(match.group(1))
                return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError):
            pass
        return None
    
    def _extract_folder_context(self, content: str, bookmark_position: int) -> Optional[str]:
        """Determine which folder a bookmark belongs to based on its position"""
        # Look backwards from bookmark position to find the most recent folder
        content_before = content[:bookmark_position]
        folder_matches = list(re.finditer(self.folder_pattern, content_before, re.IGNORECASE))
        
        if folder_matches:
            last_folder = folder_matches[-1]
            folder_name = last_folder.group(1).strip()
            return re.sub(r'<[^>]+>', '', folder_name).strip()
        
        return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if a string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def extract_urls_only(self, file_content: str) -> List[str]:
        """
        Simple method to extract just the URLs from a bookmark file
        
        Args:
            file_content: String content of the bookmark file
            
        Returns:
            List of URLs
        """
        result = self.parse_bookmark_file(file_content)
        return [bookmark['url'] for bookmark in result['bookmarks']]
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported bookmark file formats"""
        return [
            'HTML (Netscape format)',
            'Chrome bookmarks export',
            'Firefox bookmarks export', 
            'Safari bookmarks export',
            'Edge bookmarks export',
            'Opera bookmarks export'
        ]
    
    def validate_bookmark_file(self, file_content: str) -> Dict[str, Union[bool, str]]:
        """
        Validate if a file appears to be a valid bookmark file
        
        Returns:
            Dictionary with validation result and details
        """
        try:
            # Check for common bookmark file indicators
            indicators = [
                '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
                '<META HTTP-EQUIV="Content-Type" CONTENT="text/html',
                '<TITLE>Bookmarks</TITLE>',
                '<H1>Bookmarks</H1>',
                '<DT><A HREF=',
                'HREF="http'
            ]
            
            content_upper = file_content.upper()
            matches = sum(1 for indicator in indicators if indicator.upper() in content_upper)
            
            if matches >= 2:
                return {
                    'is_valid': True,
                    'confidence': min(matches / len(indicators), 1.0),
                    'message': 'Valid bookmark file detected'
                }
            else:
                return {
                    'is_valid': False,
                    'confidence': matches / len(indicators),
                    'message': 'File does not appear to be a standard bookmark export'
                }
                
        except Exception as e:
            return {
                'is_valid': False,
                'confidence': 0.0,
                'message': f'Error validating file: {str(e)}'
            }

# Create a global instance
bookmark_parser = BookmarkParser()