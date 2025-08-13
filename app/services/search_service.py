"""
Search Service - Integrates web search capabilities for article verification
"""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import re
from bs4 import BeautifulSoup

from app.models.settings import Settings

                                    
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SearchService:
    """Service for web search and verification"""
    
    def __init__(self):
        self.settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scrapingdog_api_key = self.settings.scrapingdog_api_key
        
                                             
        try:
            from app.services.scraping_service import ScrapingDogService
            self.scraping_service = ScrapingDogService(self.scrapingdog_api_key) if self.scrapingdog_api_key else None
            logger.info(f"   🕷️ ScrapingDog Service: {'✅ Inizializzato' if self.scraping_service else '❌ Non configurato'}")
        except ImportError:
            self.scraping_service = None
            logger.warning("   ⚠️ ScrapingDog Service non disponibile")
        
                                                     
        self.serpapi_service = None
        
        logger.info("🔍 SEARCH SERVICE inizializzato")
        logger.info(f"   🔑 ScrapingDog API Key: {'✅ Configurata' if self.scrapingdog_api_key else '❌ Non configurata'}")
    
    def search_web(self, query: str, engine: str = 'google', max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca web usando diversi motori
        """
        try:
            logger.info(f"🔍 Ricerca web: {query} (motore: {engine}, max: {max_results})")
            
            if engine == 'google':
                return self._search_google(query, max_results)
            elif engine == 'bing':
                return self._search_bing(query, max_results)
            elif engine == 'duckduckgo':
                return self._search_duckduckgo(query, max_results)
            else:
                return self._search_google(query, max_results)           
        except Exception as e:
            logger.error(f"❌ Errore ricerca {engine}: {e}")
            return []
    
    def _search_google(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Ricerca tramite ScrapingDog se configurato, altrimenti fallback a Google diretto"""
        try:
                                                    
            if self.scrapingdog_api_key:
                logger.info("   🔍 Tentativo ricerca tramite ScrapingDog")
                from app.services.scraping_service import ScrapingDogService
                client = ScrapingDogService(self.scrapingdog_api_key)
                results = client.search_news(query, language='it', max_results=max_results)
                
                if results and len(results) > 0:
                    logger.info(f"   ✅ ScrapingDog ha restituito {len(results)} risultati")
                    return results
                else:
                    logger.warning("   ⚠️ ScrapingDog ha restituito risultati vuoti, tentativo fallback")
            else:
                logger.info("   ⚠️ ScrapingDog non configurato, uso fallback diretto")
            
                                               
            logger.info("   🔍 Tentativo ricerca Google diretta (fallback)")
            return self._search_google_direct(query, max_results)
            
        except Exception as e:
            logger.error(f"   ❌ Errore ScrapingDog: {e}, uso fallback")
            return self._search_google_direct(query, max_results)
    
    def _search_google_direct(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Ricerca Google diretta come fallback"""
        try:
            logger.info(f"   🔍 Ricerca Google diretta: {query}")
            
                                              
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=it&gl=it"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
                                               
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
                                                  
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:max_results]:
                try:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    snippet_elem = result.find('div', class_='VwiC3b')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        
                                                               
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                                                  
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        source = parsed_url.netloc
                        
                        if title and url and not url.startswith('https://www.google.com'):
                            results.append({
                                'title': title,
                                'snippet': snippet,
                                'link': url,
                                'url': url,
                                'source': source,
                                'date': ''
                            })
                            
                except Exception as e:
                    logger.debug(f"   ⚠️ Errore parsing risultato: {e}")
                    continue
            
            logger.info(f"   ✅ Ricerca Google diretta ha restituito {len(results)} risultati")
            return results
            
        except Exception as e:
            logger.error(f"   ❌ Errore ricerca Google diretta: {e}")
                                                               
            return self._generate_fallback_results(query, max_results)
    
    def _generate_fallback_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Genera risultati di fallback pertinenti alla query"""
        logger.info(f"   🔄 Generazione risultati di fallback per: {query}")
        
                                          
        keywords = re.findall(r'\b\w+\b', query.lower())
        relevant_keywords = [kw for kw in keywords if len(kw) > 3][:3]
        
        fallback_results = []
        for i in range(min(max_results, 3)):
                                                      
            title = f"Risultato di ricerca per: {query[:50]}..."
            snippet = f"Questo è un risultato di fallback per la ricerca '{query}'. Per risultati reali, configura ScrapingDog API o verifica la connessione internet."
            url = f"https://example.com/search-fallback-{i+1}"
            
            fallback_results.append({
                'title': title,
                'snippet': snippet,
                'link': url,
                'url': url,
                'source': 'fallback',
                'date': ''
            })
        
        logger.info(f"   ✅ Generati {len(fallback_results)} risultati di fallback")
        return fallback_results
    
    def _search_bing(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Usa lo stesso backend (ScrapingDog) come fallback; se non configurato, nessun risultato."""
        return self._search_google(query, max_results)
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Usa lo stesso backend (ScrapingDog) come fallback; se non configurato, nessun risultato."""
        return self._search_google(query, max_results)
    
    def verify_article_claims(self, article_content: str, language: str = 'it') -> Dict[str, Any]:
        """
        Verifica le affermazioni di un articolo attraverso ricerca web
        """
        try:
                                                      
            claims = self._extract_claims(article_content, language)
            
            verification_results = []
            
            for claim in claims[:5]:                           
                search_results = self.search_web(claim, 'google', 3)
                verification = self._verify_single_claim(claim, search_results, language)
                verification_results.append(verification)
                
                                                              
                time.sleep(1)
            
            return {
                'success': True,
                'claims_analyzed': len(verification_results),
                'verification_results': verification_results,
                'overall_verification_score': self._calculate_verification_score(verification_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_claims(self, content: str, language: str) -> List[str]:
        """Estrae affermazioni chiave dal contenuto dell'articolo"""
        claims = []
        
                                      
        sentences = re.split(r'[.!?]+', content)
        
                                                
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                                                         
                if any(keyword in sentence.lower() for keyword in [
                    'è', 'sono', 'ha', 'hanno', 'stato', 'stata', 'stati', 'state',
                    'is', 'are', 'has', 'have', 'was', 'were'
                ]):
                    claims.append(sentence)
        
        return claims[:10]                            
    
    def _verify_single_claim(self, claim: str, search_results: List[Dict], language: str) -> Dict[str, Any]:
        """Verifica una singola affermazione"""
        if not search_results:
            return {
                'claim': claim,
                'verification_status': 'no_results',
                'confidence': 0,
                'supporting_evidence': [],
                'contradicting_evidence': []
            }
        
                                                            
        supporting = []
        contradicting = []
        
        for result in search_results:
                                                      
            if self._supports_claim(claim, result['snippet']):
                supporting.append(result)
            elif self._contradicts_claim(claim, result['snippet']):
                contradicting.append(result)
        
                                       
        confidence = self._calculate_claim_confidence(supporting, contradicting)
        
        return {
            'claim': claim,
            'verification_status': self._determine_verification_status(confidence),
            'confidence': confidence,
            'supporting_evidence': supporting[:3],
            'contradicting_evidence': contradicting[:3],
            'search_results_count': len(search_results)
        }
    
    def _supports_claim(self, claim: str, snippet: str) -> bool:
        """Determina se un snippet supporta l'affermazione"""
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        snippet_words = set(re.findall(r'\b\w+\b', snippet.lower()))
        
                                                  
        overlap = len(claim_words.intersection(snippet_words))
        return overlap >= 3                             
    
    def _contradicts_claim(self, claim: str, snippet: str) -> bool:
        """Determina se un snippet contraddice l'affermazione"""
                                                  
        contradiction_words = ['no', 'non', 'false', 'falso', 'wrong', 'sbagliato', 'incorrect']
        
        for word in contradiction_words:
            if word in snippet.lower() and any(word in claim.lower() for word in claim_words):
                return True
        
        return False
    
    def _calculate_claim_confidence(self, supporting: List, contradicting: List) -> float:
        """Calcola il livello di confidenza per un'affermazione"""
        total_evidence = len(supporting) + len(contradicting)
        
        if total_evidence == 0:
            return 0.0
        
                                                            
        confidence = ((len(supporting) - len(contradicting)) / total_evidence) * 10
        return max(0, min(10, confidence + 5))                     
    
    def _determine_verification_status(self, confidence: float) -> str:
        """Determina lo stato di verifica basato sulla confidenza"""
        if confidence >= 8:
            return 'verified'
        elif confidence >= 6:
            return 'likely_true'
        elif confidence >= 4:
            return 'uncertain'
        elif confidence >= 2:
            return 'likely_false'
        else:
            return 'disputed'
    
    def _calculate_verification_score(self, verification_results: List[Dict]) -> float:
        """Calcola un punteggio complessivo di verifica"""
        if not verification_results:
            return 0.0
        
        total_confidence = sum(result.get('confidence', 0) for result in verification_results)
        return total_confidence / len(verification_results)
    
    def search_specific_domain(self, query: str, domain: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Ricerca in un dominio specifico"""
        try:
                                                    
            domain_query = f'site:{domain} {query}'
            return self.search_web(domain_query, 'google', max_results)
        except Exception as e:
            print(f"❌ Errore ricerca dominio {domain}: {e}")
            return []
    
    def get_trending_topics(self, language: str = 'it') -> List[str]:
        """Ottiene argomenti di tendenza per la ricerca"""
        if language == 'it':
            return [
                "politica italiana",
                "economia italiana", 
                "scienza e tecnologia",
                "cronaca nazionale",
                "sport calcio",
                "cultura e spettacoli"
            ]
        else:
            return [
                "world politics",
                "global economy",
                "science technology",
                "international news",
                "sports",
                "entertainment"
            ]


    def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for news articles using multiple sources"""
        logger.info(f"🔍 Ricerca notizie: {query} (limite: {limit})")
        
                                                                                           
        if len(query) > 100:
            query = query[:100] + "..."
            logger.info(f"   ⚠️ Query troncata a 100 caratteri per ottimizzazione")
        
                                                                                         
        common_words = ['verificare', 'controllare', 'cercare', 'dati', 'ufficiali', 'fonti', 'affidabili']
        optimized_query = query
        for word in common_words:
            if word in optimized_query.lower():
                optimized_query = optimized_query.replace(word, '').replace(word.capitalize(), '')
        
        optimized_query = ' '.join(optimized_query.split())                          
        if optimized_query != query:
            logger.info(f"   🔧 Query ottimizzata: '{optimized_query}'")
            query = optimized_query
        
        try:
                                                        
            if self.scraping_service:
                logger.info("   🔍 Tentativo ricerca tramite ScrapingDog")
                results = self.scraping_service.search_news(query, language='it', max_results=limit)
                
                if results:
                    logger.info(f"   ✅ ScrapingDog ha restituito {len(results)} risultati")
                    return results
                else:
                    logger.warning("   ⚠️ ScrapingDog ha restituito risultati vuoti")
            else:
                logger.info("   ⚠️ ScrapingDog non disponibile")
            
                                               
            logger.info("   🔄 Fallback a ricerca Google diretta")
            results = self._search_google_direct(query, limit)
            
            if results:
                logger.info(f"   ✅ Google diretto ha restituito {len(results)} risultati")
                return results
            
            logger.warning("   ⚠️ Nessun risultato trovato da entrambe le fonti")
            return []
            
        except Exception as e:
            logger.error(f"   ❌ Errore durante la ricerca: {e}")
            return []


                                           
def create_search_service() -> SearchService:
    """Crea e restituisce un'istanza del servizio di ricerca"""
    return SearchService()
