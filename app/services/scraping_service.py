"""
Scraping service for extracting article content
"""

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List
import re
import time
import random
import logging

                   
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingService:
    """Service for scraping article content from URLs"""
    
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        self.timeout = 30
        
    def scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape article content from URL"""
        try:
            logger.info(f"🔍 Scraping article: {url}")
            
            response = requests.get(url, headers={'User-Agent': self.user_agent}, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_data = {
                'title': self._extract_title(soup),
                'content': self._extract_content(soup),
                'author': self._extract_author(soup),
                'source': self._extract_source(url),
                'url': url
            }
            
            if article_data['content']:
                logger.info(f"✅ Article scraped successfully: {article_data['title'][:50]}...")
                return article_data
            else:
                logger.warning(f"⚠️ No content extracted from: {url}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout scraping {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error scraping {url}: {e}")
            return None
    
    def scrape_article_content(self, url: str) -> Optional[str]:
        """Scrape only the article content"""
        article_data = self.scrape_article(url)
        if article_data:
            return article_data['content']
        return None
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is likely a news article"""
        if not url:
            return False
        
                                   
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except:
            return False
        
                                       
        news_domains = [
            'ansa.it', 'repubblica.it', 'corriere.it', 'ilsole24ore.com',
            'reuters.com', 'bbc.co.uk', 'bbc.com', 'cnn.com', 'nytimes.com',
            'washingtonpost.com', 'theguardian.com', 'lemonde.fr', 'spiegel.de'
        ]
        
        domain = urlparse(url).netloc.lower()
        return any(news_domain in domain for news_domain in news_domains)
    
    def _extract_source(self, url: str) -> str:
        """Extract source from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "Unknown"
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
                                          
        title_selectors = [
            'h1',
            '.article-title',
            '.post-title',
            '.entry-title',
            '.headline',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                if len(title) > 10:                           
                    return title
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content"""
                                          
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
                                            
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '.article-body',
            '.post-body',
            '.entry-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                                             
                largest_block = self._find_largest_text_block(content_elem)
                if largest_block:
                    text = largest_block.get_text(separator=' ', strip=True)
                    if len(text) > 100:                          
                        return text
        
                                                    
        largest_block = self._find_largest_text_block(soup)
        if largest_block:
            text = largest_block.get_text(separator=' ', strip=True)
            if len(text) > 100:
                return text
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        author_selectors = [
            '.author',
            '.byline',
            '.author-name',
            '.post-author',
            '.entry-author',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text().strip()
                if author and len(author) > 2:
                    return author
        
        return None
    
    def _find_largest_text_block(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the largest text block in the soup"""
        text_blocks = []
        
        for element in soup.find_all(['p', 'div', 'section']):
            if self._looks_like_article_content(element):
                text_length = len(element.get_text())
                text_blocks.append((text_length, element))
        
        if text_blocks:
                                                        
            text_blocks.sort(key=lambda x: x[0], reverse=True)
            return text_blocks[0][1]
        
        return None
    
    def _looks_like_article_content(self, element: BeautifulSoup) -> bool:
        """Check if an element looks like article content"""
        text = element.get_text().strip()
        
                                          
        if len(text) < 50:
            return False
        
                                    
        links = element.find_all('a')
        if len(links) > len(text) / 20:                  
            return False
        
                                                            
        alphanumeric = sum(1 for c in text if c.isalnum())
        if alphanumeric < len(text) * 0.6:                               
            return False
        
        return True
    
    def _clean_content(self, content: str) -> str:
        """Clean and format the content"""
                                     
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
                                         
        unwanted_patterns = [
            r'Condividi su.*',
            r'Share on.*',
            r'Leggi anche.*',
            r'Read also.*',
            r'Pubblicità.*',
            r'Advertisement.*',
            r'Cookie.*',
            r'Privacy.*'
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()


class ScrapingDogService:
    """Service for using ScrapingDog API for verification searches"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.scrapingdog.com/google"
        logger.info(f"🔍 ScrapingDogService inizializzato con API key: {'✅ Configurata' if api_key else '❌ Non configurata'}")
    
    def search_news(self, query: str, language: str = 'it', max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for news using ScrapingDog"""
        try:
            logger.info(f"🔍 ScrapingDog ricerca: {query} (lingua: {language}, max: {max_results})")
            
            params = {
                'api_key': self.api_key,
                'query': query,
                'gl': 'it' if language == 'it' else 'us',
                'hl': language,
                'num': max_results
            }
            
            logger.info(f"   📤 URL: {self.base_url}")
            logger.info(f"   📤 Parametri: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            logger.info(f"   📥 Status code: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"   📥 Risposta JSON ricevuta: {len(str(data))} caratteri")
            
                                               
            print(f"🚨 RISPOSTA COMPLETA SCRAPINGDOG:")
            print(f"   📥 Status: {response.status_code}")
            print(f"   📥 URL: {response.url}")
            print(f"   📥 Headers: {dict(response.headers)}")
            print(f"   📥 JSON completo: {data}")
            print(f"🚨 FINE RISPOSTA SCRAPINGDOG")
            
                                                       
            logger.info(f"   🔍 Chiavi nella risposta: {list(data.keys())}")
            if 'organic_results' in data:
                logger.info(f"   📊 Primi 2 risultati organici grezzi:")
                for i, result in enumerate(data['organic_results'][:2]):
                    logger.info(f"      Risultato {i+1} grezzo: {result}")
            
            results = []
            
            if 'organic_results' in data:
                organic_results = data['organic_results']
                logger.info(f"   📊 Risultati organici trovati: {len(organic_results)}")
                
                for i, result in enumerate(organic_results[:max_results]):
                    try:
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        link = result.get('link', '')
                        source = result.get('displayed_link', '')
                        date = result.get('date', '')
                        
                                                                  
                        logger.info(f"   📰 Risultato {i+1} parsing:")
                        logger.info(f"      Title: '{title}'")
                        logger.info(f"      Snippet: '{snippet[:100]}...'")
                        logger.info(f"      Link: '{link}'")
                        logger.info(f"      Source: '{source}'")
                        
                                                                                                       
                                                                        
                        
                                                    
                        results.append({
                            'title': title,
                            'snippet': snippet,
                            'link': link,
                            'source': source,
                            'date': date
                        })
                        logger.info(f"      ✅ Aggiunto ai risultati (filtro rimosso)")
                        
                    except Exception as e:
                        logger.error(f"   ❌ Errore parsing risultato {i+1}: {e}")
                        continue
            else:
                logger.warning(f"   ⚠️ Nessun 'organic_results' nella risposta. Chiavi disponibili: {list(data.keys())}")
                if 'error' in data:
                    logger.error(f"   ❌ Errore API: {data['error']}")
            
            logger.info(f"   ✅ Risultati finali filtrati: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"❌ ScrapingDog API error: {e}")
            return []
    
    def search(self, query: str, language: str = 'it', max_results: int = 5) -> List[Dict[str, Any]]:
        """General search using ScrapingDog"""
        return self.search_news(query, language, max_results)
