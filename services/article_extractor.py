import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urlparse, urljoin
import re
from datetime import datetime

class ArticleExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract(self, url):
        try:
            # Fetch the page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for common paywall indicators (but continue processing anyway)
            is_potentially_paywalled = self._is_paywalled(response.text)
            
            # Use readability to extract main content
            doc = Document(response.text)
            clean_html = doc.summary()
            
            # Parse with BeautifulSoup for further processing
            soup = BeautifulSoup(clean_html, 'html.parser')
            
            # Extract text content
            content = self._extract_text_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(response.text, url)
            
            # Calculate word count
            word_count = len(content.split()) if content else 0
            
            # If content is too short and paywall was detected, it might be paywalled
            if word_count < 100 and is_potentially_paywalled:
                return {
                    'url': url,
                    'title': metadata.get('title', doc.title()),
                    'author': metadata.get('author'),
                    'publication_date': metadata.get('publication_date'),
                    'content': None,
                    'word_count': 0,
                    'is_paywalled': True,
                    'error': f'Article appears to be behind a paywall (extracted only {word_count} words). You can manually paste the content instead.'
                }
            
            return {
                'url': url,
                'title': metadata.get('title', doc.title()),
                'author': metadata.get('author'),
                'publication_date': metadata.get('publication_date'),
                'content': content,
                'word_count': word_count,
                'is_paywalled': is_potentially_paywalled,
                'paywall_warning': 'This article might be behind a paywall' if is_potentially_paywalled and word_count >= 100 else None
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'url': url,
                'error': f'Failed to fetch article: {str(e)}',
                'is_paywalled': False
            }
        except Exception as e:
            return {
                'url': url,
                'error': f'Failed to extract article: {str(e)}',
                'is_paywalled': False
            }
    
    def _extract_text_content(self, soup):
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_metadata(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        # Extract title
        title = None
        # Try Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content')
        # Try regular title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
        metadata['title'] = title
        
        # Extract author
        author = None
        # Try various author meta tags
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[name="article:author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    author = element.get('content')
                else:
                    author = element.get_text().strip()
                if author:
                    break
        
        metadata['author'] = author
        
        # Extract publication date
        pub_date = None
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="article:published_time"]',
            'meta[name="date"]',
            'meta[name="pubdate"]',
            'time[datetime]',
            '.date',
            '.published'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    date_str = element.get('content')
                elif element.name == 'time':
                    date_str = element.get('datetime') or element.get_text().strip()
                else:
                    date_str = element.get_text().strip()
                
                if date_str:
                    pub_date = self._parse_date(date_str)
                    if pub_date:
                        break
        
        metadata['publication_date'] = pub_date.isoformat() if pub_date else None
        
        return metadata
    
    def _extract_title(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else 'Untitled'
    
    def _parse_date(self, date_str):
        # Common date formats
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _is_paywalled(self, html):
        # More specific paywall indicators to reduce false positives
        paywall_indicators = [
            'subscription required',
            'premium content',
            'sign up to continue reading',
            'this article is for subscribers only',
            'become a member to continue',
            'login to continue reading',
            'paywall-message',
            'subscribe to read this article',
            'this content is exclusive to subscribers',
            'upgrade to premium'
        ]
        
        html_lower = html.lower()
        
        # Count how many indicators are found
        indicator_count = sum(1 for indicator in paywall_indicators if indicator in html_lower)
        
        # Only consider it paywalled if multiple strong indicators are present
        # or if very specific paywall messages are found
        strong_indicators = [
            'subscription required',
            'this article is for subscribers only',
            'paywall-message'
        ]
        
        has_strong_indicator = any(indicator in html_lower for indicator in strong_indicators)
        
        # Return True only if we have strong evidence of a paywall
        return has_strong_indicator or indicator_count >= 2
    
    def chunk_content(self, content, max_tokens=3000):
        """
        Split content into chunks that fit within LLM context windows
        """
        if not content:
            return []
        
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(content) <= max_chars:
            return [content]
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            para_length = len(paragraph)
            
            if current_length + para_length > max_chars and current_chunk:
                # Start new chunk
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = para_length
            else:
                current_chunk.append(paragraph)
                current_length += para_length + 2  # +2 for \n\n
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks