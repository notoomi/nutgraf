import requests
import feedparser
from urllib.parse import urlparse, urljoin
import csv
import io
import re

class URLProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def process_url_list(self, url_text):
        """
        Process a list of URLs from textarea input
        """
        urls = []
        lines = url_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and self._is_valid_url(line):
                urls.append(line)
        
        return urls
    
    def process_file_upload(self, file_content, file_type):
        """
        Process URLs from uploaded file (CSV or TXT)
        """
        urls = []
        
        try:
            content = file_content.decode('utf-8')
            
            if file_type.lower() == 'csv':
                # Process CSV file
                csv_reader = csv.reader(io.StringIO(content))
                for row in csv_reader:
                    for cell in row:
                        cell = cell.strip()
                        if cell and self._is_valid_url(cell):
                            urls.append(cell)
            else:
                # Process TXT file
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and self._is_valid_url(line):
                        urls.append(line)
        
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")
        
        return urls
    
    def process_rss_feed(self, rss_url):
        """
        Process URLs from RSS feed
        """
        try:
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                raise Exception("Invalid RSS feed")
            
            urls = []
            for entry in feed.entries:
                if hasattr(entry, 'link') and entry.link:
                    urls.append(entry.link)
            
            return urls
            
        except Exception as e:
            raise Exception(f"Failed to process RSS feed: {str(e)}")
    
    def process_url(self, url):
        """
        Process a single URL and return basic metadata
        """
        try:
            if not self._is_valid_url(url):
                return None
            
            # Try to fetch basic metadata with more lenient approach
            try:
                response = self.session.head(url, timeout=15, allow_redirects=True)
                if response.status_code not in [200, 301, 302]:
                    # Try GET request if HEAD fails
                    response = self.session.get(url, timeout=15, stream=True)
                    # Read only first 2KB for metadata
                    content = response.raw.read(2048).decode('utf-8', errors='ignore')
                    response.close()
                else:
                    content = None
            except:
                # If both HEAD and GET fail, still try to process the URL
                return {
                    'url': url,
                    'title': self._extract_title_from_url(url),
                    'status': 'warning',
                    'accessible': True,  # Assume accessible, let article extractor handle it
                    'warning': 'Could not verify URL accessibility, but will attempt extraction'
                }
            
            # Extract basic info
            title = self._extract_title_from_content(content) if content else self._extract_title_from_url(url)
            
            # Be more lenient about what we consider "accessible"
            is_accessible = response.status_code in [200, 301, 302, 403, 404]  # Even 403/404 might have content
            
            return {
                'url': url,
                'title': title,
                'status': 'valid',
                'accessible': is_accessible
            }
            
        except Exception as e:
            # Even if there's an error, still allow the URL to be processed
            return {
                'url': url,
                'title': self._extract_title_from_url(url),
                'status': 'warning',
                'error': str(e),
                'accessible': True,  # Let the article extractor decide
                'warning': f'URL check failed ({str(e)}), but will attempt extraction'
            }
    
    def _is_valid_url(self, url):
        """
        Validate if string is a valid URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _extract_title_from_url(self, url):
        """
        Extract a title from URL path
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if path:
                # Get the last part of the path
                title = path.split('/')[-1]
                # Remove file extensions
                title = re.sub(r'\.[a-zA-Z0-9]+$', '', title)
                # Replace hyphens and underscores with spaces
                title = re.sub(r'[-_]', ' ', title)
                # Capitalize
                title = title.title()
                return title
            else:
                return parsed.netloc
                
        except:
            return url
    
    def _extract_title_from_content(self, content):
        """
        Extract title from HTML content
        """
        try:
            # Simple regex to find title tag
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except:
            pass
        
        return None
    
    def batch_process_urls(self, urls, max_workers=5):
        """
        Process multiple URLs concurrently
        """
        import concurrent.futures
        import threading
        
        results = []
        
        def process_single_url(url):
            return self.process_url(url)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(process_single_url, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    url = future_to_url[future]
                    results.append({
                        'url': url,
                        'title': self._extract_title_from_url(url),
                        'status': 'error',
                        'error': str(e),
                        'accessible': False
                    })
        
        return results
    
    def import_browser_bookmarks(self, bookmarks_html):
        """
        Import URLs from browser bookmarks HTML export
        """
        urls = []
        
        try:
            # Simple regex to find bookmark URLs
            url_pattern = r'<A[^>]+HREF="([^"]+)"[^>]*>([^<]*)</A>'
            matches = re.findall(url_pattern, bookmarks_html, re.IGNORECASE)
            
            for url, title in matches:
                if self._is_valid_url(url):
                    urls.append({
                        'url': url,
                        'title': title.strip() if title.strip() else self._extract_title_from_url(url),
                        'status': 'imported',
                        'accessible': None  # Will be checked later
                    })
        
        except Exception as e:
            raise Exception(f"Failed to parse bookmarks: {str(e)}")
        
        return urls