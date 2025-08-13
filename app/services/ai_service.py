"""
AI service for managing different AI providers
"""

import logging
import requests
import json
from typing import Dict, Any, Optional
import time

                                    
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, config):
        self.config = config
        self.openai_api_key = config.get('OPENAI_API_KEY')
        self.anthropic_api_key = config.get('ANTHROPIC_API_KEY')
        self.ollama_base_url = config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
                                            
        self.ollama_model = config.get('OLLAMA_MODEL', 'qwen2:7b-instruct')
        self.openai_model = config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.anthropic_model = config.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
        
        logger.info("🤖 AI SERVICE inizializzato")
        logger.info(f"   🔑 OpenAI API Key: {'✅ Configurata' if self.openai_api_key else '❌ Non configurata'}")
        logger.info(f"   🔑 Anthropic API Key: {'✅ Configurata' if self.anthropic_api_key else '❌ Non configurata'}")
        logger.info(f"   🐳 Ollama Base URL: {self.ollama_base_url}")

    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, provider: str = None) -> str:
        logger.info("🚀 GENERAZIONE AI")
        logger.info(f"   📝 Prompt: {prompt[:200]}...")
        logger.info(f"   📊 Max tokens: {max_tokens}")
        logger.info(f"   🌡️ Temperature: {temperature}")
        logger.info(f"   🎯 Provider richiesto: {provider or 'auto'}")
        
                                                                         
        if not provider:
            providers = ['ollama', 'openai', 'anthropic']
        else:
            providers = [provider]
        
        for provider_name in providers:
            logger.info(f"   🔄 Tentativo con provider: {provider_name}")
            
            try:
                if provider_name == 'ollama':
                    result = self._generate_ollama(prompt, max_tokens, temperature)
                elif provider_name == 'openai':
                    result = self._generate_openai(prompt, max_tokens, temperature)
                elif provider_name == 'anthropic':
                    result = self._generate_anthropic(prompt, max_tokens, temperature)
                else:
                    continue
                
                if result:
                    logger.info(f"   ✅ Generazione completata con {provider_name}")
                    logger.info(f"   📥 Risultato: {result[:200]}...")
                    return result
                else:
                    logger.warning(f"   ⚠️ {provider_name} ha restituito risultato vuoto")
                    
            except Exception as e:
                logger.error(f"   ❌ Errore con {provider_name}: {e}")
                continue
        
                                        
        logger.error("   🚨 TUTTI I PROVIDER SONO FALLITI")
        raise Exception("Tutti i provider AI sono falliti")

    def _generate_ollama(self, prompt: str, max_tokens: int, temperature: float) -> str:
        logger.info(f"   🐳 Generazione Ollama")
        
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,                        
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        logger.info(f"   📤 URL: {url}")
        logger.info(f"   📤 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload)                                     
            logger.info(f"   📥 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   📊 Risposta ricevuta: {len(str(data))} caratteri")
                
                if 'response' in data:
                    result = data['response']
                    logger.info(f"   ✅ Ollama generazione completata: {len(result)} caratteri")
                    return result
                else:
                    logger.error(f"   ❌ Formato risposta Ollama non riconosciuto: {list(data.keys())}")
                    return None
            else:
                logger.error(f"   ❌ Errore HTTP Ollama: {response.status_code}")
                logger.error(f"   📥 Risposta: {response.text}")
                return None
                
                                                     
        except requests.exceptions.RequestException as e:
            logger.error(f"   ❌ Errore richiesta Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"   ❌ Errore generico Ollama: {e}")
            return None

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        if not self.openai_api_key:
            logger.warning("   ⚠️ OpenAI API key non configurata")
            return None
            
        logger.info(f"   🧠 Generazione OpenAI")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openai_model,                        
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        logger.info(f"   📤 URL: {url}")
        logger.info(f"   📤 Headers: {headers}")
        logger.info(f"   📤 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)                   
            logger.info(f"   📥 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   📊 Risposta ricevuta: {len(str(data))} caratteri")
                
                if 'choices' in data and len(data['choices']) > 0:
                    result = data['choices'][0]['message']['content']
                    logger.info(f"   ✅ OpenAI generazione completata: {len(result)} caratteri")
                    return result
                else:
                    logger.error(f"   ❌ Formato risposta OpenAI non riconosciuto: {list(data.keys())}")
                    return None
            else:
                logger.error(f"   ❌ Errore HTTP OpenAI: {response.status_code}")
                logger.error(f"   📥 Risposta: {response.text}")
                return None
                
                                   
        except requests.exceptions.RequestException as e:
            logger.error(f"   ❌ Errore richiesta OpenAI: {e}")
            return None
        except Exception as e:
            logger.error(f"   ❌ Errore generico OpenAI: {e}")
            return None

    def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float) -> str:
        if not self.anthropic_api_key:
            logger.warning("   ⚠️ Anthropic API key non configurata")
            return None
            
        logger.info(f"   🧠 Generazione Anthropic")
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.anthropic_model,                        
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        logger.info(f"   📤 URL: {url}")
        logger.info(f"   📤 Headers: {headers}")
        logger.info(f"   📤 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)                   
            logger.info(f"   📥 Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   📊 Risposta ricevuta: {len(str(data))} caratteri")
                
                if 'content' in data and len(data['content']) > 0:
                    result = data['content'][0]['text']
                    logger.info(f"   ✅ Anthropic generazione completata: {len(result)} caratteri")
                    return result
                else:
                    logger.error(f"   ❌ Formato risposta Anthropic non riconosciuto: {list(data.keys())}")
                    return None
            else:
                logger.error(f"   ❌ Errore HTTP Anthropic: {response.status_code}")
                logger.error(f"   📥 Risposta: {response.text}")
                return None
                
                                   
        except requests.exceptions.RequestException as e:
            logger.error(f"   ❌ Errore richiesta Anthropic: {e}")
            return None
        except Exception as e:
            logger.error(f"   ❌ Errore generico Anthropic: {e}")
            return None
