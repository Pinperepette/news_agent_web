"""
Configuration management for News Agent Web
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
                         
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
                           
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/news_agent_web')
    
                                
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
                             
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2:7b-instruct')
    
                         
    DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
    
                                
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'it')
    ENABLE_MULTILINGUAL = os.getenv('ENABLE_MULTILINGUAL', 'true').lower() == 'true'
    ARTICLES_PER_PAGE = int(os.getenv('ARTICLES_PER_PAGE', '15'))
    
                 
    RSS_SOURCES = os.getenv('RSS_SOURCES', '').split(',') if os.getenv('RSS_SOURCES') else [
        'https://www.ansa.it/sito/ansait_rss.xml',
        'https://www.repubblica.it/rss/homepage/rss2.0.xml',
        'https://www.corriere.it/rss/homepage.xml',
        'https://www.ilsole24ore.com/rss/homepage.xml',
        'https://feeds.reuters.com/reuters/topNews',
        'https://feeds.bbci.co.uk/news/rss.xml'
    ]
    
                       
    MCP_ENABLED = os.getenv('MCP_ENABLED', 'false').lower() == 'true'
    MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
    
    @classmethod
    def get_ai_config(cls) -> Dict[str, Any]:
        """Get AI configuration as dictionary"""
        return {
            'provider': cls.DEFAULT_AI_PROVIDER,
            'openai_api_key': cls.OPENAI_API_KEY,
            'anthropic_api_key': cls.ANTHROPIC_API_KEY,
            'ollama_base_url': cls.OLLAMA_BASE_URL,
            'openai_model': cls.OPENAI_MODEL,
            'anthropic_model': cls.ANTHROPIC_MODEL,
            'ollama_model': cls.OLLAMA_MODEL
        }
    
    @classmethod
    def get_news_config(cls) -> Dict[str, Any]:
        """Get news configuration as dictionary"""
        return {
            'default_language': cls.DEFAULT_LANGUAGE,
            'enable_multilingual': cls.ENABLE_MULTILINGUAL,
            'articles_per_page': cls.ARTICLES_PER_PAGE,
            'rss_sources': cls.RSS_SOURCES
        }
    
    @classmethod
    def get_mcp_config(cls) -> Dict[str, Any]:
        """Get MCP configuration as dictionary"""
        return {
            'enabled': cls.MCP_ENABLED,
            'server_url': cls.MCP_SERVER_URL
        }
