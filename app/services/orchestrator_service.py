"""
Orchestrator Service - Multi-level orchestration architecture for news verification
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from collections import Counter

from app.services.ai_service import AIService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_INFO = "needs_info"

class InformationRequest(Enum):
    OFFICIAL_DATA = "official_data"
    VERIFICATION_SOURCES = "verification_sources"
    EXPERT_OPINION = "expert_opinion"
    HISTORICAL_CONTEXT = "historical_context"
    TECHNICAL_DETAILS = "technical_details"

@dataclass
class AgentRequest:
    agent_name: str
    request_type: InformationRequest
    context: Dict[str, Any]
    priority: int = 1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus
    result: Dict[str, Any]
    confidence: float
    processing_time: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class InformationCoordinator:
    """Coordinates information requests between agents"""
    
    def __init__(self, search_service):
        self.search_service = search_service
        self.pending_requests: List[AgentRequest] = []
        self.completed_requests: Dict[str, Any] = {}
        self.max_requests_per_agent = 2                                       
        self.agent_request_counts: Dict[str, int] = {}                                  
        logger.info("🔗 COORDINATORE INFORMAZIONI inizializzato")
    
    def add_request(self, request: AgentRequest) -> bool:
        """Add a new information request if within limits"""
        agent_name = request.agent_name
        
                                               
        current_count = self.agent_request_counts.get(agent_name, 0)
        if current_count >= self.max_requests_per_agent:
            logger.warning(f"   ⚠️ Agente {agent_name} ha raggiunto il limite massimo richieste ({self.max_requests_per_agent})")
            return False
        
        self.pending_requests.append(request)
        self.agent_request_counts[agent_name] = current_count + 1
        logger.info(f"   📋 Richiesta aggiunta: {agent_name} - {request.request_type.value} ({current_count + 1}/{self.max_requests_per_agent})")
        return True
    
    def prioritize_requests(self) -> List[AgentRequest]:
        """Sort requests by priority and dependencies"""
        return sorted(self.pending_requests, key=lambda x: x.priority, reverse=True)
    
    def fulfill_request(self, request: AgentRequest) -> Dict[str, Any]:
        """Fulfill an information request using search service"""
        logger.info(f"   🔍 Soddisfacimento richiesta: {request.agent_name} - {request.request_type.value}")
        
        try:
                                                         
            search_query = self._generate_search_query(request)
            results = self.search_service.search_news(search_query, limit=5)
            
                                                                          
            if self._are_results_irrelevant(results):
                logger.warning(f"   ⚠️ Risultati irrilevanti per {request.agent_name}, uso fallback")
                fallback_data = self._generate_fallback_data(request)
                self.completed_requests[f"{request.agent_name}_{request.request_type.value}"] = fallback_data
                return fallback_data
            
            fulfilled_data = {
                "query": search_query,
                "results": results,
                "fulfillment_time": datetime.now().isoformat(),
                "source": "search_service"
            }
            
            self.completed_requests[f"{request.agent_name}_{request.request_type.value}"] = fulfilled_data
            logger.info(f"   ✅ Richiesta soddisfatta: {request.agent_name}")
            
            return fulfilled_data
            
        except Exception as e:
            logger.error(f"   ❌ Errore soddisfacimento richiesta: {e}")
            fallback_data = self._generate_fallback_data(request)
            self.completed_requests[f"{request.agent_name}_{request.request_type.value}"] = fallback_data
            return fallback_data
    
    def _are_results_irrelevant(self, results: List[Dict]) -> bool:
        """Check if search results are irrelevant (like 'undefined' definitions)"""
        if not results:
            return True
        
        irrelevant_keywords = ['undefined', 'definition', 'meaning', 'javascript', 'mdn', 'dictionary']
        irrelevant_count = 0
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
                                                                                        
            if any(keyword in title or keyword in snippet for keyword in irrelevant_keywords):
                irrelevant_count += 1
        
        return (irrelevant_count / len(results)) > 0.6
    
    def _generate_fallback_data(self, request: AgentRequest) -> Dict[str, Any]:
        """Generate fallback data when search results are irrelevant"""
        return {
            "query": f"fallback_{request.request_type.value}",
            "results": [{"title": "Informazioni non disponibili", "snippet": "Risultati di ricerca non pertinenti", "url": ""}],
            "fulfillment_time": datetime.now().isoformat(),
            "source": "fallback",
            "note": "Risultati originali non pertinenti, utilizzato fallback"
        }
    
    def _generate_search_query(self, request: AgentRequest) -> str:
        """Generate appropriate search query based on request type"""
        base_context = request.context.get('article_title', '')
        
        if request.request_type == InformationRequest.OFFICIAL_DATA:
            return f"dati ufficiali {base_context} fonte istituzionale"
        elif request.request_type == InformationRequest.VERIFICATION_SOURCES:
            return f"verifica {base_context} fonti attendibili"
        elif request.request_type == InformationRequest.EXPERT_OPINION:
            return f"opinione esperto {base_context} analisi specializzata"
        elif request.request_type == InformationRequest.HISTORICAL_CONTEXT:
            return f"contesto storico {base_context} precedenti"
        elif request.request_type == InformationRequest.TECHNICAL_DETAILS:
            return f"dettagli tecnici {base_context} specifiche"
        else:
            return f"informazioni {base_context}"

class DomainOrchestrator:
    """Orchestrates agents within a specific domain"""
    
    def __init__(self, domain_name: str, description: str):
        self.domain_name = domain_name
        self.description = description
        self.agents: List['SpecializedAgent'] = []
        self.information_coordinator: InformationCoordinator = None
        logger.info(f"🎭 DOMAIN ORCHESTRATOR inizializzato: {domain_name} - {description}")
    
    def add_agent(self, agent: 'SpecializedAgent'):
        """Add a specialized agent to this domain"""
        self.agents.append(agent)
        logger.info(f"   🤖 Agente aggiunto: {agent.name}")
    
    def set_information_coordinator(self, coordinator: InformationCoordinator):
        """Set the information coordinator for this domain"""
        self.information_coordinator = coordinator
    
    def orchestrate_domain_analysis(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[AgentResult]:
        """Orchestrate analysis within this domain"""
        logger.info(f"🎭 ORCHESTRAZIONE DOMINIO: {self.domain_name}")
        
        if not self.agents:
            logger.warning(f"   ⚠️ Nessun agente disponibile per il dominio {self.domain_name}")
            return []
        
                                                     
        domain_relevance = self._evaluate_domain_relevance(article_data, initial_analysis)
        if domain_relevance < 0.3:
            logger.info(f"   📊 Dominio {self.domain_name} non rilevante ({domain_relevance:.2f}), salto analisi")
            return []
        
        logger.info(f"   📊 Dominio {self.domain_name} rilevante ({domain_relevance:.2f}), procedo con analisi")
        
                                   
        domain_results = self._execute_domain_agents(article_data, initial_analysis)
        
                                            
        if self.information_coordinator:
            self._handle_information_requests(domain_results)
        
                           
        aggregated_results = self._aggregate_domain_results(domain_results)
        
                                    
        domain_summary = self._create_domain_summary(aggregated_results)
        
        logger.info(f"   ✅ Analisi dominio {self.domain_name} completata: {len(aggregated_results)} risultati")
        return aggregated_results
    
    def _evaluate_domain_relevance(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> float:
        """Evaluate how relevant this domain is to the article"""
                                                                
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        domain_keywords = {
            'scientifico': ['studi', 'ricerca', 'scienza', 'medicina', 'tecnologia'],
            'politico': ['governo', 'politica', 'elezioni', 'parlamento', 'ministro'],
            'tecnologico': ['tecnologia', 'innovazione', 'digitale', 'software', 'ai'],
            'economico': ['economia', 'finanza', 'mercato', 'borsa', 'inflazione', 'prezzi', 'istat'],
            'cronaca': ['cronaca', 'notizie', 'eventi', 'accadimenti'],
            'universale': ['generale', 'notizie', 'informazioni']
        }
        
        keywords = domain_keywords.get(self.domain_name, [])
        relevance_score = 0.0
        
                                                              
        if self.domain_name == 'universale':
            relevance_score = 0.5
        
        for keyword in keywords:
            if keyword in title:
                relevance_score += 0.3
            if keyword in content:
                relevance_score += 0.1
        
        return min(relevance_score, 1.0)
    
    def _execute_domain_agents(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[AgentResult]:
        """Execute all agents in this domain"""
        results = []
        logger.info(f"   🤖 Esecuzione {len(self.agents)} agenti nel dominio")
        
        for agent in self.agents:
            try:
                logger.info(f"   🤖 Esecuzione agente: {agent.name}")
                result = agent.execute_verification_with_fallback(article_data, initial_analysis)
                results.append(result)
                logger.info(f"   ✅ Agente {agent.name} completato: {result.status.value} - confidenza: {result.confidence:.2f}")
                
            except Exception as e:
                logger.error(f"   ❌ Errore agente {agent.name}: {e}")
                logger.error("   📍 Stack trace completo:", exc_info=True)
                                                                 
                fallback_result = AgentResult(
                    agent_name=agent.name,
                    status=AgentStatus.FAILED,
                    result={"error": str(e)},
                    confidence=0.0,
                    processing_time=0.0
                )
                results.append(fallback_result)
        
        logger.info(f"   📊 Totale risultati agenti: {len(results)}")
        return results
    
    def _handle_information_requests(self, domain_results: List[AgentResult]):
        """Handle information requests from domain agents"""
        if not self.information_coordinator:
            return
        
        for result in domain_results:
            if result.status == AgentStatus.NEEDS_INFO:
                                                               
                logger.info(f"   📋 Gestione richiesta info per agente: {result.agent_name}")
                                                                                 
    
    def _aggregate_domain_results(self, domain_results: List[AgentResult]) -> List[AgentResult]:
        """Aggregate results from all domain agents"""
        return domain_results
    
    def _create_domain_summary(self, results: List[AgentResult]) -> Dict[str, Any]:
        """Create a summary of domain analysis results"""
        if not results:
            return {"summary": "Nessun risultato disponibile"}
        
        successful_results = [r for r in results if r.status == AgentStatus.COMPLETED]
        failed_results = [r for r in results if r.status == AgentStatus.FAILED]
        
        summary = {
            "total_agents": len(results),
            "successful_agents": len(successful_results),
            "failed_agents": len(failed_results),
            "average_confidence": sum(r.confidence for r in successful_results) / len(successful_results) if successful_results else 0.0,
            "domain": self.domain_name
        }
        
        return summary
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from agent with robust handling for all AI providers"""
        try:
                                                                        
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                                                    
                parts = response.split('```')
                if len(parts) >= 3:
                    response = parts[1]
            
                                     
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"   ⚠️ Nessun JSON trovato nella risposta")
                return {}
            
            json_str = response[json_start:json_end].strip()
            
                                          
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
                                                                             
            try:
                                                                                             
                                               
                fixed_json = re.sub(r"'([^']+)':", r'"\1":', json_str)
                                                     
                fixed_json = re.sub(r": '([^']*)'", r': "\1"', fixed_json)
                                                   
                fixed_json = re.sub(r"\['([^']+)'\]", r'["\1"]', fixed_json)
                                                              
                fixed_json = re.sub(r"'([^',\[\]{}]+)'", r'"\1"', fixed_json)
                
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                pass
            
                                                                      
            try:
                import ast
                result = ast.literal_eval(json_str)
                if isinstance(result, dict):
                    return result
            except (ValueError, SyntaxError):
                pass
            
                                                           
            try:
                                                               
                extracted = {}
                
                                      
                patterns = {
                    'confidence': r'"?confidence"?\s*:\s*([0-9.]+)',
                    'conferma': r'"?conferma"?\s*:\s*(true|false)',
                    'punteggio_finale': r'"?punteggio_finale"?\s*:\s*([0-9]+)',
                    'verosimiglianza': r'"?verosimiglianza"?\s*:\s*["\']?([^",\'\}]+)["\']?',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, json_str, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if key in ['confidence', 'punteggio_finale']:
                            try:
                                extracted[key] = float(value)
                            except ValueError:
                                pass
                        elif key == 'conferma':
                            extracted[key] = value.lower() == 'true'
                        else:
                            extracted[key] = value.strip('"\'')
                
                if extracted:
                    logger.warning(f"   ⚠️ Parsing parziale riuscito: {list(extracted.keys())}")
                    return extracted
                    
            except Exception:
                pass
            
            logger.error(f"   ❌ Tutti i tentativi di parsing falliti")
            logger.error(f"   📝 Risposta grezza: {response[:500]}...")
            return {}
            
        except json.JSONDecodeError as e:
            logger.error(f"   ❌ Errore parsing JSON: {e}")
            logger.error(f"   📝 Risposta grezza: {response[:200]}...")
            return {}

class SpecializedAgent:
    """Base class for specialized verification agents"""
    
    def __init__(self, name: str, description: str, ai_service: AIService, search_service: SearchService):
        self.name = name
        self.description = description
        self.ai_service = ai_service
        self.search_service = search_service
        self.max_info_requests = 2                                            
        self.info_requests_count = 0                       
        logger.info(f"🔧 AGENTE SPECIALIZZATO inizializzato: {name} - {description}")
    
    def execute_verification_with_fallback(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> AgentResult:
        """Execute verification with fallback to prevent infinite loops"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 ESECUZIONE VERIFICA per agente {self.name}")
            
                                                            
            result = self._execute_verification(article_data, initial_analysis)
            
                                                                                                      
            confidence = result.get('confidence', 0)
            has_error = result.get('error') or result.get('fallback')
            
            if (confidence < 0.4 and                    
                self.info_requests_count < self.max_info_requests and
                not has_error and                                            
                not result.get('fallback')):                                            
                
                logger.info(f"   📋 Confidenza bassa ({confidence:.2f}), richiedo informazioni aggiuntive")
                result = self._execute_verification_with_info(article_data, initial_analysis)
            else:
                if has_error:
                    logger.info(f"   ✅ Non richiedo info aggiuntive: errore o fallback rilevato")
                elif confidence >= 0.4:
                    logger.info(f"   ✅ Confidenza sufficiente ({confidence:.2f}), non richiedo info aggiuntive")
                else:
                    logger.info(f"   ✅ Limite richieste info raggiunto ({self.info_requests_count}/{self.max_info_requests})")
            
                                                                                         
            final_confidence = result.get('confidence', 0)
            if final_confidence < 0.3:
                logger.warning(f"   ⚠️ Confidenza finale troppo bassa ({final_confidence:.2f}), uso fallback forzato")
                result = {
                    "confidence": 0.3,                               
                    "fallback": True,
                    "error": "Confidenza troppo bassa, fallback automatico",
                    "agent_name": self.name,
                    "conferma": False,
                    "punteggio_finale": 3,
                    "verosimiglianza": "bassa",
                    "spiegazione": "Fallback automatico per confidenza insufficiente"
                }
            
                                           
            processing_time = (datetime.now() - start_time).total_seconds()
            
                                   
            final_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                result=result,
                confidence=result.get('confidence', 0.3),                               
                processing_time=processing_time
            )
            
            logger.info(f"   ✅ Verifica completata per {self.name}: confidenza {final_result.confidence:.2f}")
            return final_result
            
        except Exception as e:
            logger.error(f"   ❌ Errore verifica agente {self.name}: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
                                                     
            fallback_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                result={"error": str(e), "fallback": True},
                confidence=0.3,                                      
                processing_time=processing_time
            )
            return fallback_result
    
    def _execute_verification(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute basic verification without additional information"""
        try:
                                                                           
            search_queries = self.generate_search_queries(article_data, initial_analysis)
            
                             
            search_results = self._get_search_results(search_queries)
            
                                                                      
            evaluation = self.evaluate_results(article_data, initial_analysis, search_results)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"   ❌ Errore esecuzione verifica base: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    def _execute_verification_with_info(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute verification with additional information"""
        try:
                                            
            self.info_requests_count += 1
            logger.info(f"   📊 Richiesta info {self.info_requests_count}/{self.max_info_requests} per {self.name}")
            
                                                                   
            enhanced_queries = self._generate_enhanced_queries(article_data, initial_analysis)
            
                                        
            enhanced_results = self._get_search_results(enhanced_queries)
            
                                                                  
            enhanced_evaluation = self.evaluate_results(article_data, initial_analysis, enhanced_results)
            
                                                 
            combined_result = self._combine_evaluations(initial_analysis, enhanced_evaluation)
            
                                                                                                                    
            final_confidence = combined_result.get('confidence', 0)
            if final_confidence < 0.3:
                logger.warning(f"   ⚠️ Confidenza finale troppo bassa ({final_confidence:.2f}) dopo info aggiuntive, uso fallback forzato")
                combined_result = {
                    "confidence": 0.3,                               
                    "fallback": True,
                    "error": "Impossibile ottenere confidenza > 0.3 anche con informazioni aggiuntive",
                    "agent_name": self.name,
                    "conferma": False,
                    "punteggio_finale": 3,
                    "verosimiglianza": "bassa",
                    "spiegazione": "Fallback automatico per confidenza insufficiente anche con info aggiuntive",
                    "raccomandazioni": ["Verificare la qualità delle fonti e la configurazione AI"]
                }
            
            return combined_result
            
        except Exception as e:
            logger.error(f"   ❌ Errore verifica con info aggiuntive: {e}")
            return {
                "error": str(e), 
                "confidence": 0.3,                               
                "fallback": True,
                "agent_name": self.name,
                "conferma": False,
                "punteggio_finale": 3,
                "verosimiglianza": "bassa",
                "spiegazione": f"Errore durante verifica con info aggiuntive: {e}"
            }
    
    def _generate_enhanced_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        """Generate enhanced search queries for additional information - OVERRIDE PER DOMINIO"""
        base_queries = self.generate_search_queries(article_data, initial_analysis)
        enhanced_queries = []
        
        for query in base_queries:
                                                                                 
            domain_terms = self._get_domain_specific_terms(article_data, initial_analysis)
            if domain_terms and isinstance(domain_terms, list):
                                                                                           
                enhanced_query = f"{query} {domain_terms[0]}"
                enhanced_queries.append(enhanced_query)
            else:
                                                           
                enhanced_queries.append(query)
        
        return enhanced_queries
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        """Ritorna termini specifici per il dominio dell'agente - OVERRIDE PER DOMINIO"""
        return []
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        """Ritorna query specifiche per il dominio dell'agente - OVERRIDE PER DOMINIO"""
        return []
    
    def _combine_evaluations(self, base_eval: Dict[str, Any], enhanced_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Combine base and enhanced evaluations"""
        combined = base_eval.copy()
        
                                                                  
        if enhanced_eval.get('confidence', 0) > base_eval.get('confidence', 0):
            combined['confidence'] = enhanced_eval['confidence']
            combined['enhanced_with_additional_info'] = True
        
        return combined
    
    def generate_search_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        """Genera query di ricerca specifiche per l'articolo usando l'LLM"""
        try:
            title = article_data.get('title', '')
            content = article_data.get('content', '')
        
                                                            
            prompt = f"""Sei un esperto di fact-checking. Analizza questo articolo e genera 5 query di ricerca BREVI per verificare la credibilità.

            Titolo: {title}
            Contenuto: {content[:300]}...

            REGOLE IMPORTANTI:
            - Ogni query deve essere BREVE ma mirata
            - Focalizzati sui dati specifici: numeri, percentuali, date, enti
            - Usa termini di ricerca semplici e diretti
            - Evita frasi lunghe e complesse

            Esempio per articolo sull'inflazione:
            "istat inflazione luglio 2025"
            "dati inflazione alimentari luglio"
            "comunicato istat luglio"
            "prezzi alimentari luglio 2025"
            "inflazione istat ufficiale"

            Ora genera 5 query BREVI per questo articolo:"""

            print(f"🔍 PROMPT PER QUERY: {prompt}")
            
                                             
            response = self.ai_service.generate(prompt, max_tokens=200, temperature=0.1)
            
            print(f"🤖 RISPOSTA LLM PER QUERY: {response}")
            
                                                     
            queries = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Esempio') and not line.startswith('"dati ufficiali'):
                                                       
                    line = line.strip('"')
                                                                         
                    if line and line[0].isdigit() and '. ' in line[:3]:
                        line = line.split('. ', 1)[1] if '. ' in line else line
                                                                     
                    line = line.strip('"').strip("'")
                                         
                    line = line.strip()
                    if line:
                        queries.append(line)
            
                              
            final_queries = queries[:5]
            print(f"🎯 QUERY FINALI PARSEATE: {final_queries}")
            logger.info(f"   🔍 Query generate dall'LLM per '{self.name}': {final_queries}")
            
            return final_queries
            
        except Exception as e:
            logger.error(f"   ❌ Errore generazione query con LLM: {e}")
                                       
            fallback_queries = [
                f"verifica {title[:50]}",
                f"fact-checking {title[:50]}",
                "fonti ufficiali notizia",
                "verifica credibilità fonte",
                "dati ufficiali conferma"
            ]
            logger.warning(f"   ⚠️ Fallback a query generiche: {fallback_queries}")
            return fallback_queries
    
    def _extract_article_keywords(self, title: str, content: str) -> List[str]:
        """Estrae parole chiave rilevanti dall'articolo usando l'LLM"""
        try:
                                                         
            prompt = f"""Analizza questo articolo e estrai le 5 parole chiave più rilevanti per la verifica.

            Titolo: {title}
            Contenuto: {content[:500]}...

            Estrai SOLO le parole chiave più importanti per verificare la credibilità della notizia.
            Focalizzati su: enti, dati, percentuali, date, luoghi, nomi specifici.

            Ritorna SOLO una lista di parole chiave, una per riga, nient'altro.

            Esempio:
            istat
            inflazione
            1.7
            luglio
            2025"""

                                                     
            response = self.ai_service.generate(prompt, max_tokens=100, temperature=0.1)
            
                                                             
            keywords = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Esempio:') and not line.startswith('istat'):
                    keywords.append(line)
            
                                      
            final_keywords = keywords[:5]
            logger.info(f"   🎯 Parole chiave estratte dall'LLM: {final_keywords}")
            
            return final_keywords
            
        except Exception as e:
            logger.error(f"   ❌ Errore estrazione parole chiave con LLM: {e}")
                                           
            text = f"{title} {content}".lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            
                                       
            stop_words = {'il', 'la', 'lo', 'gli', 'le', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
                         'a', 'e', 'o', 'ma', 'se', 'che', 'come', 'quando', 'dove', 'perché', 'come',
                         'essere', 'avere', 'fare', 'dire', 'andare', 'venire', 'stare', 'dare',
                         'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
                         'uno', 'una', 'un', 'del', 'della', 'dell', 'dello', 'dei', 'delle'}
            
            words = [word for word in text.split() if len(word) > 3 and word not in stop_words]
            from collections import Counter
            word_freq = Counter(words)
            fallback_keywords = [word for word, freq in word_freq.most_common(5) if freq >= 1]
            
            logger.warning(f"   ⚠️ Fallback a estrazione semplice: {fallback_keywords}")
            return fallback_keywords

    def _get_search_results(self, queries: List[str]) -> str:
        """Get search results for queries using search service"""
        logger.info(f"🔍 ESECUZIONE RICERCHE per agente {self.name}")
        logger.info(f"   📝 Query da eseguire: {len(queries)}")
        
        all_results = []
        
        for i, query in enumerate(queries):
            logger.info(f"   🔍 Ricerca {i+1}/{len(queries)}: {query}")
            
            try:
                                                                  
                results = self.search_service.search_web(query, engine='google', max_results=3)
                
                print(f"🔍 RISULTATI RICERCA '{query}': {results}")
                
                logger.info(f"   ✅ Risultati ricevuti per '{query}': {len(results)} risultati")
                
                if results:
                    query_results = f"🔍 QUERY: {query}\n"
                    for j, result in enumerate(results):
                        title = result.get('title', 'N/A')
                        url = result.get('url') or result.get('link', 'N/A')
                        snippet = result.get('snippet', 'N/A')
                        
                        print(f"📰 RISULTATO {j+1}: Title={title}, URL={url}")
                        
                        query_results += f"   - Titolo: {title}\n"
                        query_results += f"     URL: {url}\n"
                        query_results += f"     Snippet: {snippet}\n"
                    
                    all_results.append(query_results)
                    logger.info(f"   📊 Risultati formattati per '{query}': {len(query_results)} caratteri")
                else:
                    logger.warning(f"   ⚠️ Nessun risultato per '{query}'")
                    all_results.append(f"🔍 QUERY: {query}\n   - Nessun risultato trovato\n")
                    
            except Exception as e:
                logger.error(f"   ❌ Errore ricerca per '{query}': {e}")
                all_results.append(f"🔍 QUERY: {query}\n   - Errore ricerca: {e}\n")
        
                                                                
        if not any('Nessun risultato' not in r for r in all_results):
            logger.info("   🔄 Tentativo con query semplificate")
            simplified_queries = [self._simplify_query(q) for q in queries[:2]]
            
            for query in simplified_queries:
                try:
                                                                      
                    results = self.search_service.search_web(query, engine='google', max_results=2)
                    if results:
                        all_results.append(f"🔍 QUERY SEMPLIFICATA: {query}\n   - Risultati trovati: {len(results)}\n")
                except Exception as e:
                    logger.error(f"   ❌ Errore query semplificata '{query}': {e}")
        
        final_results = "\n---\n".join(all_results)
        logger.info(f"   📊 RISULTATI FINALI: {len(final_results)} caratteri totali")
        return final_results

    def _simplify_query(self, query: str) -> str:
        """Semplifica una query per migliorare i risultati di ricerca"""
                                                   
        simplified = re.sub(r'[^\w\s]', '', query)
        words = simplified.split()[:4]
        return ' '.join(words)

    def evaluate_results(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> Dict[str, Any]:
        """Evaluate search results and provide verification assessment"""
        try:
                                                                 
            prompt = self._prepare_evaluation_prompt(article_data, initial_analysis, search_results)
            
                                                                                              
            ai_response = self.ai_service.generate(prompt, max_tokens=800, temperature=0.2)
            
                                    
            evaluation = self._parse_json_response(ai_response)
            
                               
            evaluation['agent_name'] = self.name
            evaluation['evaluation_timestamp'] = datetime.now().isoformat()
            evaluation['search_results_length'] = len(search_results)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"   ❌ Errore valutazione risultati: {e}")
            return {
                "error": str(e),
                "confidence": 0.0,
                "agent_name": self.name,
                "fallback": True
            }
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        """Prepare the prompt for AI evaluation - OVERRIDE PER DOMINIO"""
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
                                                                                       
        prompt = f"""Sei un analista critico con scetticismo professionale. Valuta la credibilità di questa notizia con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca bias, contraddizioni e fonti non affidabili.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è logicamente plausibile?
        2. QUALITÀ FONTI: Le fonti sono affidabili e indipendenti?
        3. PUNTI SOSPETTI: Quali elementi sembrano sospetti o troppo belli per essere veri?
        4. CONTRADDIZIONI: Ci sono contraddizioni interne o con fonti esterne?
        5. BIAS E INTERESSI: La fonte ha bias o interessi particolari?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e bias identificati]
        - spiegazione: spiegazione dettagliata critica
        - evidenze_a_favore: [lista evidenze a supporto]
        - evidenze_contro: [lista evidenze contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI with robust fallback"""
        try:
                                        
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            
                               
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            json_str = json_match.group() if json_match else response
            json_str = json_str.strip()
            
                                          
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                                                                       
                fixed_json = re.sub(r"'([^']+)':", r'"\1":', json_str)
                fixed_json = re.sub(r": '([^']*)'", r': "\1"', fixed_json)
                fixed_json = re.sub(r"\['([^']+)'\]", r'["\1"]', fixed_json)
                fixed_json = re.sub(r"'([^',\[\]{}]+)'", r'"\1"', fixed_json)
                
                try:
                    parsed = json.loads(fixed_json)
                except json.JSONDecodeError:
                                                                   
                    import ast
                    try:
                        parsed = ast.literal_eval(json_str)
                        if not isinstance(parsed, dict):
                            raise ValueError("Not a dict")
                    except (ValueError, SyntaxError):
                                                      
                        parsed = {}
                        patterns = {
                            'confidence': r'"?confidence"?\s*:\s*([0-9.]+)',
                            'conferma': r'"?conferma"?\s*:\s*(true|false)',
                            'punteggio_finale': r'"?punteggio_finale"?\s*:\s*([0-9]+)',
                            'verosimiglianza': r'"?verosimiglianza"?\s*:\s*["\']?([^",\'\}]+)["\']?',
                        }
                        
                        for key, pattern in patterns.items():
                            match = re.search(pattern, json_str, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                if key in ['confidence', 'punteggio_finale']:
                                    try:
                                        parsed[key] = float(value)
                                    except ValueError:
                                        pass
                                elif key == 'conferma':
                                    parsed[key] = value.lower() == 'true'
                                else:
                                    parsed[key] = value.strip('"\'')
            
                                                              
            if 'confidence' not in parsed or parsed.get('confidence', 0) == 0:
                parsed['confidence'] = 0.5                         
            return parsed
            
        except Exception as e:
            logger.error(f"   ❌ Errore parsing JSON: {e}")
                                                                                     
            return {
                "confidence": 0.4,                                      
                "fallback": True,
                "error": f"Parsing JSON fallito: {e}",
                "conferma": False,
                "punteggio_finale": 4,
                "verosimiglianza": "bassa",
                "punti_sospetti": ["Impossibile analizzare la risposta AI"],
                "spiegazione": "Fallback automatico dovuto a errore di parsing",
                "evidenze_a_favore": [],
                "evidenze_contro": ["Errore tecnico nell'analisi"],
                "raccomandazioni": ["Verificare la configurazione AI e riprovare"]
            }

                                                         
class ScientificAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("scientifico", "Verifica scientifica con scetticismo professionale e focus su metodologia, bias e lacune", ai_service, search_service)
        logger.info(f"🔬 AGENTE SCIENTIFICO inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["studi scientifici peer-reviewed", "ricerca accademica", "metodologia scientifica"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        queries = []
        if any(word in title or word in content for word in ['studi', 'ricerca', 'scienza', 'medicina']):
            queries.extend([
                "Studi scientifici peer-reviewed",
                "Riviste scientifiche reputazione",
                "Ricercatori esperti riconosciuti"
            ])
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista scientifico critico con scetticismo professionale. Valuta la credibilità di questa notizia scientifica con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca bias, lacune metodologiche e contraddizioni.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è logicamente plausibile?
        2. QUALITÀ METODOLOGICA: Ci sono lacune o bias nella ricerca?
        3. FONTI ACCADEMICHE: Le fonti sono realmente peer-reviewed e affidabili?
        4. PUNTI SOSPETTI: Quali elementi sembrano troppo belli per essere veri?
        5. CRITICHE E REPLICHE: Esistono studi contrari o critiche metodologiche?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e bias identificati]
        - qualità_metodologica: "eccellente", "buona", "scarsa", "problematica"
        - fonti_affidabili: [lista fonti scientifiche verificate]
        - criticità_metodologiche: [lista problemi metodologici e bias]
        - studi_contrari: [lista studi o critiche contrarie trovate]
        - spiegazione: spiegazione dettagliata dal punto di vista scientifico critico
        - evidenze_a_favore: [lista evidenze scientifiche a supporto]
        - evidenze_contro: [lista evidenze scientifiche contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class PoliticalAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("politico", "Verifica politica con scetticismo professionale e focus su fonti istituzionali, contraddizioni e timing sospetti", ai_service, search_service)
        logger.info(f"🏛️ AGENTE POLITICO inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["dichiarazioni ufficiali governo", "fonti istituzionali", "comunicati ufficiali"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        queries = []
        if any(word in title or word in content for word in ['politica', 'governo', 'ministro', 'parlamento']):
            queries.extend([
                "Dichiarazioni governo ufficiali",
                "Fonti istituzionali riconosciute",
                "Eventi politici cronologia"
            ])
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista politico critico con scetticismo professionale. Valuta la credibilità di questa notizia politica con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca contraddizioni, timing sospetti e bias politici.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è logicamente plausibile?
        2. FONTI ISTITUZIONALI: Le fonti sono realmente ufficiali e affidabili?
        3. CONTRADDIZIONI: Ci sono contraddizioni tra diverse dichiarazioni?
        4. TIMING SOSPETTO: Il timing dell'annuncio è strategico o sospetto?
        5. BIAS POLITICI: La fonte ha interessi o bias politici particolari?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e contraddizioni]
        - credibilità_politica: "alta", "media", "bassa"
        - fonti_istituzionali: [lista fonti ufficiali verificate]
        - dichiarazioni_verificate: [lista dichiarazioni confermate]
        - contraddizioni_trovate: [lista contraddizioni e discrepanze]
        - timing_sospetto: "sì", "no", "possibile" con spiegazione
        - bias_politici: [lista possibili bias o interessi identificati]
        - spiegazione: spiegazione dettagliata dal punto di vista politico critico
        - evidenze_a_favore: [lista evidenze politiche a supporto]
        - evidenze_contro: [lista evidenze politiche contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class TechnologyAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("tecnologico", "Verifica tecnologica con scetticismo professionale e focus su fattibilità, brevetti e hype tecnologico", ai_service, search_service)
        logger.info(f"💻 AGENTE TECNOLOGICO inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["brevetti documentazione tecnica", "specifiche tecniche", "esperti settore"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        queries = []
        if any(word in title or word in content for word in ['tecnologia', 'innovazione', 'software', 'ai', 'startup']):
            queries.extend([
                "Brevetti documentazione tecnica",
                "Aziende tecnologiche reputazione",
                "Esperti settore tecnologico"
            ])
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista tecnologico critico con scetticismo professionale. Valuta la credibilità di questa notizia tecnologica con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca hype tecnologico, limitazioni tecniche e fattibilità irrealistica.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è tecnologicamente plausibile?
        2. FATTIBILITÀ TECNICA: La tecnologia descritta è realmente fattibile?
        3. BREVETTI E DOCUMENTAZIONE: Esistono prove tecniche concrete?
        4. ESPERTI VERIFICATI: Gli esperti citati sono realmente competenti?
        5. HYPE TECNOLOGICO: La notizia sembra eccessivamente promettente?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e hype identificato]
        - fattibilità_tecnica: "alta", "media", "bassa", "irrealistica"
        - brevetti_trovati: [lista brevetti correlati verificati]
        - documentazione_tecnica: [lista documenti tecnici trovati]
        - esperti_verificati: [lista esperti riconosciuti]
        - limitazioni_tecniche: [lista limitazioni e critiche tecniche]
        - hype_tecnologico: "alto", "medio", "basso" con spiegazione
        - spiegazione: spiegazione dettagliata dal punto di vista tecnologico critico
        - evidenze_a_favore: [lista evidenze tecnologiche a supporto]
        - evidenze_contro: [lista evidenze tecnologiche contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class EconomicAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("economico", "Verifica economica con scetticismo professionale e focus su dati statistici ufficiali, fonti finanziarie e manipolazione", ai_service, search_service)
        logger.info(f"💰 AGENTE ECONOMICO inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["dati statistici ufficiali istat", "fonti finanziarie ufficiali", "dati borsa"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', 'N/A').lower()
        content = article_data.get('content', 'N/A').lower()
        
        queries = []
        if any(word in title or word in content for word in ['economia', 'inflazione', 'prezzi', 'mercato', 'borsa', 'finanza']):
            queries.extend([
                "Dati Istat inflazione ufficiali",
                "Banca d'Italia comunicazioni ufficiali",
                "Quotazioni borsa dati ufficiali"
            ])
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista economico critico con scetticismo professionale. Valuta la credibilità di questa notizia economica con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca manipolazioni, distorsioni e bias economici.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è economicamente plausibile?
        2. DATI STATISTICI UFFICIALI: I dati sono realmente ufficiali e verificabili?
        3. FONTI FINANZIARIE: Le fonti sono affidabili e indipendenti?
        4. MANIPOLAZIONE: I dati potrebbero essere manipolati o distorti?
        5. BIAS ECONOMICI: La fonte ha interessi economici particolari?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e possibili manipolazioni]
        - credibilità_economica: "alta", "media", "bassa"
        - dati_statistici_verificati: [lista dati ufficiali trovati]
        - fonti_finanziarie: [lista fonti finanziarie affidabili]
        - coerenza_economica: "alta", "media", "bassa"
        - possibili_manipolazioni: [lista possibili distorsioni o manipolazioni]
        - bias_economici: [lista possibili bias o interessi economici]
        - spiegazione: spiegazione dettagliata dal punto di vista economico critico
        - evidenze_a_favore: [lista evidenze economiche a supporto]
        - evidenze_contro: [lista evidenze economiche contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class CronacaAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("cronaca", "Verifica cronaca con scetticismo professionale e focus su fonti giornalistiche affidabili, verifiche incrociate e bias mediatici", ai_service, search_service)
        logger.info(f"📰 AGENTE CRONACA inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["fonti giornalistiche affidabili", "verifiche incrociate", "comunicati ufficiali"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', '').lower()
        content = article_data.get('content', '').lower()
        
        queries = []
        if any(word in title or word in content for word in ['cronaca', 'notizie', 'eventi', 'accadimenti']):
            queries.extend([
                "Giornali affidabili stessa notizia",
                "Comunicati forze dell'ordine",
                "Eventi cronologia verificabile"
            ])
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista giornalistico critico con scetticismo professionale. Valuta la credibilità di questa notizia di cronaca con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale, cerca bias mediatici, clickbait e sensazionalismo.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è logicamente plausibile?
        2. FONTI GIORNALISTICHE: Le fonti sono realmente affidabili e indipendenti?
        3. VERIFICHE INCROCIATE: Altri media riportano la stessa notizia?
        4. BIAS MEDIATICI: La notizia ha elementi di sensazionalismo o clickbait?
        5. CRONOLOGIA EVENTI: La sequenza degli eventi è coerente e verificabile?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e possibili bias]
        - credibilità_giornalistica: "alta", "media", "bassa"
        - fonti_verificate: [lista fonti giornalistiche affidabili]
        - verifiche_incrociate: [lista verifiche trovate]
        - coerenza_eventi: "alta", "media", "bassa"
        - bias_mediatici: [lista possibili bias o sensazionalismo]
        - clickbait: "sì", "no", "possibile" con spiegazione
        - spiegazione: spiegazione dettagliata dal punto di vista giornalistico critico
        - evidenze_a_favore: [lista evidenze di cronaca a supporto]
        - evidenze_contro: [lista evidenze di cronaca contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class UniversalAgent(SpecializedAgent):
    def __init__(self, ai_service: AIService, search_service: SearchService):
        super().__init__("universale", "Verifica generale con scetticismo professionale e approccio multidisciplinare critico", ai_service, search_service)
        logger.info(f"🌍 AGENTE UNIVERSALE inizializzato")
    
    def _get_domain_specific_terms(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        return ["verifica generale credibilità", "fact-checking", "fonti affidabili"]
    
    def _get_domain_specific_queries(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any]) -> List[str]:
        title = article_data.get('title', 'N/A').lower()
        content = article_data.get('content', 'N/A').lower()
        
        queries = [
            "Fonte notizia credibilità",
            "Fact-checking precedenti",
            "Coerenza logica informazioni"
        ]
        return queries
    
    def _prepare_evaluation_prompt(self, article_data: Dict[str, Any], initial_analysis: Dict[str, Any], search_results: str) -> str:
        title = article_data.get('title', 'N/A')
        content = article_data.get('content', 'N/A')[:500] + "..." if len(article_data.get('content', '')) > 500 else article_data.get('content', 'N/A')
        
        prompt = f"""Sei un analista generale critico con scetticismo professionale. Valuta la credibilità complessiva di questa notizia con estrema cautela.

        Articolo: {title}
        Contenuto: {content}
        Analisi iniziale: {initial_analysis}

        Informazioni aggiuntive: {search_results}

        Agente: {self.name}
        Descrizione: {self.description}

        APPROCCIO CRITICO: Analizza con scetticismo professionale multidisciplinare, cerca bias generali, contraddizioni e fonti non affidabili.

        FOCUS SPECIFICO:
        1. VEROSIMIGLIANZA INTRINSECA: La notizia è logicamente plausibile?
        2. QUALITÀ FONTI: Le fonti sono affidabili e indipendenti?
        3. COERENZA LOGICA: Le informazioni sono coerenti e non contraddittorie?
        4. BIAS GENERALI: La fonte ha bias o interessi particolari?
        5. FACT-CHECKING: Esistono verifiche precedenti su argomenti simili?

        Fornisci una valutazione critica completa con:
        - conferma: true/false
        - punteggio_finale: 1-10
        - verosimiglianza: "alta", "media", "bassa"
        - punti_sospetti: [lista elementi sospetti e possibili bias]
        - credibilità_complessiva: "alta", "media", "bassa"
        - qualità_fonti: "eccellente", "buona", "scarsa"
        - coerenza_logica: "alta", "media", "bassa"
        - fact_checking_precedenti: [lista verifiche precedenti trovate]
        - bias_generali: [lista possibili bias o interessi identificati]
        - contraddizioni_logiche: [lista contraddizioni e incoerenze]
        - spiegazione: spiegazione dettagliata generale critica
        - evidenze_a_favore: [lista evidenze generali a supporto]
        - evidenze_contro: [lista evidenze generali contrarie]
        - raccomandazioni: [suggerimenti per verifiche ulteriori]

        Ritorna SOLO JSON valido, nient'altro."""
        
        return prompt

class PrimaryOrchestrator:
    """Primary orchestrator that coordinates domain orchestrators"""
    
    def __init__(self, ai_service: AIService, search_service: SearchService):
        self.ai_service = ai_service
        self.search_service = search_service
        self.information_coordinator = InformationCoordinator(search_service)
        
                                         
        self.domain_orchestrators = {
            'scientifico': DomainOrchestrator('scientifico', 'Verifica scientifica e medica'),
            'politico': DomainOrchestrator('politico', 'Verifica politica e istituzionale'),
            'tecnologico': DomainOrchestrator('tecnologico', 'Verifica tecnologica e innovazione'),
            'economico': DomainOrchestrator('economico', 'Verifica economica e finanziaria'),
            'cronaca': DomainOrchestrator('cronaca', 'Verifica cronaca locale e nazionale'),
            'universale': DomainOrchestrator('universale', 'Verifica generale dei fatti')
        }
        
                             
        self._setup_domain_agents()
        
                                                                                               
        self.called_agents = set()
        self.called_domains = set()
        
        logger.info("🎼 PRIMARY ORCHESTRATOR inizializzato")
        logger.info(f"   🎭 Domini disponibili: {list(self.domain_orchestrators.keys())}")
    
    def _setup_domain_agents(self):
        """Setup specialized agents in their respective domains"""
        logger.info("   🤖 Configurazione agenti nei domini")
        
                           
        scientific_agent = ScientificAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['scientifico'].add_agent(scientific_agent)
        
                          
        political_agent = PoliticalAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['politico'].add_agent(political_agent)
        
                           
        technology_agent = TechnologyAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['tecnologico'].add_agent(technology_agent)
        
                         
        economic_agent = EconomicAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['economico'].add_agent(economic_agent)
        
                     
        cronaca_agent = CronacaAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['cronaca'].add_agent(cronaca_agent)
        
                          
        universal_agent = UniversalAgent(self.ai_service, self.search_service)
        self.domain_orchestrators['universale'].add_agent(universal_agent)
        
                                                     
        for domain in self.domain_orchestrators.values():
            domain.set_information_coordinator(self.information_coordinator)
        
        logger.info("   🤖 Agenti configurati nei domini")
    
    def orchestrate_analysis(self, article: Dict[str, Any], analysis: str, language: str = 'it') -> Dict[str, Any]:
        """Orchestrate the complete analysis process with iterative agent calling"""
        logger.info("🎼 INIZIO ORCHESTRAZIONE INTELLIGENTE")
        start_time = datetime.now()
        
                                                          
        self.called_agents.clear()
        self.called_domains.clear()
        logger.info("   🔄 Reset controllo anti-duplicati per nuova analisi")
        
        try:
                                                                       
            if not analysis or analysis.strip() == "":
                logger.info("   📝 Generazione analisi iniziale da parte dell'orchestrator")
                analysis_dict = self._generate_initial_analysis(article, language)
                logger.info("   ✅ Analisi iniziale generata dall'orchestrator")
            else:
                                                       
                if isinstance(analysis, str):
                    try:
                        analysis_dict = json.loads(analysis)
                    except json.JSONDecodeError:
                        analysis_dict = {"raw_analysis": analysis}
                else:
                    analysis_dict = analysis
            
                                                         
            selected_domains = self._make_strategic_routing_decision(article, analysis_dict)
            logger.info(f"   🎯 Domini selezionati inizialmente: {selected_domains}")
            
                                                
            logger.info("   🔄 ROUND 1: Prima chiamata agli agenti")
            first_round_results = self._execute_domain_orchestrators(article, analysis_dict, selected_domains)
            
                                                                               
            logger.info("   📊 Valutazione risultati primo round")
            needs_more_agents = self._evaluate_if_needs_more_agents(first_round_results, article)
            
            second_round_results = []
            if needs_more_agents:
                logger.info("   🔄 ROUND 2: Chiamata ad agenti aggiuntivi")
                additional_domains = self._identify_additional_domains_needed(first_round_results, article)
                second_round_results = self._execute_domain_orchestrators(article, analysis_dict, additional_domains)
            
                                                         
            all_results = first_round_results + second_round_results
            logger.info(f"   🔗 Sintesi finale di {len(all_results)} risultati")
            
            final_result = self._synthesize_final_result(article, analysis_dict, all_results)
            
                                                                
            final_result['initial_analysis'] = analysis_dict
            
                                       
            processing_time = (datetime.now() - start_time).total_seconds()
            final_result['processing_time'] = processing_time
            final_result['rounds_executed'] = 2 if needs_more_agents else 1
            final_result['total_agents_called'] = len(all_results)
            
                                           
            final_result['orchestration_metadata'] = {
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "rounds_executed": 2 if needs_more_agents else 1,
                "total_agents_called": len(all_results),
                "domains_selected_round1": selected_domains,
                "domains_called_round2": additional_domains if needs_more_agents else [],
                "orchestration_strategy": "intelligent_multi_round",
                "confidence_threshold": 0.4,
                "max_rounds": 2,
                "needs_more_agents": needs_more_agents,
                "orchestrator_version": "2.0",
                "ai_provider": "ollama",                                   
                "model": "qwen2:7b-instruct"                                   
            }
            
                                                
            final_result['raw_orchestration_data'] = {
                "first_round_results": [self._result_to_dict_detailed(r) if hasattr(r, '__iter__') else self._result_to_dict_detailed([r]) for r in first_round_results],
                "second_round_results": [self._result_to_dict_detailed(r) if hasattr(r, '__iter__') else self._result_to_dict_detailed([r]) for r in second_round_results] if needs_more_agents else [],
                "all_results_combined": self._result_to_dict_detailed(all_results)
            }
            
            logger.info(f"   ✅ ORCHESTRAZIONE COMPLETATA in {processing_time:.2f}s - {final_result['rounds_executed']} round")
            return final_result
            
        except Exception as e:
            logger.error(f"   ❌ ERRORE orchestrazione primaria: {e}")
            logger.error("   📍 Stack trace completo:", exc_info=True)
            return self._create_fallback_result(article, str(e))
    
    def _make_strategic_routing_decision(self, article: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Make strategic decision about which domains to use"""
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
                                               
        selected_domains = ['universale']                            
        
                                                                               
        economic_keywords = ['economia', 'inflazione', 'prezzi', 'mercato', 'borsa', 'finanza', 'investimenti', 
                           'oro', 'petrolio', 'euro', 'dollaro', 'istat', 'pil', 'debito', 'spread', 'azioni',
                           'quotazioni', 'trading', 'banche', 'banche centrali', 'politica monetaria']
        if any(word in title or word in content for word in economic_keywords):
            selected_domains.append('economico')
            logger.info(f"   💰 Dominio economico selezionato per parole chiave: {[w for w in economic_keywords if w in title or w in content]}")
        
                                                         
        political_keywords = ['politica', 'governo', 'ministro', 'parlamento', 'elezioni', 'partito', 'coalizione',
                            'presidente', 'senato', 'camera', 'decreto legge', 'legge', 'riforma']
        if any(word in title or word in content for word in political_keywords):
                                                                
            political_word_count = sum(1 for word in political_keywords if word in title or word in content)
            if political_word_count >= 2:                                                       
                selected_domains.append('politico')
                logger.info(f"   🏛️ Dominio politico selezionato per parole chiave: {[w for w in political_keywords if w in title or w in content]}")
        
                             
        tech_keywords = ['tecnologia', 'innovazione', 'digitale', 'software', 'ai', 'intelligenza artificiale', 'startup',
                        'app', 'social media', 'blockchain', 'cryptocurrency', 'robot', 'automazione']
        if any(word in title or word in content for word in tech_keywords):
            selected_domains.append('tecnologico')
            logger.info(f"   💻 Dominio tecnologico selezionato per parole chiave: {[w for w in tech_keywords if w in title or w in content]}")
        
                             
        scientific_keywords = ['scienza', 'ricerca', 'studi', 'medicina', 'università', 'laboratorio', 'scoperta',
                             'ricercatori', 'pubblicazione', 'peer review', 'metodologia', 'esperimenti']
        if any(word in title or word in content for word in scientific_keywords):
            selected_domains.append('scientifico')
            logger.info(f"   🔬 Dominio scientifico selezionato per parole chiave: {[w for w in scientific_keywords if w in title or w in content]}")
        
                                                       
        news_keywords = ['cronaca', 'notizie', 'eventi', 'accadimenti', 'incidente', 'arresto', 'procedimento',
                        'delitto', 'furto', 'rapina', 'incidente stradale', 'terremoto', 'alluvione']
        if any(word in title or word in content for word in news_keywords):
                                                                
            news_word_count = sum(1 for word in news_keywords if word in title or word in content)
            if news_word_count >= 2:                                                       
                selected_domains.append('cronaca')
                logger.info(f"   📰 Dominio cronaca selezionato per parole chiave: {[w for w in news_keywords if w in title or w in content]}")
        
                                                                   
        if len(selected_domains) > 3:
                                                            
            priority_domains = ['universale']
            domain_scores = {}
            
            for domain in selected_domains:
                if domain != 'universale':
                    score = 0
                    if domain == 'economico' and any(word in title or word in content for word in economic_keywords):
                        score += 3                                         
                    elif domain == 'scientifico' and any(word in title or word in content for word in scientific_keywords):
                        score += 2
                    elif domain == 'tecnologico' and any(word in title or word in content for word in tech_keywords):
                        score += 2
                    elif domain == 'politico' and any(word in title or word in content for word in political_keywords):
                        score += 1
                    elif domain == 'cronaca' and any(word in title or word in content for word in news_keywords):
                        score += 1
                    domain_scores[domain] = score
            
                                                         
            top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            priority_domains.extend([domain for domain, score in top_domains])
            
            selected_domains = priority_domains
            logger.info(f"   ⚠️ Limite domini raggiunto, selezionati i più rilevanti: {selected_domains}")
        
                                                               
        selected_domains = [domain for domain in selected_domains if domain not in self.called_domains]
        
                                               
        self.called_domains.update(selected_domains)
        
        logger.info(f"   🎯 Routing strategico finale: {selected_domains}")
        logger.info(f"   🚫 Domini già chiamati: {list(self.called_domains)}")
        return selected_domains
    
    def _execute_domain_orchestrators(self, article: Dict[str, Any], analysis: Dict[str, Any], domains: List[str]) -> List[Any]:
        """Execute domains in parallel"""
        results = []
        logger.info(f"   🎭 Esecuzione {len(domains)} domini: {domains}")
        
        for domain_name in domains:
            if domain_name in self.domain_orchestrators:
                try:
                    logger.info(f"   🎭 Avvio dominio: {domain_name}")
                    result = self.domain_orchestrators[domain_name].orchestrate_domain_analysis(article, analysis)
                    logger.info(f"   ✅ Dominio {domain_name} completato con {len(result) if isinstance(result, list) else 0} risultati")
                    results.append(result)
                except Exception as e:
                    logger.error(f"   ❌ Dominio {domain_name} fallito: {e}")
                    logger.error("   📍 Stack trace completo:", exc_info=True)
            else:
                logger.warning(f"   ⚠️ Dominio non trovato: {domain_name}")
        
        logger.info(f"   📊 Totale risultati domini: {len(results)}")
        return results
    
    def _evaluate_if_needs_more_agents(self, first_round_results: List[Any], article: Dict[str, Any]) -> bool:
        """Evaluate if we need to call additional agents based on first round results"""
        logger.info("   📊 Valutazione necessità agenti aggiuntivi")
        
                                             
        if not first_round_results:
            logger.info("   ⚠️ Nessun risultato primo round, servono più agenti")
            return True
        
                                                                                     
        flattened_results = []
        
        def flatten_recursively(item):
            """Appiattisce ricorsivamente liste annidate"""
            if isinstance(item, list):
                for subitem in item:
                    flatten_recursively(subitem)
            elif hasattr(item, 'agent_name') or (isinstance(item, dict) and 'agent_name' in item):
                                       
                flattened_results.append(item)
            else:
                logger.warning(f"   ⚠️ Elemento sconosciuto ignorato nel controllo agenti: {type(item)} = {item}")
        
        for result in first_round_results:
            flatten_recursively(result)
        
        successful_agents = []
        for agent_result in flattened_results:
            if hasattr(agent_result, 'status') and agent_result.status == AgentStatus.COMPLETED:
                successful_agents.append(agent_result)
        
                                                                                             
        if len(successful_agents) >= 1:                     
            logger.info(f"   ✅ Abbastanza risultati ({len(successful_agents)}), non servono più agenti")
            return False
        
                                                                                 
        failed_agents = []
        for agent_result in flattened_results:
            if hasattr(agent_result, 'status') and agent_result.status == AgentStatus.FAILED:
                failed_agents.append(agent_result)
        
        if len(failed_agents) > len(successful_agents):
            logger.warning(f"   ⚠️ Troppi fallimenti ({len(failed_agents)}) rispetto ai successi ({len(successful_agents)}), non chiamo altri agenti per evitare loop")
        return False
        
                                              
        logger.info(f"   ⚠️ Solo {len(successful_agents)} agenti completati, servono più pareri")
        return True
    

    
    def _identify_critical_domains(self, article: Dict[str, Any]) -> set:
        """Identify critical domains for this article"""
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()
        
        critical_domains = set()
        
                                                             
        if any(word in title or word in content for word in ['economia', 'inflazione', 'prezzi', 'mercato', 'borsa', 'finanza']):
            critical_domains.add('economico')
        
                                                          
        if any(word in title or word in content for word in ['politica', 'governo', 'ministro', 'parlamento']):
            critical_domains.add('politico')
        
                                                                
        if any(word in title or word in content for word in ['scienza', 'ricerca', 'studi', 'medicina']):
            critical_domains.add('scientifico')
        
        return critical_domains
    
    def _identify_additional_domains_needed(self, first_round_results: List[Any], article: Dict[str, Any]) -> List[str]:
        """Identify which additional domains we need to call"""
        logger.info("   🔍 Identificazione domini aggiuntivi necessari")
        
                                                                                        
        failed_agents = []
        successful_agents = []
        called_domains = set()
        
                                                                           
        flattened_results = []
        
        def flatten_recursively(item):
            """Appiattisce ricorsivamente liste annidate"""
            if isinstance(item, list):
                for subitem in item:
                    flatten_recursively(subitem)
            elif hasattr(item, 'agent_name') or (isinstance(item, dict) and 'agent_name' in item):
                                       
                flattened_results.append(item)
            else:
                logger.warning(f"   ⚠️ Elemento sconosciuto ignorato: {type(item)} = {item}")
        
        for result in first_round_results:
            flatten_recursively(result)
        
                                             
        for agent_result in flattened_results:
            if hasattr(agent_result, 'status'):
                if agent_result.status == AgentStatus.FAILED:
                    failed_agents.append(agent_result)
                elif agent_result.status == AgentStatus.COMPLETED:
                    successful_agents.append(agent_result)
                if hasattr(agent_result, 'agent_name'):
                                                               
                    agent_name = agent_result.agent_name
                    if isinstance(agent_name, str):
                        called_domains.add(agent_name)
                    else:
                        logger.warning(f"   ⚠️ agent_name non è stringa: {type(agent_name)} = {agent_name}")
            elif isinstance(agent_result, dict) and 'agent_name' in agent_result:
                                                                                  
                agent_name = agent_result['agent_name']
                if isinstance(agent_name, str):
                    called_domains.add(agent_name)
                else:
                    logger.warning(f"   ⚠️ agent_name nel dict non è stringa: {type(agent_name)} = {agent_name}")
        
        if len(failed_agents) > len(successful_agents):
            logger.warning(f"   ⚠️ Troppi fallimenti ({len(failed_agents)}) rispetto ai successi ({len(successful_agents)}), non chiamo altri domini per evitare loop")
            return []
        
                                       
        critical_domains = self._identify_critical_domains(article)
        
                         
        missing_domains = critical_domains - called_domains
        
                                                                      
        if not missing_domains:
            complementary_domains = ['universale']                
            if 'economico' not in called_domains and any(word in article.get('title', '').lower() for word in ['mercato', 'borsa']):
                complementary_domains.append('economico')
            if 'politico' not in called_domains and any(word in article.get('title', '').lower() for word in ['governo', 'politica']):
                complementary_domains.append('politico')
            
            missing_domains = set(complementary_domains) - called_domains
        
                                                               
        additional_domains = [domain for domain in missing_domains if domain not in self.called_domains]
        
                                                                                
        additional_domains = additional_domains[:2]
        
                                               
        self.called_domains.update(additional_domains)
        
        if additional_domains:
            logger.info(f"   🎯 Domini aggiuntivi selezionati: {additional_domains}")
            logger.info(f"   🚫 Domini già chiamati: {list(self.called_domains)}")
        else:
            logger.info("   ✅ Nessun dominio aggiuntivo necessario")
        
        return additional_domains
    
    def _coordinate_cross_domain_information(self, domain_results: List[Any]):
        """Coordinate information sharing between domains"""
        logger.info("   🔗 Coordinazione informazioni cross-dominio")
                                                                        
    
    def _synthesize_final_result(self, article: Dict[str, Any], analysis: Dict[str, Any], domain_results: List[Any]) -> Dict[str, Any]:
        """Synthesize final result from all domains"""
        logger.info("   🔗 Sintesi risultato finale")
        
                                
        all_agent_results = []
        for domain_result in domain_results:
            if isinstance(domain_result, list):
                all_agent_results.extend(domain_result)
            else:
                all_agent_results.append(domain_result)
        
                                      
        valid_results = [r for r in all_agent_results if hasattr(r, 'status') and r.status == AgentStatus.COMPLETED]
        overall_confidence = sum(r.confidence for r in valid_results) / len(valid_results) if valid_results else 5.0
        
                                  
        primary_domain = self._determine_primary_domain(all_agent_results)
        
                                         
        final_evaluation = self._create_comprehensive_evaluation(article, analysis, all_agent_results, overall_confidence)
        
                                                 
        return {
            "article_id": article.get('_id', ''),
            "analysis_timestamp": datetime.now().isoformat(),
            "primary_domain": primary_domain,
            "overall_confidence": overall_confidence,
            "domains_analyzed": len(domain_results),
            "total_agents": len(all_agent_results),
            "successful_agents": len(valid_results),
            "failed_agents": len([r for r in all_agent_results if hasattr(r, 'status') and r.status == AgentStatus.FAILED]),
            "final_evaluation": final_evaluation,
            "domain_results": self._result_to_dict(all_agent_results),
            "raw_agent_results": self._result_to_dict_detailed(all_agent_results),
            "orchestration_summary": {
                "total_rounds": 2 if len(domain_results) > 3 else 1,
                "orchestration_strategy": "intelligent_routing",
                "confidence_threshold": 0.4,
                "max_rounds": 2
            }
        }
    
    def _determine_primary_domain(self, agent_results: List[AgentResult]) -> str:
        """Determine the primary domain based on agent results"""
        if not agent_results:
            return "universale"
        
                                                     
        domain_confidences = {}
        for result in agent_results:
            if hasattr(result, 'agent_name'):
                domain = result.agent_name
                if domain not in domain_confidences:
                    domain_confidences[domain] = []
                domain_confidences[domain].append(result.confidence)
        
        if not domain_confidences:
            return "universale"
        
                                                 
        domain_averages = {}
        for domain, confidences in domain_confidences.items():
            domain_averages[domain] = sum(confidences) / len(confidences)
        
                                                       
        primary_domain = max(domain_averages.items(), key=lambda x: x[1])[0]
        return primary_domain
    
    def _create_comprehensive_evaluation(self, article: Dict[str, Any], analysis: Dict[str, Any], agent_results: List[AgentResult], overall_confidence: float) -> Dict[str, Any]:
        """Create comprehensive evaluation from all agent results"""
        evaluations = []
        combined_insights = []
        combined_suspicious_points = []
        combined_recommendations = []
        
        for result in agent_results:
            if hasattr(result, 'status') and result.status == AgentStatus.COMPLETED and hasattr(result, 'result'):
                                                          
                agent_evaluation = result.result
                
                                                
                if isinstance(agent_evaluation, str):
                    try:
                        import json
                        agent_evaluation = json.loads(agent_evaluation)
                    except:
                        agent_evaluation = {"raw": agent_evaluation}
                
                                         
                if 'punti_sospetti' in agent_evaluation:
                    for punto in agent_evaluation['punti_sospetti']:
                        if isinstance(punto, dict):
                                                                                               
                            if 'descrizione' in punto:
                                combined_suspicious_points.append(punto['descrizione'])
                            else:
                                combined_suspicious_points.append(str(punto))
                        elif isinstance(punto, str):
                            combined_suspicious_points.append(punto)
                        else:
                            combined_suspicious_points.append(str(punto))
                
                                          
                if 'raccomandazioni' in agent_evaluation:
                    for raccomandazione in agent_evaluation['raccomandazioni']:
                        if isinstance(raccomandazione, dict):
                                                                                               
                            if 'descrizione' in raccomandazione:
                                combined_recommendations.append(raccomandazione['descrizione'])
                            else:
                                combined_recommendations.append(str(raccomandazione))
                        elif isinstance(raccomandazione, str):
                            combined_recommendations.append(raccomandazione)
                        else:
                            combined_recommendations.append(str(raccomandazione))
                
                                              
                domain_eval = {
                    "domain": result.agent_name,
                    "confidence": result.confidence,
                    "credibility_score": agent_evaluation.get('livello_credibilità', 5),
                    "verosimiglianza": agent_evaluation.get('verosimiglianza', 'media'),
                    "summary": self._extract_key_insights(agent_evaluation)
                }
                evaluations.append(domain_eval)
        
                                                                    
        if evaluations:
            avg_credibility = sum(e.get('credibility_score', 5) for e in evaluations) / len(evaluations)
            overall_credibility = "alta" if avg_credibility >= 7 else "media" if avg_credibility >= 4 else "bassa"
        else:
            overall_credibility = "bassa"
            avg_credibility = overall_confidence
        
        return {
            "overall_credibility": overall_credibility,
            "confidence_score": avg_credibility,
            "domain_evaluations": evaluations,
            "total_evaluations": len(evaluations),
            "combined_insights": combined_insights[:10],                                 
            "combined_suspicious_points": list(set(combined_suspicious_points))[:10],                      
            "combined_recommendations": list(set(combined_recommendations))[:10],                                
            
                                     
            "statistics": {
                "total_agents": len(agent_results),
                "successful_agents": len([r for r in agent_results if hasattr(r, 'status') and r.status == AgentStatus.COMPLETED]),
                "failed_agents": len([r for r in agent_results if hasattr(r, 'status') and r.status == AgentStatus.FAILED]),
                "agents_needing_info": len([r for r in agent_results if hasattr(r, 'status') and r.status == AgentStatus.NEEDS_INFO]),
                "average_confidence": sum(r.confidence for r in agent_results if hasattr(r, 'confidence')) / len(agent_results) if agent_results else 0.0,
                "confidence_distribution": {
                    "high": len([r for r in agent_results if hasattr(r, 'confidence') and r.confidence >= 0.7]),
                    "medium": len([r for r in agent_results if hasattr(r, 'confidence') and 0.4 <= r.confidence < 0.7]),
                    "low": len([r for r in agent_results if hasattr(r, 'confidence') and r.confidence < 0.4])
                }
            },
            
                                 
            "domain_analysis": {
                "scientific": [r for r in agent_results if hasattr(r, 'agent_name') and 'scientific' in r.agent_name.lower()],
                "political": [r for r in agent_results if hasattr(r, 'agent_name') and 'politic' in r.agent_name.lower()],
                "economic": [r for r in agent_results if hasattr(r, 'agent_name') and 'economic' in r.agent_name.lower()],
                "technological": [r for r in agent_results if hasattr(r, 'agent_name') and 'technolog' in r.agent_name.lower()],
                "news": [r for r in agent_results if hasattr(r, 'agent_name') and 'cronaca' in r.agent_name.lower()],
                "universal": [r for r in agent_results if hasattr(r, 'agent_name') and 'universal' in r.agent_name.lower()]
            }
        }
    
    def _extract_key_insights(self, evaluation: Dict[str, Any]) -> str:
        """Extract key insights from agent evaluation"""
        insights = []
        
        if 'punti_sospetti' in evaluation and evaluation['punti_sospetti']:
            insights.append(f"Punti sospetti: {len(evaluation['punti_sospetti'])}")
        
        if 'raccomandazioni' in evaluation and evaluation['raccomandazioni']:
            insights.append(f"Raccomandazioni: {len(evaluation['raccomandazioni'])}")
        
        if 'livello_credibilità' in evaluation:
            insights.append(f"Credibilità: {evaluation['livello_credibilità']}/10")
        
        if 'verosimiglianza' in evaluation:
            insights.append(f"Verosimiglianza: {evaluation['verosimiglianza']}")
        
        return " | ".join(insights) if insights else "Analisi completata"
    
    def _result_to_dict(self, agent_results: List[AgentResult]) -> List[Dict[str, Any]]:
        """Convert agent results to dictionary format"""
        results = []
        
        for result in agent_results:
            if hasattr(result, 'agent_name'):
                results.append({
                    "agent_name": result.agent_name,
                    "status": result.status.value if hasattr(result, 'status') else "unknown",
                    "confidence_score": result.confidence if hasattr(result, 'confidence') else 0.0,
                    "processing_time": result.processing_time if hasattr(result, 'processing_time') else 0.0,
                    "evaluation": result.result if hasattr(result, 'result') else {}
                })
        
        return results
    
    def _result_to_dict_detailed(self, agent_results: List[AgentResult]) -> List[Dict[str, Any]]:
        """Convert agent results to detailed dictionary format with ALL information"""
        detailed_results = []
        
        for result in agent_results:
            if hasattr(result, 'agent_name'):
                                                                             
                agent_evaluation = result.result if hasattr(result, 'result') else {}
                
                                                         
                if isinstance(agent_evaluation, str):
                    try:
                        import json
                        agent_evaluation = json.loads(agent_evaluation)
                    except:
                        agent_evaluation = {"raw_response": agent_evaluation}
                
                detailed_result = {
                    "agent_name": result.agent_name,
                    "agent_type": result.agent_name,                                          
                    "status": result.status.value if hasattr(result, 'status') else "unknown",
                    "confidence_score": result.confidence if hasattr(result, 'confidence') else 0.0,
                    "processing_time": result.processing_time if hasattr(result, 'processing_time') else 0.0,
                    "timestamp": result.timestamp.isoformat() if hasattr(result, 'timestamp') and result.timestamp else None,
                    
                                                      
                    "evaluation": agent_evaluation,
                    
                                                        
                    "conferma": agent_evaluation.get('conferma', None),
                    "punteggio_finale": agent_evaluation.get('punteggio_finale', None),
                    "verosimiglianza": agent_evaluation.get('verosimiglianza', None),
                    "punti_sospetti": agent_evaluation.get('punti_sospetti', []),
                    "spiegazione": agent_evaluation.get('spiegazione', None),
                    "evidenze_a_favore": agent_evaluation.get('evidenze_a_favore', []),
                    "evidenze_contro": agent_evaluation.get('evidenze_contro', []),
                    "raccomandazioni": agent_evaluation.get('raccomandazioni', []),
                    
                                                 
                    "qualità_metodologica": agent_evaluation.get('qualità_metodologica', None),
                    "fonti_affidabili": agent_evaluation.get('fonti_affidabili', []),
                    "criticità_metodologiche": agent_evaluation.get('criticità_metodologiche', []),
                    "studi_contrari": agent_evaluation.get('studi_contrari', []),
                    "credibilità_politica": agent_evaluation.get('credibilità_politica', None),
                    "fonti_istituzionali": agent_evaluation.get('fonti_istituzionali', []),
                    "dichiarazioni_verificate": agent_evaluation.get('dichiarazioni_verificate', []),
                    "contraddizioni_trovate": agent_evaluation.get('contraddizioni_trovate', []),
                    "timing_sospetto": agent_evaluation.get('timing_sospetto', None),
                    "bias_politici": agent_evaluation.get('bias_politici', []),
                    "fattibilità_tecnica": agent_evaluation.get('fattibilità_tecnica', None),
                    "brevetti_trovati": agent_evaluation.get('brevetti_trovati', []),
                    "documentazione_tecnica": agent_evaluation.get('documentazione_tecnica', []),
                    "esperti_verificati": agent_evaluation.get('esperti_verificati', []),
                    "limitazioni_tecniche": agent_evaluation.get('limitazioni_tecniche', []),
                    "hype_tecnologico": agent_evaluation.get('hype_tecnologico', None),
                    "credibilità_economica": agent_evaluation.get('credibilità_economica', None),
                    "dati_statistici_verificati": agent_evaluation.get('dati_statistici_verificati', []),
                    "fonti_finanziarie": agent_evaluation.get('fonti_finanziarie', []),
                    "coerenza_economica": agent_evaluation.get('coerenza_economica', None),
                    "possibili_manipolazioni": agent_evaluation.get('possibili_manipolazioni', []),
                    "bias_economici": agent_evaluation.get('bias_economici', []),
                    "credibilità_giornalistica": agent_evaluation.get('credibilità_giornalistica', None),
                    "fonti_verificate": agent_evaluation.get('fonti_verificate', []),
                    "verifiche_incrociate": agent_evaluation.get('verifiche_incrociate', []),
                    "coerenza_eventi": agent_evaluation.get('coerenza_eventi', None),
                    "bias_mediatici": agent_evaluation.get('bias_mediatici', []),
                    "clickbait": agent_evaluation.get('clickbait', None),
                    "credibilità_complessiva": agent_evaluation.get('credibilità_complessiva', None),
                    "qualità_fonti": agent_evaluation.get('qualità_fonti', None),
                    "coerenza_logica": agent_evaluation.get('coerenza_logica', None),
                    "fact_checking_precedenti": agent_evaluation.get('fact_checking_precedenti', []),
                    "bias_generali": agent_evaluation.get('bias_generali', []),
                    "contraddizioni_logiche": agent_evaluation.get('contraddizioni_logiche', []),
                    
                                         
                    "fallback": agent_evaluation.get('fallback', False),
                    "error": agent_evaluation.get('error', None),
                    "enhanced_with_additional_info": agent_evaluation.get('enhanced_with_additional_info', False)
                }
                
                detailed_results.append(detailed_result)
        
        return detailed_results
    
    def _create_fallback_result(self, article: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create fallback result when orchestration fails"""
        return {
            "article_id": article.get('_id', ''),
            "analysis_timestamp": datetime.now().isoformat(),
            "error": error,
            "fallback": True,
            "overall_confidence": 0.0,
            "final_evaluation": {
                "overall_credibility": "bassa",
                "confidence_score": 0.0,
                "error": error
            }
        }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from AI with robust fallback"""
        try:
                                        
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            
                               
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            json_str = json_match.group() if json_match else response
            json_str = json_str.strip()
            
                                          
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
                                                                       
                fixed_json = re.sub(r"'([^']+)':", r'"\1":', json_str)
                fixed_json = re.sub(r": '([^']*)'", r': "\1"', fixed_json)
                fixed_json = re.sub(r"\['([^']+)'\]", r'["\1"]', fixed_json)
                fixed_json = re.sub(r"'([^',\[\]{}]+)'", r'"\1"', fixed_json)
                
                try:
                    parsed = json.loads(fixed_json)
                except json.JSONDecodeError:
                                                                   
                    import ast
                    try:
                        parsed = ast.literal_eval(json_str)
                        if not isinstance(parsed, dict):
                            raise ValueError("Not a dict")
                    except (ValueError, SyntaxError):
                                                      
                        parsed = {}
                        patterns = {
                            'confidence': r'"?confidence"?\s*:\s*([0-9.]+)',
                            'conferma': r'"?conferma"?\s*:\s*(true|false)',
                            'punteggio_finale': r'"?punteggio_finale"?\s*:\s*([0-9]+)',
                            'verosimiglianza': r'"?verosimiglianza"?\s*:\s*["\']?([^",\'\}]+)["\']?',
                        }
                        
                        for key, pattern in patterns.items():
                            match = re.search(pattern, json_str, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                if key in ['confidence', 'punteggio_finale']:
                                    try:
                                        parsed[key] = float(value)
                                    except ValueError:
                                        pass
                                elif key == 'conferma':
                                    parsed[key] = value.lower() == 'true'
                                else:
                                    parsed[key] = value.strip('"\'')
            
                                                              
            if 'confidence' not in parsed or parsed.get('confidence', 0) == 0:
                parsed['confidence'] = 0.5                         
            return parsed
            
        except Exception as e:
            logger.error(f"   ❌ Errore parsing JSON: {e}")
                                                                                     
            return {
                "confidence": 0.4,                                      
                "fallback": True,
                "error": f"Parsing JSON fallito: {e}",
                "conferma": False,
                "punteggio_finale": 4,
                "verosimiglianza": "bassa",
                "punti_sospetti": ["Impossibile analizzare la risposta AI"],
                "spiegazione": "Fallback automatico dovuto a errore di parsing",
                "evidenze_a_favore": [],
                "evidenze_contro": ["Errore tecnico nell'analisi"],
                "raccomandazioni": ["Verificare la configurazione AI e riprovare"]
            }

    def _generate_initial_analysis(self, article: Dict[str, Any], language: str = 'it') -> Dict[str, Any]:
        """Generate initial analysis using AI service - this is the FIRST prompt from the orchestrator"""
        logger.info("   🧠 Generazione analisi iniziale con prompt critico")
        
        title = article.get('title', 'N/A')
        content = article.get('content', 'N/A')
        source = article.get('source', 'N/A')
        date = article.get('date', 'N/A')
        
        prompt = f"""Sei un analista critico esperto di notizie. Analizza questa notizia con scetticismo professionale.
        
        NOTIZIA:
        Titolo: {title}
        Contenuto: {content[:1000] if content else 'N/A'}
        Fonte: {source}
        Data: {date}
        
        Esegui un'analisi critica in {language} considerando:
        
        1. VEROSIMIGLIANZA INTRINSECA:
        - La notizia è plausibile dal punto di vista logico?
        - Ci sono contraddizioni interne?
        - I fatti riportati sono coerenti con la realtà?
        
        2. CONTESTO E TIMING:
        - Il timing dell'annuncio è sospetto?
        - Ci sono eventi correlati che potrebbero spiegare la notizia?
        - È un periodo in cui simili notizie sono comuni?
        
        3. FONTE E CREDIBILITÀ:
        - La fonte è affidabile?
        - Ha una storia di accuratezza?
        - Potrebbe avere bias o interessi particolari?
        
        4. PUNTI SOSPETTI:
        - Quali elementi sembrano troppo belli per essere veri?
        - Ci sono dettagli vaghi o mancanti?
        - La notizia sembra clickbait?
        
        5. POSSIBILI SCENARI:
        - Se fosse vera, quali sarebbero le implicazioni?
        - Se fosse falsa, perché potrebbe essere stata pubblicata?
        - Ci sono spiegazioni alternative?
        
        Fornisci un'analisi strutturata in formato JSON:
        {{
            "verosimiglianza": "alta/media/bassa",
            "punti_sospetti": ["lista punti sospetti"],
            "possibili_scenari": ["scenario 1", "scenario 2"],
            "query_strategiche": ["query 1", "query 2"],
            "livello_credibilità": 1-10,
            "raccomandazioni": ["suggerimenti per verificare"]
        }}
        
        Ritorna SOLO JSON valido, nient'altro."""
        
        try:
            logger.info(f"   📤 PROMPT ANALISI INIZIALE ORCHESTRATOR:")
            logger.info(f"   {prompt}")
            
            response = self.ai_service.generate(prompt, max_tokens=1500, temperature=0.3)
            logger.info(f"   📥 RISPOSTA ANALISI INIZIALE ORCHESTRATOR:")
            logger.info(f"   {response}")
            
            if response:
                try:
                    analysis_data = json.loads(response)
                    logger.info(f"   ✅ Analisi iniziale orchestrator parsata come JSON")
                    logger.info(f"   📊 Campi trovati: {list(analysis_data.keys())}")
                    return analysis_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"   ❌ Errore parsing JSON analisi iniziale orchestrator: {e}")
                    logger.error(f"   📄 Testo che non si riesce a parsare: {response}")
                    
                                                    
                    fallback_analysis = {
                        "verosimiglianza": "media",
                        "punti_sospetti": ["Impossibile parsare l'analisi orchestrator"],
                        "possibili_scenari": ["Analisi non strutturata"],
                        "query_strategiche": ["Verifica fonte", "Cerca conferme"],
                        "livello_credibilità": 5,
                        "raccomandazioni": ["Verifica manuale necessaria"],
                        "analisi_grezza": response,
                        "fallback": True
                    }
                    logger.warning(f"   ⚠️ Fallback a analisi di base per errore parsing")
                    return fallback_analysis
            
            else:
                logger.error("   ❌ AI Service ha restituito risposta vuota per analisi iniziale")
                                                
                fallback_analysis = {
                    "verosimiglianza": "media",
                    "punti_sospetti": ["AI Service ha restituito risposta vuota"],
                    "possibili_scenari": ["Analisi non disponibile"],
                    "query_strategiche": ["Verifica fonte", "Cerca conferme"],
                    "livello_credibilità": 5,
                    "raccomandazioni": ["Verifica manuale necessaria"],
                    "fallback": True
                }
                logger.warning(f"   ⚠️ Fallback a analisi di base per risposta vuota")
                return fallback_analysis
                
        except Exception as e:
            logger.error(f"   ❌ ERRORE durante generazione analisi iniziale orchestrator: {e}")
            logger.error(f"   📍 Stack trace completo:", exc_info=True)
            
                                            
            fallback_analysis = {
                "verosimiglianza": "media",
                "punti_sospetti": [f"Errore sistema: {e}"],
                "possibili_scenari": ["Analisi non disponibile"],
                "query_strategiche": ["Verifica fonte", "Cerca conferme"],
                "livello_credibilità": 5,
                "raccomandazioni": ["Verifica manuale necessaria"],
                "fallback": True
            }
            logger.warning(f"   ⚠️ Fallback a analisi di base per errore sistema")
            return fallback_analysis

class IntelligentOrchestrator:
    """Legacy intelligent orchestrator for backward compatibility"""
    
    def __init__(self, ai_service: AIService, search_service: SearchService):
        self.primary_orchestrator = PrimaryOrchestrator(ai_service, search_service)
        logger.info("🎼 INTELLIGENT ORCHESTRATOR (legacy) inizializzato")
    
    def orchestrate_analysis(self, article: Dict[str, Any], analysis: str, language: str = 'it') -> Dict[str, Any]:
        """Delegate to primary orchestrator"""
        return self.primary_orchestrator.orchestrate_analysis(article, analysis, language)

def create_orchestrator(ai_service: AIService = None, search_service: SearchService = None) -> IntelligentOrchestrator:
    """Create and return an intelligent orchestrator instance"""
    if ai_service is None:
        from app.services.ai_service import AIService
        ai_service = AIService()
    
    if search_service is None:
        from app.services.search_service import SearchService
        search_service = SearchService()
    
    return IntelligentOrchestrator(ai_service, search_service)
