"""
Enhanced Multi-Source Knowledge Scraper
Supports: Web pages, YouTube transcripts, GitHub repos, local PDFs
Fully offline-capable with intelligent strategy classification
"""
import os
import re
import json
import logging
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
import PyPDF2

from .strategy_domains import classify_content_by_keywords, STRATEGY_DOMAINS

logger = logging.getLogger(__name__)

class EnhancedKnowledgeScraper:
    """
    Multi-source scraper for building strategy-aware knowledge base
    Handles web pages, PDFs, and text files
    """
    
    def __init__(self, data_dir='/Users/macbook/zenithedge_trading_hub/data/knowledge'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZenithEdge-KnowledgeBot/2.0 (Educational Purpose)'
        })
        
        self.robots_cache = {}
        
    def scrape_web_page(self, url: str, strategy: str = None) -> Optional[Dict]:
        """
        Scrape a single web page and extract trading knowledge
        
        Args:
            url: Target URL
            strategy: Optional strategy category hint
            
        Returns:
            Extracted knowledge dict or None
        """
        try:
            # Check robots.txt
            if not self._can_fetch(url):
                logger.warning(f"Robots.txt disallows: {url}")
                return None
            
            # Fetch page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'advertisement']):
                tag.decompose()
            
            # Extract title
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else ''
            
            # Extract main content
            main_content = []
            
            # Try common content containers
            content_areas = soup.find_all(['article', 'main']) or soup.find_all(['div'], class_=re.compile('content|article|post'))
            
            if content_areas:
                for area in content_areas[:1]:  # Take first match
                    for elem in area.find_all(['p', 'h2', 'h3', 'li']):
                        text = elem.get_text(strip=True)
                        if len(text) > 30:  # Filter noise
                            main_content.append(text)
            else:
                # Fallback: extract all paragraphs
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        main_content.append(text)
            
            if not main_content:
                logger.warning(f"No content extracted from {url}")
                return None
            
            # Join content
            full_text = '\n'.join(main_content)
            
            # Auto-classify strategy if not provided
            if not strategy:
                strategies = classify_content_by_keywords(full_text)
                strategy = strategies[0] if strategies else 'ta'
            
            # Extract concept (from title or first sentence)
            concept = self._extract_concept(title_text or main_content[0])
            
            # Build knowledge entry
            knowledge = {
                'strategy': strategy,
                'concept': concept,
                'title': title_text,
                'definition': full_text[:1000],  # First 1000 chars
                'full_text': full_text,
                'examples': self._extract_examples(main_content),
                'source': url,
                'source_type': 'web',
                'timestamp': datetime.now().isoformat(),
                'raw_content': main_content
            }
            
            # Save raw text
            self._save_raw_text(strategy, concept, full_text, url)
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def scrape_pdf(self, pdf_path: str, strategy: str = None) -> List[Dict]:
        """
        Extract knowledge from a local PDF file
        
        Args:
            pdf_path: Path to PDF file
            strategy: Optional strategy category
            
        Returns:
            List of extracted knowledge entries
        """
        try:
            entries = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                full_text = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                
                combined_text = '\n'.join(full_text)
                
                # Auto-classify if needed
                if not strategy:
                    strategies = classify_content_by_keywords(combined_text)
                    strategy = strategies[0] if strategies else 'ta'
                
                # Split into sections (by headings or paragraphs)
                sections = self._split_into_sections(combined_text)
                
                for section in sections:
                    if len(section) < 100:  # Skip too short sections
                        continue
                    
                    concept = self._extract_concept(section[:200])
                    
                    entry = {
                        'strategy': strategy,
                        'concept': concept,
                        'definition': section[:1000],
                        'full_text': section,
                        'examples': self._extract_examples([section]),
                        'source': pdf_path,
                        'source_type': 'pdf',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    entries.append(entry)
                    self._save_raw_text(strategy, concept, section, pdf_path)
                
                logger.info(f"Extracted {len(entries)} entries from {pdf_path}")
                return entries
                
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return []
    
    def scrape_youtube_transcript(self, video_url: str, strategy: str = None) -> Optional[Dict]:
        """
        Extract knowledge from YouTube video transcript (requires youtube-transcript-api)
        
        Args:
            video_url: YouTube video URL
            strategy: Optional strategy category
            
        Returns:
            Extracted knowledge dict or None
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                logger.warning(f"Could not extract video ID from {video_url}")
                return None
            
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine transcript
            full_text = ' '.join([entry['text'] for entry in transcript_list])
            
            # Auto-classify
            if not strategy:
                strategies = classify_content_by_keywords(full_text)
                strategy = strategies[0] if strategies else 'ta'
            
            concept = self._extract_concept(full_text[:200])
            
            knowledge = {
                'strategy': strategy,
                'concept': concept,
                'definition': full_text[:1000],
                'full_text': full_text,
                'examples': self._extract_examples([full_text]),
                'source': video_url,
                'source_type': 'youtube',
                'timestamp': datetime.now().isoformat()
            }
            
            self._save_raw_text(strategy, concept, full_text, video_url)
            
            return knowledge
            
        except ImportError:
            logger.warning("youtube-transcript-api not installed. Install with: pip install youtube-transcript-api")
            return None
        except Exception as e:
            logger.error(f"Error getting transcript from {video_url}: {e}")
            return None
    
    def scrape_github_repo(self, repo_url: str, strategy: str = None) -> List[Dict]:
        """
        Extract knowledge from GitHub repository README and docs
        
        Args:
            repo_url: GitHub repository URL
            strategy: Optional strategy category
            
        Returns:
            List of extracted knowledge entries
        """
        try:
            entries = []
            
            # Convert to raw content URL
            if 'github.com' in repo_url:
                # Get README
                readme_url = repo_url.replace('github.com', 'raw.githubusercontent.com')
                if not readme_url.endswith('/'):
                    readme_url += '/'
                readme_url += 'main/README.md'  # Try main first
                
                response = self.session.get(readme_url, timeout=10)
                if response.status_code == 404:
                    # Try master branch
                    readme_url = readme_url.replace('/main/', '/master/')
                    response = self.session.get(readme_url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Auto-classify
                    if not strategy:
                        strategies = classify_content_by_keywords(content)
                        strategy = strategies[0] if strategies else 'ta'
                    
                    concept = self._extract_concept(content[:200])
                    
                    entry = {
                        'strategy': strategy,
                        'concept': concept,
                        'definition': content[:1000],
                        'full_text': content,
                        'examples': self._extract_code_examples(content),
                        'source': repo_url,
                        'source_type': 'github',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    entries.append(entry)
                    self._save_raw_text(strategy, concept, content, repo_url)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error scraping GitHub repo {repo_url}: {e}")
            return []
    
    def scan_local_docs(self, docs_dir: str = '/Users/macbook/zenithedge_trading_hub/docs/strategies') -> List[Dict]:
        """
        Scan local documents directory for PDFs and text files
        
        Args:
            docs_dir: Directory containing strategy documents
            
        Returns:
            List of all extracted knowledge entries
        """
        all_entries = []
        docs_path = Path(docs_dir)
        
        if not docs_path.exists():
            logger.warning(f"Docs directory does not exist: {docs_dir}")
            return []
        
        # Scan for PDFs
        for pdf_file in docs_path.glob('**/*.pdf'):
            logger.info(f"Processing PDF: {pdf_file}")
            entries = self.scrape_pdf(str(pdf_file))
            all_entries.extend(entries)
        
        # Scan for text/markdown files
        for text_file in docs_path.glob('**/*.{txt,md}'):
            logger.info(f"Processing text file: {text_file}")
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                strategies = classify_content_by_keywords(content)
                strategy = strategies[0] if strategies else 'ta'
                
                concept = self._extract_concept(content[:200])
                
                entry = {
                    'strategy': strategy,
                    'concept': concept,
                    'definition': content[:1000],
                    'full_text': content,
                    'examples': self._extract_examples([content]),
                    'source': str(text_file),
                    'source_type': 'local_file',
                    'timestamp': datetime.now().isoformat()
                }
                
                all_entries.append(entry)
                self._save_raw_text(strategy, concept, content, str(text_file))
                
            except Exception as e:
                logger.error(f"Error reading {text_file}: {e}")
        
        logger.info(f"Scanned local docs: {len(all_entries)} total entries")
        return all_entries
    
    # Helper methods
    
    def _can_fetch(self, url: str) -> bool:
        """Check robots.txt"""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            if base_url not in self.robots_cache:
                robots_url = f"{base_url}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[base_url] = rp
            
            return self.robots_cache[base_url].can_fetch('*', url)
        except:
            return True  # Allow if can't check
    
    def _extract_concept(self, text: str) -> str:
        """Extract main concept from text"""
        # Remove common prefixes
        text = re.sub(r'^(What is|Definition of|Understanding|Learn about)\s+', '', text, flags=re.IGNORECASE)
        
        # Take first sentence or up to 80 chars
        sentences = re.split(r'[.!?]\s+', text)
        concept = sentences[0] if sentences else text[:80]
        
        return concept.strip()
    
    def _extract_examples(self, content_list: List[str]) -> List[str]:
        """Extract example sentences"""
        examples = []
        
        for text in content_list:
            # Look for example patterns
            example_pattern = r'(?:for example|e\.g\.|such as|like|consider)[:\s]([^.!?]+[.!?])'
            matches = re.findall(example_pattern, text, re.IGNORECASE)
            examples.extend([m.strip() for m in matches[:3]])  # Max 3 per text
        
        return examples[:5]  # Max 5 total
    
    def _extract_code_examples(self, markdown_text: str) -> List[str]:
        """Extract code blocks from markdown"""
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', markdown_text, re.DOTALL)
        return [block.strip() for block in code_blocks[:3]]
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into logical sections"""
        # Split by double newlines or heading patterns
        sections = re.split(r'\n\n+|(?:^|\n)#{1,3}\s+', text)
        return [s.strip() for s in sections if len(s.strip()) > 50]
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _save_raw_text(self, strategy: str, concept: str, text: str, source: str):
        """Save raw text to filesystem"""
        strategy_dir = self.data_dir / strategy / 'raw_texts'
        strategy_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean concept for filename
        filename = re.sub(r'[^\w\s-]', '', concept)[:50]
        filename = re.sub(r'[-\s]+', '_', filename)
        
        filepath = strategy_dir / f"{filename}_{int(time.time())}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Source: {source}\n")
            f.write(f"Strategy: {strategy}\n")
            f.write(f"Concept: {concept}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"{'-' * 80}\n\n")
            f.write(text)
        
        logger.debug(f"Saved raw text: {filepath}")


def batch_scrape_urls(urls: List[str], strategy: str = None) -> List[Dict]:
    """
    Scrape multiple URLs in batch
    
    Args:
        urls: List of URLs to scrape
        strategy: Optional strategy category for all URLs
        
    Returns:
        List of extracted knowledge entries
    """
    scraper = EnhancedKnowledgeScraper()
    results = []
    
    for url in urls:
        logger.info(f"Scraping: {url}")
        result = scraper.scrape_web_page(url, strategy)
        if result:
            results.append(result)
        time.sleep(2)  # Rate limiting
    
    return results
