"""
Analysis service for critical news analysis
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from bson import ObjectId

from app.models.article import Article
from app.models.analysis import Analysis
from app.services.ai_service import AIService
from app.services.scraping_service import ScrapingService, ScrapingDogService
from app.models.settings import Settings
from app.services.orchestrator_service import IntelligentOrchestrator

                                    
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for analyzing news articles critically"""
    
    def __init__(self, config):
        self.config = config
        self.ai_service = AIService(config)
        
                                               
        from app.services.search_service import SearchService
        self.search_service = SearchService()
        
                                             
        self.orchestrator = IntelligentOrchestrator(self.ai_service, self.search_service)
        self.scraping_service = ScrapingService()                       
        
        logger.info("🔍 ANALYSIS SERVICE inizializzato")
        logger.info(f"   🤖 AI Service: {'✅ Inizializzato' if self.ai_service else '❌ Fallito'}")
        logger.info(f"   🔍 Search Service: {'✅ Inizializzato' if self.search_service else '❌ Fallito'}")
        logger.info(f"   🎼 Orchestrator: {'✅ Inizializzato' if self.orchestrator else '❌ Fallito'}")
        logger.info(f"   🕷️ Scraping Service: {'✅ Inizializzato' if self.scraping_service else '❌ Fallito'}")
    
    def _get_model_for_provider(self, provider: str) -> str:
        """Get the correct model name based on the provider"""
        if provider == 'openai':
            return self.config.get('OPENAI_MODEL', 'gpt-4')
        elif provider == 'anthropic':
            return self.config.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        else:                  
            return self.config.get('OLLAMA_MODEL', 'qwen2:7b-instruct')

    @classmethod
    def with_orchestrator(cls):
        """Create AnalysisService with orchestrator"""
        try:
            from app.services.orchestrator_service import create_orchestrator
            from app.models.settings import Settings
            
                                       
            settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
            
                                               
            ai_config = {
                'OPENAI_API_KEY': settings.openai_api_key,
                'ANTHROPIC_API_KEY': settings.anthropic_api_key,
                'OLLAMA_BASE_URL': 'http://localhost:11434',
                'OLLAMA_MODEL': settings.ai_model,                        
                'OPENAI_MODEL': 'gpt-4',                  
                'ANTHROPIC_MODEL': 'claude-3-5-sonnet-20241022'                  
            }
            
                                                                                 
            service = cls(ai_config)
            
                                    
            logger.info("✅ AnalysisService con orchestrator creato con successo")
            return service
            
        except ImportError:
            logger.warning("⚠️ Orchestrator not available, using direct analysis")
                                       
            settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
            
                                               
            ai_config = {
                'OPENAI_API_KEY': settings.openai_api_key,
                'ANTHROPIC_API_KEY': settings.anthropic_api_key,
                'OLLAMA_BASE_URL': 'http://localhost:11434',
                'OLLAMA_MODEL': settings.ai_model,                        
                'OPENAI_MODEL': 'gpt-4',                  
                'ANTHROPIC_MODEL': 'claude-3-5-sonnet-20241022'                  
            }
            return cls(ai_config)
    
    @classmethod
    def create_default(cls):
        """Create default AnalysisService (without orchestrator)"""
        from app.models.settings import Settings
        
                                   
        settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        
                                           
        ai_config = {
            'OPENAI_API_KEY': settings.openai_api_key,
            'ANTHROPIC_API_KEY': settings.anthropic_api_key,
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'OLLAMA_MODEL': settings.ai_model,                        
            'OPENAI_MODEL': 'gpt-4',                  
            'ANTHROPIC_MODEL': 'claude-3-5-sonnet-20241022'                  
        }
        return cls(ai_config)
    
    def analyze_article_critically(self, article_id: str, provider: str = None, 
                                 language: str = "it") -> Dict[str, Any]:
        logger.info("🚀 INIZIO ANALISI CRITICA ARTICOLO")
        logger.info(f"   📰 Article ID: {article_id}")
        logger.info(f"   🌍 Lingua: {language}")
        logger.info(f"   🤖 Provider: {provider or 'auto'}")
        
        start_time = time.time()
        
        try:
                                       
            article = Article.find_by_id(article_id)
            if not article:
                raise ValueError(f"Article not found: {article_id}")
            
            logger.info(f"   📰 Articolo trovato: {article.title[:100]}...")
            
                                                                     
            logger.info("   💾 Salvataggio analisi con status 'processing'")
            processing_analysis = Analysis(
                article_id=article_id,
                analysis_type="orchestrator_complete",
                provider=provider or "auto",
                model="orchestrator",
                language=language,
                result="",
                status="processing",
                processing_time=0.0,
                error_message=""
            )
            processing_analysis_id = processing_analysis.save()
            logger.info(f"   ✅ Analisi salvata con ID: {processing_analysis_id}")
            
                                                                                  
            logger.info("   🎼 FASE 1: Delegazione all'orchestrator")
            orchestrator_complete_result = self._perform_critical_analysis(article, language, provider)
            
                                                                        
                                                                          
            logger.info("   💾 FASE 2: Aggiornamento analisi esistente con risultati completi")
            
                                                           
            initial_analysis = orchestrator_complete_result['initial_analysis']
            orchestrator_result = orchestrator_complete_result['orchestrator_complete_result']
            
                                                                             
            complete_analysis = {
                'article_id': article_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': time.time() - start_time,
                'success': True,
                'orchestrator_controlled': True,
                'initial_analysis': initial_analysis,
                'status': 'completed'
            }
            
                                                                            
            complete_analysis.update(orchestrator_result)
            
                                             
            logger.info(f"   🔍 Passaggio al salvataggio:")
            logger.info(f"   📝 initial_analysis keys: {list(initial_analysis.keys())}")
            logger.info(f"   🎼 orchestrator_result keys: {list(orchestrator_result.keys())}")
            
                                                                                      
            import json
            
            def clean_for_json(obj):
                """Converte oggetti Python complessi in strutture JSON-compatibili"""
                if isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                                                              
                    return clean_for_json(obj.__dict__)
                elif hasattr(obj, 'value'):
                                 
                    return obj.value
                elif isinstance(obj, (str, int, float, bool)) or obj is None:
                    return obj
                else:
                                                          
                    return str(obj)
            
            clean_complete_analysis = clean_for_json(complete_analysis)
            json_result = json.dumps(clean_complete_analysis, ensure_ascii=False, indent=2)
            
                                                                      
            logger.info("   💾 Aggiornamento analisi esistente nel database")
            try:
                from app import mongo
                mongo.db.analyses.update_one(
                    {'_id': ObjectId(processing_analysis_id)},
                    {'$set': {
                        'provider': provider or 'ollama',
                        'model': self._get_model_for_provider(provider or 'ollama'),
                        'result': json_result,
                        'status': "completed",
                        'processing_time': complete_analysis['processing_time'],
                        'error_message': "",
                        'updated_at': datetime.utcnow()
                    }}
                )
                analysis_id = processing_analysis_id
                logger.info(f"   ✅ Analisi aggiornata con ID: {analysis_id}")
            except Exception as update_error:
                logger.error(f"   ❌ Errore aggiornamento analisi: {update_error}")
                                                   
                analysis_id = self._save_analysis_results(
                article_id, 
                initial_analysis, 
                orchestrator_result, 
                provider, 
                language,
                    complete_analysis['processing_time']
                )
                logger.info(f"   ⚠️ Analisi salvata con metodo fallback, ID: {analysis_id}")
            
            complete_analysis['analysis_id'] = analysis_id
            
            logger.info(f"   ✅ ANALISI COMPLETATA con successo in {complete_analysis['processing_time']:.2f}s")
            logger.info(f"   🆔 Analysis ID: {analysis_id}")
            
            return complete_analysis
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante analisi critica: {e}")
            logger.error("   📍 Stack trace completo:", exc_info=True)
            
            processing_time = time.time() - start_time
            
                                          
            error_analysis = {
                'article_id': article_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': processing_time,
                'success': False,
                'error': str(e),
                'orchestrator_controlled': False,
                'status': 'failed'
            }
            
                                                       
            try:
                from app import mongo
                mongo.db.analyses.update_one(
                    {'_id': ObjectId(processing_analysis_id)},
                    {'$set': {
                        'provider': provider or 'ollama',
                        'model': self._get_model_for_provider(provider or 'ollama'),
                        'result': str(error_analysis),
                        'status': "failed",
                        'processing_time': processing_time,
                        'error_message': f"Errore salvataggio: {e}",
                        'updated_at': datetime.utcnow()
                    }}
                )
                logger.info(f"   ✅ Analisi aggiornata con errore, ID: {processing_analysis_id}")
                return processing_analysis_id
            except Exception as update_error:
                logger.error(f"   ❌ Errore aggiornamento analisi fallita: {update_error}")
                                                    
                analysis = Analysis(
                    article_id=article_id,
                    analysis_type="orchestrator_error",
                    provider=provider or 'ollama',
                    model=self._get_model_for_provider(provider or 'ollama'),
                    language=language,
                    result=str(error_analysis),
                    status="failed",
                    processing_time=processing_time,
                    error_message=f"Errore salvataggio: {e}"
                )
                analysis.save()
                error_id = str(analysis._id)
                logger.info(f"   ⚠️ Analisi di errore salvata con ID: {error_id}")
                return error_id
                
            except Exception as fallback_error:
                logger.error(f"   🚨 ERRORE CRITICO durante salvataggio fallback: {fallback_error}")
                return None

    def _perform_critical_analysis(self, article: Article, language: str, provider: str) -> Dict[str, Any]:
        logger.info("🔍 DELEGAZIONE ANALISI ALL'ORCHESTRATOR")
        logger.info(f"   📰 Titolo articolo: {article.title[:100]}...")
        logger.info(f"   🌍 Lingua: {language}")
        logger.info(f"   🤖 Provider: {provider or 'auto'}")
        
                                                  
                                                                               
        
        try:
                                                                    
            article_dict = {
                '_id': str(article._id),
                'title': article.title,
                'content': article.content,
                'source': article.source,
                'url': article.link,                               
                'date': article.published_date.isoformat() if article.published_date else None,
                'author': article.author
            }
            
            logger.info("   🎼 Chiamata all'orchestrator per analisi completa")
            
                                                              
                                      
                                            
                                          
            orchestrator_result = self.orchestrator.orchestrate_analysis(article_dict, "", language)
            
            logger.info("   ✅ Orchestrator ha completato l'analisi")
            
                                                                          
            if 'initial_analysis' in orchestrator_result:
                initial_analysis = orchestrator_result['initial_analysis']
            else:
                                                      
                initial_analysis = self._create_fallback_analysis(article, language, provider)
            
                                  
            initial_analysis.update({
                        'article_id': str(article._id),
                        'analysis_timestamp': datetime.now().isoformat(),
                        'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                        'language': language,
                        'processing_time': 0,                                
                'success': True,
                'orchestrator_controlled': True                                                    
            })
            
                                                                 
                                                                          
            complete_result = {
                'initial_analysis': initial_analysis,
                'orchestrator_complete_result': orchestrator_result                                            
            }
            
            logger.info(f"   ✅ Analisi iniziale completata dall'orchestrator")
            logger.info(f"   🔍 Risultato orchestrator completo: {list(orchestrator_result.keys())}")
            return complete_result
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante delegazione all'orchestrator: {e}")
            logger.error(f"   📍 Stack trace completo:", exc_info=True)
            
                                            
            fallback_analysis = self._create_fallback_analysis(article, language, provider)
            logger.info(f"   🔄 Analisi fallback creata per errore orchestrator")
            return fallback_analysis

    def _create_fallback_analysis(self, article: Article, language: str, provider: str) -> Dict[str, Any]:
        """Crea un'analisi di fallback quando tutto il resto fallisce"""
        logger.info("🚨 CREAZIONE ANALISI FALLBACK")
        
        return {
            'verosimiglianza': 'media',
            'punti_sospetti': ['Analisi automatica non riuscita - verifica manuale necessaria'],
            'possibili_scenari': ['Sistema temporaneamente non disponibile'],
            'query_strategiche': [f"notizia {article.title[:50]}"],
            'livello_credibilità': 5,
            'raccomandazioni': ['Verifica manuale della notizia', 'Riprova l\'analisi automatica più tardi'],
            'article_id': str(article._id),
            'analysis_timestamp': datetime.now().isoformat(),
            'provider': provider or 'fallback',
            'model': 'fallback',
            'language': language,
            'processing_time': 0,
            'success': False
        }

    def _save_analysis_results(self, article_id: str, initial_analysis: Dict, orchestrator_result: Dict, 
                              provider: str, language: str, processing_time: float) -> Dict[str, Any]:
        """Save analysis results to database"""
        logger.info("   💾 Salvataggio risultati analisi nel database")
        
        try:
                                         
            analysis_data = {
                'article_id': article_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': processing_time,
                'success': True,
                'orchestrator_controlled': True,
                'initial_analysis': initial_analysis,
                'orchestrator_result': orchestrator_result,
                'status': 'completed'
            }
            
                                                                                  
            if 'initial_analysis' in orchestrator_result:
                analysis_data['orchestrator_analysis'] = orchestrator_result['initial_analysis']
            
            if 'final_evaluation' in orchestrator_result:
                analysis_data['final_evaluation'] = orchestrator_result['final_evaluation']
            
            if 'domain_results' in orchestrator_result:
                analysis_data['domain_results'] = orchestrator_result['domain_results']
            
            if 'overall_confidence' in orchestrator_result:
                analysis_data['overall_confidence'] = orchestrator_result['overall_confidence']
            
            if 'primary_domain' in orchestrator_result:
                analysis_data['primary_domain'] = orchestrator_result['primary_domain']
            
                                                                  
            if 'raw_agent_results' in orchestrator_result:
                analysis_data['raw_agent_results'] = orchestrator_result['raw_agent_results']
            
            if 'orchestration_metadata' in orchestrator_result:
                analysis_data['orchestration_metadata'] = orchestrator_result['orchestration_metadata']
            
            if 'raw_orchestration_data' in orchestrator_result:
                analysis_data['raw_orchestration_data'] = orchestrator_result['raw_orchestration_data']
            
            if 'domains_analyzed' in orchestrator_result:
                analysis_data['domains_analyzed'] = orchestrator_result['domains_analyzed']
            
            if 'total_agents' in orchestrator_result:
                analysis_data['total_agents'] = orchestrator_result['total_agents']
            
            if 'successful_agents' in orchestrator_result:
                analysis_data['successful_agents'] = orchestrator_result['successful_agents']
            
            if 'failed_agents' in orchestrator_result:
                analysis_data['failed_agents'] = orchestrator_result['failed_agents']
            
            if 'rounds_executed' in orchestrator_result:
                analysis_data['rounds_executed'] = orchestrator_result['rounds_executed']
            
            if 'total_agents_called' in orchestrator_result:
                analysis_data['total_agents_called'] = orchestrator_result['total_agents_called']
            
                                                               
            import json
            
            def clean_for_json(obj):
                """Converte oggetti Python complessi in strutture JSON-compatibili"""
                if isinstance(obj, dict):
                    return {k: clean_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_for_json(item) for item in obj]
                elif hasattr(obj, '__dict__'):
                                                              
                    return clean_for_json(obj.__dict__)
                elif hasattr(obj, 'value'):
                          
                    return obj.value
                elif hasattr(obj, 'isoformat'):
                              
                    return obj.isoformat()
                else:
                                                       
                    return str(obj) if not isinstance(obj, (int, float, bool, str, type(None))) else obj
            
                                                                 
            clean_analysis_data = clean_for_json(analysis_data)
            
                                        
            json_result = json.dumps(clean_analysis_data, ensure_ascii=False, indent=2)
            logger.info(f"   🧹 Converted analysis_data to clean JSON: {len(json_result)} chars")
            
                                                                       
            analysis = Analysis(
                    article_id=article_id,
                analysis_type="orchestrator_complete",
                provider=provider or 'ollama',
                model=self._get_model_for_provider(provider or 'ollama'),
                    language=language,
                result=json_result,                      
                    status="completed",
                processing_time=processing_time,
                error_message=""
            )
            
            analysis.save()
            analysis_id = str(analysis._id)
            logger.info(f"   📊 Dati salvati: {len(str(analysis_data))} caratteri")
            logger.info(f"   🔍 Campi salvati: {list(analysis_data.keys())}")
            logger.info(f"   📝 Dati completi salvati: {analysis_data}")
            
            return analysis_id
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante salvataggio: {e}")
            logger.error("   📍 Stack trace completo:", exc_info=True)
            
                                                    
            error_analysis = {
                'article_id': article_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': processing_time,
                'success': False,
                'error': f"Errore salvataggio: {e}",
                'orchestrator_controlled': False,
                'status': 'failed',
                'initial_analysis': initial_analysis,
                'orchestrator_result': orchestrator_result
            }
            
            try:
                analysis = Analysis(
                    article_id=article_id,
                    analysis_type="orchestrator_error",
                    provider=provider or 'ollama',
                    model=self._get_model_for_provider(provider or 'ollama'),
                    language=language,
                    result=str(error_analysis),
                    status="failed",
                    processing_time=processing_time,
                    error_message=f"Errore salvataggio: {e}"
                )
                analysis.save()
                error_id = str(analysis._id)
                logger.info(f"   ⚠️ Analisi di errore salvata con ID: {error_id}")
                return error_id
                
            except Exception as fallback_error:
                logger.error(f"   🚨 ERRORE CRITICO durante salvataggio fallback: {fallback_error}")
                return None

    def analyze_custom_text(self, text: str, title: str = "Testo personalizzato", 
                            provider: str = None, language: str = "it") -> Dict[str, Any]:
        """Analyze custom text using orchestrator"""
        logger.info("🚀 INIZIO ANALISI TESTO PERSONALIZZATO")
        logger.info(f"   📝 Titolo: {title}")
        logger.info(f"   📄 Testo: {len(text)} caratteri")
        logger.info(f"   🌍 Lingua: {language}")
        logger.info(f"   🤖 Provider: {provider or 'auto'}")
        
        start_time = time.time()
        
        try:
                                                             
            article_dict = {
                '_id': f'custom_{int(time.time())}',
                'title': title,
                'content': text,
                'source': 'input_utente',
                'url': None,
                'date': datetime.now().isoformat(),
                'author': 'utente'
            }
            
            logger.info("   🎼 Delegazione all'orchestrator per analisi testo personalizzato")
            
                                                              
                                      
                                            
                                          
            orchestrator_result = self.orchestrator.orchestrate_analysis(article_dict, "", language)
            
            logger.info("   ✅ Orchestrator ha completato l'analisi del testo personalizzato")
            
                                                                          
            if 'initial_analysis' in orchestrator_result:
                initial_analysis = orchestrator_result['initial_analysis']
            else:
                                                      
                initial_analysis = {
                    "verosimiglianza": "media",
                    "punti_sospetti": ["Testo personalizzato - analisi non disponibile"],
                    "possibili_scenari": ["Analisi non strutturata"],
                    "query_strategiche": ["Verifica contenuto", "Cerca conferme"],
                    "livello_credibilità": 5,
                    "raccomandazioni": ["Verifica manuale necessaria"],
                    "fallback": True
                }
            
                                  
            initial_analysis.update({
                'article_id': article_dict['_id'],
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': time.time() - start_time,
                'success': True,
                'orchestrator_controlled': True,
                'custom_text': True
            })
            
                                         
            complete_analysis = {
                'article_id': article_dict['_id'],
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': time.time() - start_time,
                'success': True,
                'orchestrator_controlled': True,
                'custom_text_analysis': True,
                'original_text': text,                            
                'custom_title': title,                                  
                'initial_analysis': initial_analysis,
                'orchestrator_result': orchestrator_result,
                'status': 'completed'
            }
            
                                
            logger.info("   💾 Salvataggio analisi nel database...")
            
            try:
                from app.models.analysis import Analysis
                
                                                                           
                import json
                
                def clean_for_json(obj):
                    """Converte oggetti Python complessi in strutture JSON-compatibili"""
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    elif hasattr(obj, '__dict__'):
                                                                  
                        return clean_for_json(obj.__dict__)
                    elif hasattr(obj, 'value'):
                              
                        return obj.value
                    elif hasattr(obj, 'isoformat'):
                                  
                        return obj.isoformat()
                    else:
                                                           
                        return str(obj) if not isinstance(obj, (int, float, bool, str, type(None))) else obj
                
                                                                         
                clean_analysis_data = clean_for_json(complete_analysis)
                json_result = json.dumps(clean_analysis_data, ensure_ascii=False, indent=2)
                
                                                                
                analysis_obj = Analysis(
                    article_id=f"text_{int(time.time())}",                                  
                    analysis_type="custom_text",
                    provider=provider or 'ollama',
                    model=self._get_model_for_provider(provider or 'ollama'),
                    language=language,
                    status="completed",
                    result=json_result,                      
                    processing_time=complete_analysis['processing_time']
                )
                
                                    
                analysis_id = analysis_obj.save()
                logger.info(f"   ✅ Analisi salvata con ID: {analysis_id}")
                
                                                          
                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'status': 'completed',
                    'processing_time': complete_analysis['processing_time'],
                    'message': 'Analisi testo personalizzato completata'
                }
                
            except Exception as save_error:
                logger.error(f"   ❌ Errore salvataggio: {save_error}")
                                                                            
                return {
                    'success': True,
                    'analysis_id': f"temp_{int(time.time())}",
                    'result': complete_analysis,
                    'status': 'completed',
                    'processing_time': complete_analysis['processing_time'],
                    'message': 'Analisi completata (salvataggio fallito)'
                }
            
            logger.info(f"   ✅ ANALISI TESTO PERSONALIZZATO COMPLETATA in {complete_analysis['processing_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante analisi testo personalizzato: {e}")
            logger.error("   📍 Stack trace completo:", exc_info=True)
            
            processing_time = time.time() - start_time
            
                                          
            error_analysis = {
                'article_id': f'custom_{int(time.time())}',
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': processing_time,
                'success': False,
                'error': str(e),
                'orchestrator_controlled': False,
                'custom_text': True,
                'status': 'failed'
            }
            
            return error_analysis
    
    def analyze_url(self, url: str, provider: str = None, language: str = "it") -> Dict[str, Any]:
        """Analyze URL using orchestrator"""
        logger.info("🚀 INIZIO ANALISI URL")
        logger.info(f"   🔗 URL: {url}")
        logger.info(f"   🌍 Lingua: {language}")
        logger.info(f"   🤖 Provider: {provider or 'auto'}")
        
        start_time = time.time()
        
        try:
                                    
            logger.info("   🕷️ FASE 1: Scraping dell'articolo")
            scraper = ScrapingService()
            article_data = scraper.scrape_article(url)
            
            if not article_data:
                raise ValueError("Impossibile estrarre l'articolo dall'URL fornito")
        
            logger.info(f"   ✅ Articolo estratto: {article_data.get('title', 'N/A')[:100]}...")
            
                                                                    
            article_dict = {
                '_id': f'url_{int(time.time())}',
                'title': article_data.get('title', 'Titolo non disponibile'),
                'content': article_data.get('content', 'Contenuto non disponibile'),
                'source': article_data.get('source', url),
                'url': url,
                'date': article_data.get('date', datetime.now().isoformat()),
                'author': article_data.get('author', 'Autore non disponibile')
            }
            
            logger.info("   🎼 FASE 2: Delegazione all'orchestrator per analisi URL")
            
                                                              
                                      
                                            
                                          
            orchestrator_result = self.orchestrator.orchestrate_analysis(article_dict, "", language)
            
            logger.info("   ✅ Orchestrator ha completato l'analisi dell'URL")
            
                                                                          
            if 'initial_analysis' in orchestrator_result:
                initial_analysis = orchestrator_result['initial_analysis']
            else:
                                                      
                initial_analysis = {
                    "verosimiglianza": "media",
                    "punti_sospetti": ["URL - analisi non disponibile"],
                    "possibili_scenari": ["Analisi non strutturata"],
                    "query_strategiche": ["Verifica fonte", "Cerca conferme"],
                    "livello_credibilità": 5,
                    "raccomandazioni": ["Verifica manuale necessaria"],
                    "fallback": True
                }
            
                                  
            initial_analysis.update({
                'article_id': article_dict['_id'],
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': time.time() - start_time,
                'success': True,
                'orchestrator_controlled': True,
                'url_analysis': True,
                'scraped_url': url
            })
            
                                         
            complete_analysis = {
                'article_id': article_dict['_id'],
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': time.time() - start_time,
                'success': True,
                'orchestrator_controlled': True,
                'url_analysis': True,
                'scraped_url': url,
                'scraped_article': article_data,
                'initial_analysis': initial_analysis,
                'orchestrator_result': orchestrator_result,
                'status': 'completed'
            }
            
                                
            logger.info("   💾 Salvataggio analisi URL nel database...")
            
            try:
                from app.models.analysis import Analysis
                
                                                                           
                import json
                
                def clean_for_json(obj):
                    """Converte oggetti Python complessi in strutture JSON-compatibili"""
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    elif hasattr(obj, '__dict__'):
                                                                  
                        return clean_for_json(obj.__dict__)
                    elif hasattr(obj, 'value'):
                              
                        return obj.value
                    elif hasattr(obj, 'isoformat'):
                                  
                        return obj.isoformat()
                    else:
                                                           
                        return str(obj) if not isinstance(obj, (int, float, bool, str, type(None))) else obj
                
                                                                         
                clean_analysis_data = clean_for_json(complete_analysis)
                json_result = json.dumps(clean_analysis_data, ensure_ascii=False, indent=2)
                
                                                                
                analysis_obj = Analysis(
                    article_id=f"url_{int(time.time())}",                         
                    analysis_type="custom_url",
                    provider=provider or 'ollama',
                    model=self._get_model_for_provider(provider or 'ollama'),
                    language=language,
                    status="completed",
                    result=json_result,                      
                    processing_time=complete_analysis['processing_time']
                )
                
                                    
                analysis_id = analysis_obj.save()
                logger.info(f"   ✅ Analisi URL salvata con ID: {analysis_id}")
                
                                                          
                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'status': 'completed',
                    'processing_time': complete_analysis['processing_time'],
                    'message': 'Analisi URL completata'
                }
                
            except Exception as save_error:
                logger.error(f"   ❌ Errore salvataggio URL: {save_error}")
                                                                            
                return {
                    'success': True,
                    'analysis_id': f"temp_url_{int(time.time())}",
                    'result': complete_analysis,
                    'status': 'completed',
                    'processing_time': complete_analysis['processing_time'],
                    'message': 'Analisi URL completata (salvataggio fallito)'
                }
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante analisi URL: {e}")
            logger.error("   📍 Stack trace completo:", exc_info=True)
            
            processing_time = time.time() - start_time
            
                                          
            error_analysis = {
                'article_id': f'url_{int(time.time())}',
                'analysis_timestamp': datetime.now().isoformat(),
                'provider': provider or 'ollama',
                'model': self._get_model_for_provider(provider or 'ollama'),
                'language': language,
                'processing_time': processing_time,
                'success': False,
                'error': str(e),
                'orchestrator_controlled': False,
                'url_analysis': True,
                'scraped_url': url,
                'status': 'failed'
            }
            
            return error_analysis
    
    def get_analysis_history(self, limit: int = 20) -> List[Analysis]:
        """Get recent analysis history"""
        return Analysis.find_recent(limit)
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Recupera un'analisi per ID"""
        logger.info(f"📖 RECUPERO ANALISI PER ID: {analysis_id}")
        
        try:
            analysis = Analysis.find_by_id(analysis_id)
            if analysis:
                logger.info(f"   ✅ Analisi trovata: {analysis._id}")
                logger.info(f"   📊 Status: {analysis.status}")
                logger.info(f"   📝 Tipo: {analysis.analysis_type}")
                
                                                         
                if isinstance(analysis.result, str):
                    logger.info(f"   🔧 Conversione result da stringa a dizionario")
                    try:
                        import json
                        analysis.result = json.loads(analysis.result)
                        logger.info(f"   ✅ Conversione JSON completata")
                    except json.JSONDecodeError as e:
                        logger.error(f"   ❌ Errore parsing JSON: {e}")
                        analysis.result = {}
                
                return analysis.to_dict()
            else:
                logger.warning(f"   ⚠️ Analisi non trovata: {analysis_id}")
                return None
                
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante il recupero: {e}")
            logger.error(f"   📍 Stack trace completo:", exc_info=True)
            return None

    def get_analyses_by_article_id(self, article_id: str) -> list:
        """Recupera tutte le analisi per un articolo"""
        logger.info(f"📖 RECUPERO ANALISI PER ARTICOLO: {article_id}")
        
        try:
            analyses = Analysis.find_by_article_id(article_id)
            logger.info(f"   ✅ Trovate {len(analyses)} analisi")
            
            result = []
            for analysis in analyses:
                                                         
                if isinstance(analysis.result, str):
                    try:
                        import json
                        analysis.result = json.loads(analysis.result)
                    except json.JSONDecodeError:
                        analysis.result = {}
                
                result.append(analysis.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante il recupero: {e}")
            logger.error(f"   📍 Stack trace completo:", exc_info=True)
            return []
    
    def get_agent_icon(self, agent_name: str) -> str:
        """Get icon for agent type"""
        return self.agent_icons.get(agent_name.lower(), '🤖')

    def verify_article(self, article_id: str, language: str = "it") -> Dict[str, Any]:
        """Verify article using external sources (ScrapingDog if available)"""
        try:
                                       
            article = Article.find_by_id(article_id)
            if not article:
                raise ValueError(f"Article not found: {article_id}")
            
                                                           
            settings = Settings.find_by_user_id('default')
            if not settings or not settings.scrapingdog_api_key:
                return {
                    'status': 'no_api_key',
                    'message': 'ScrapingDog API key not configured',
                    'suggestions': [
                        'Configure ScrapingDog API key in settings for verification',
                        'Use manual verification methods'
                    ]
                }
            
                                            
            scrapingdog = ScrapingDogService(settings.scrapingdog_api_key)
            
                                                      
            queries = self._generate_verification_queries(article, language)
            
            verification_results = []
            
            for query in queries[:3]:                      
                try:
                                             
                    news_results = scrapingdog.search_news(query, language, max_results=3)
                    
                                                
                    general_results = scrapingdog.search(query, language, max_results=2)
                    
                                     
                    all_results = news_results + general_results
                    
                    if all_results:
                        verification_results.append({
                            'query': query,
                            'results': all_results,
                            'count': len(all_results)
                        })
                    
                                                        
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error verifying query '{query}': {e}")
                    continue
            
            if verification_results:
                return {
                    'status': 'success',
                    'verification_results': verification_results,
                    'total_queries': len(queries),
                    'successful_queries': len(verification_results),
                    'message': f'Found {sum(r["count"] for r in verification_results)} verification results'
                }
            else:
                return {
                    'status': 'no_results',
                    'message': 'No verification results found',
                    'queries_tried': queries
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Error during verification'
            }
    
    def _generate_verification_queries(self, article: Article, language: str) -> List[str]:
        """Generate search queries for verification"""
        queries = []
        
                                 
        if article.title:
            title_words = article.title.split()[:5]                 
            queries.append(' '.join(title_words))
        
                              
        if article.source and article.title:
            source_words = article.source.split('.')[0].split()[:2]                           
            title_words = article.title.split()[:3]                 
            queries.append(f"{' '.join(source_words)} {' '.join(title_words)}")
        
                                            
        if article.content:
                                                   
            content_words = article.content.split()
            if len(content_words) > 10:
                                                             
                mid_point = len(content_words) // 2
                key_phrase = ' '.join(content_words[mid_point-3:mid_point+3])
                queries.append(key_phrase)
        
                          
        if article.published_date:
            date_str = article.published_date.strftime('%Y-%m-%d')
            if article.title:
                title_words = article.title.split()[:3]
                queries.append(f"{' '.join(title_words)} {date_str}")
        
                                             
        queries = [q.strip() for q in queries if q.strip()]
        queries = list(dict.fromkeys(queries))                                            
        
        return queries[:5]                      

    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera le analisi recenti"""
        logger.info(f"📖 RECUPERO ANALISI RECENTI (limite: {limit})")
        
        try:
            analyses = Analysis.find_recent(limit=limit)
            logger.info(f"   ✅ Trovate {len(analyses)} analisi recenti")
            
            result = []
            for analysis in analyses:
                                                         
                if isinstance(analysis.result, str):
                    try:
                        import json
                        analysis.result = json.loads(analysis.result)
                    except json.JSONDecodeError:
                        analysis.result = {}
                
                result.append(analysis.to_dict())
            
            return result
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante il recupero analisi recenti: {e}")
            logger.error(f"   📍 Stack trace completo:", exc_info=True)
            return []
