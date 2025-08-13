"""
News service for RSS feed management
"""

import feedparser
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
import html
from urllib.parse import urlparse
import logging

from app.models.article import Article
from app.config import Config

                   
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

                              
import requests

class NewsService:
    """Service for managing news articles from RSS feeds"""
    
    def __init__(self):
                                                                          
        try:
            from app.models.settings import Settings
            settings = Settings.find_by_user_id('default')
            if settings and settings.rss_sources:
                                                                     
                rss_lines = [line.strip() for line in settings.rss_sources.split('\n') if line.strip()]
                self.rss_sources = rss_lines
                logger.info(f"✅ Loaded {len(self.rss_sources)} RSS sources from database settings")
                for i, source in enumerate(self.rss_sources, 1):
                    logger.info(f"   {i}. {source}")
            else:
                                                                
                self.rss_sources = Config.RSS_SOURCES
                logger.warning("⚠️ Using static RSS sources from config (no database settings found)")
        except Exception as e:
            logger.error(f"❌ Error loading RSS sources from settings: {e}")
            self.rss_sources = Config.RSS_SOURCES
            logger.warning("⚠️ Using static RSS sources from config (fallback)")
            
        self.user_agent = "Mozilla/5.0 (compatible; NewsAgentWeb/1.0)"
    
    def fetch_articles_from_rss(self, feed_url: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Fetch articles from a single RSS feed"""
        try:
            logger.info(f"🔄 Fetching RSS feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            
                             
            if hasattr(feed, 'status'):
                logger.info(f"   📡 HTTP Status: {feed.status}")
            if hasattr(feed, 'entries'):
                logger.info(f"   📰 Found {len(feed.entries)} entries in feed")
            else:
                logger.warning(f"   ⚠️ No entries found in feed")
                
            articles = []
            
            for entry in feed.entries[:max_articles]:
                                        
                title = self._clean_text(entry.get('title', ''))
                link = entry.get('link', '')
                summary = self._clean_text(entry.get('summary', ''))
                author = self._clean_text(entry.get('author', ''))
                
                                                        
                content = self._extract_content(entry, summary)
                
                                        
                published_date = self._parse_date(entry.get('published', ''))
                
                                         
                source = self._extract_source_from_url(link)
                
                article_data = {
                    'title': title,
                    'link': link,
                    'source': source,
                    'summary': summary,
                    'content': content,                          
                    'author': author,
                    'published_date': published_date,
                    'language': self._detect_language(title + ' ' + summary)
                }
                
                articles.append(article_data)
            
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error fetching from {feed_url}: {e}")
            return []
    
    def fetch_multiple_sources(self, max_articles_per_source: int = 10) -> List[Dict[str, Any]]:
        """Fetch articles from multiple RSS sources concurrently"""
        all_articles = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
                                    
            future_to_url = {
                executor.submit(self.fetch_articles_from_rss, url, max_articles_per_source): url
                for url in self.rss_sources
            }
            
                             
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    articles = future.result()
                    if articles:
                        all_articles.extend(articles)
                        print(f"✅ {len(articles)} articles from {self._extract_source_from_url(url)}")
                    else:
                        print(f"⚠️ No articles from {self._extract_source_from_url(url)}")
                except Exception as e:
                    print(f"❌ Error from {self._extract_source_from_url(url)}: {e}")
                
                                                         
                time.sleep(0.5)
        
                                                 
                                                               
        articles_with_dates = [a for a in all_articles if a.get('published_date') is not None]
        articles_without_dates = [a for a in all_articles if a.get('published_date') is None]
        
                                        
        articles_with_dates.sort(key=lambda x: x['published_date'], reverse=True)
        
                                                                         
        all_articles = articles_with_dates + articles_without_dates
        
        return all_articles
    
    def save_articles_to_db(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Save articles to MongoDB with enhanced duplicate prevention"""
        saved_ids = []
        duplicates_prevented = 0
        
        logger.info(f"💾 SALVATAGGIO ARTICOLI: {len(articles)} articoli da processare")
        
        for article_data in articles:
            try:
                                                                   
                if self._is_duplicate_article(article_data):
                    duplicates_prevented += 1
                    logger.info(f"   ⚠️ Duplicato prevenuto: {article_data.get('title', 'N/A')[:50]}...")
                    continue
                
                                             
                article = Article(
                    title=article_data['title'],
                    link=article_data['link'],
                    source=article_data['source'],
                    summary=article_data['summary'],
                    content=article_data['content'],
                    author=article_data['author'],
                    published_date=article_data['published_date'],
                    language=article_data['language']
                )
                
                article_id = article.save()
                saved_ids.append(article_id)
                logger.info(f"   ✅ Articolo salvato: {article_data.get('title', 'N/A')[:50]}... (ID: {article_id})")
                
            except Exception as e:
                logger.error(f"   ❌ Errore salvataggio articolo {article_data.get('title', 'No title')}: {e}")
        
        logger.info(f"   📊 RISULTATO SALVATAGGIO: {len(saved_ids)} salvati, {duplicates_prevented} duplicati prevenuti")
        return saved_ids
    
    def _is_duplicate_article(self, article_data: Dict[str, Any]) -> bool:
        """Simplified duplicate detection - ONLY by URL"""
        try:
                                          
            source = article_data.get('source', 'N/A')
            title = article_data.get('title', 'N/A')
            link = article_data.get('link', 'N/A')
            
            logger.info(f"   🔍 CONTROLLO DUPLICATI - Source: {source}, Link: {link[:80]}...")
            
                                                                 
            if article_data.get('link'):
                existing_by_url = Article.find_by_url(article_data['link'])
                if existing_by_url:
                    logger.info(f"   ❌ DUPLICATO per URL: {article_data['link']}")
                    logger.info(f"   📰 Titolo duplicato: {title[:50]}...")
                    return True
                else:
                    logger.info(f"   ✅ URL NUOVO: {article_data['link']}")
            
                                                                    
                                                                            
                                                                                  
                                                                    
                                                                         
            
            return False                                                   
            
        except Exception as e:
            logger.error(f"   ❌ Errore controllo duplicati: {e}")
            return False                                                                 
    
    def _titles_are_similar(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are similar using difflib"""
        try:
            import difflib
            
                              
            norm_title1 = title1.lower().strip()
            norm_title2 = title2.lower().strip()
            
                                  
            similarity = difflib.SequenceMatcher(None, norm_title1, norm_title2).ratio()
            
            return similarity >= threshold
            
        except Exception as e:
            logger.error(f"   ❌ Errore calcolo similarità titoli: {e}")
            return False
    
    def get_recent_articles(self, limit: int = 50, language: str = "it") -> List[Article]:
        """Get recent articles from database"""
        return Article.find_recent(limit, language)
    
    def get_articles_by_source(self, source: str, limit: int = 20) -> List[Article]:
        """Get articles by source"""
        return Article.find_by_source(source, limit)
    
    def _clean_text(self, text: str) -> str:
        """Clean HTML and special characters from text"""
        if not text:
            return ""
        
                          
        text = re.sub('<[^<]+?>', '', text)
        
                                
        text = html.unescape(text)
        
                                    
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)
        
                              
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        
        try:
                                          
            parsed = feedparser._parse_date(date_string)
            if parsed:
                return datetime(*parsed[:6])
        except:
            pass
        
                                    
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_content(self, entry, fallback_summary: str) -> str:
        """Extract content from RSS entry with multiple fallback strategies"""
        try:
                                                            
            if hasattr(entry, 'content') and entry.content:
                for content_item in entry.content:
                    if hasattr(content_item, 'value') and content_item.value:
                        content_text = self._clean_text(content_item.value)
                        if content_text and len(content_text) > len(fallback_summary):
                            logger.info(f"   ✅ Contenuto estratto da 'content' field: {len(content_text)} caratteri")
                            return content_text
            
                                                                
            if hasattr(entry, 'description') and entry.description:
                desc_text = self._clean_text(entry.description)
                if desc_text and len(desc_text) > len(fallback_summary):
                    logger.info(f"   ✅ Contenuto estratto da 'description' field: {len(desc_text)} caratteri")
                    return desc_text
            
                                                                            
            if fallback_summary and len(fallback_summary) > 100:
                logger.info(f"   ⚠️ Usando summary come contenuto: {len(fallback_summary)} caratteri")
                return fallback_summary
            
                                                                          
            if hasattr(entry, 'link') and entry.link:
                try:
                    scraped_content = self._scrape_article_content(entry.link)
                    if scraped_content and len(scraped_content) > len(fallback_summary):
                        logger.info(f"   ✅ Contenuto estratto da scraping URL: {len(scraped_content)} caratteri")
                        return scraped_content
                except Exception as e:
                    logger.warning(f"   ⚠️ Scraping fallito per {entry.link}: {e}")
            
                                                      
            if fallback_summary:
                logger.info(f"   ⚠️ Fallback a summary: {len(fallback_summary)} caratteri")
                return fallback_summary
            
            logger.warning("   ❌ Nessun contenuto estratto")
            return ""
            
        except Exception as e:
            logger.error(f"   ❌ Errore estrazione contenuto: {e}")
            return fallback_summary or ""
    
    def _scrape_article_content(self, url: str) -> str:
        """Scrape article content from URL as fallback"""
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
                                                                            
            html_content = response.text
            
                                               
            text_content = self._clean_text(html_content)
            
                                                                   
            if len(text_content) > 10000:
                text_content = text_content[:10000] + "..."
            
            return text_content
            
        except Exception as e:
            logger.warning(f"   ⚠️ Scraping fallito per {url}: {e}")
            return ""
    
    def _extract_source_from_url(self, url: str) -> str:
        """Extract source name from URL"""
        if not url:
            return "Unknown"
        
        source_map = {
            'ansa.it': 'ANSA',
            'repubblica.it': 'La Repubblica',
            'corriere.it': 'Corriere della Sera',
            'ilsole24ore.com': 'Il Sole 24 Ore',
            'reuters.com': 'Reuters',
            'bbc.co.uk': 'BBC News',
            'adnkronos.com': 'Adnkronos',
            'agi.it': 'AGI'
        }
        
        for domain, name in source_map.items():
            if domain in url:
                return name
        
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return "Unknown"
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        if not text:
            return "it"
        
                                                  
        italian_words = ['il', 'la', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra']
        english_words = ['the', 'a', 'an', 'of', 'in', 'to', 'for', 'with', 'on', 'at']
        
        text_lower = text.lower()
        italian_count = sum(1 for word in italian_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if italian_count > english_count:
            return "it"
        elif english_count > italian_count:
            return "en"
        else:
            return "it"                      
    
    def filter_duplicate_articles(self, new_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out articles that already exist in the database to avoid duplicates"""
        logger.info(f"🔍 Controllo duplicati per {len(new_articles)} articoli")
        
        unique_articles = []
        duplicates_found = 0
        
        for article in new_articles:
                                                             
            if not self._article_exists(article):
                unique_articles.append(article)
            else:
                duplicates_found += 1
                logger.debug(f"   ⚠️ Duplicato trovato: {article.get('title', 'N/A')[:50]}...")
        
        logger.info(f"   ✅ Articoli unici: {len(unique_articles)}")
        logger.info(f"   ⚠️ Duplicati evitati: {duplicates_found}")
        
        return unique_articles
    
    def _article_exists(self, article: Dict[str, Any]) -> bool:
        """Check if an article already exists in the database"""
        try:
                                                       
            if article.get('link'):
                existing = Article.find_by_url(article['link'])
                if existing:
                    return True
            
                                                               
            if article.get('title') and article.get('source'):
                existing = Article.find_by_title_and_source(article['title'], article['source'])
                if existing:
                    return True
            
                                                                          
            if article.get('title'):
                existing = Article.find_similar_title(article['title'])
                if existing:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"   ❌ Errore controllo duplicato: {e}")
                                                                                  
            return True
