"""
Settings model for user configuration
"""

from datetime import datetime
from typing import Dict, Any, Optional

class Settings:
    """Settings model for user configuration"""
    
    def __init__(self, 
                 user_id: str = 'default',
                 ai_provider: str = 'ollama',
                 ai_model: str = 'qwen2:7b-instruct',
                 language: str = 'it',
                 articles_per_page: int = 20,
                 enable_multilingual: bool = True,
                 rss_sources: str = "https://www.ansa.it/sito/ansait_rss.xml\nhttps://www.repubblica.it/rss/homepage/rss2.0.xml\nhttps://www.corriere.it/rss/homepage.xml\nhttps://www.ilsole24ore.com/rss/homepage.xml",
                 openai_api_key: str = '',
                 anthropic_api_key: str = '',
                 scrapingdog_api_key: str = '',
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        
        self.user_id = user_id
        self.ai_provider = ai_provider
        self.ai_model = ai_model
        self.language = language
        self.articles_per_page = articles_per_page
        self.enable_multilingual = enable_multilingual
        self.rss_sources = rss_sources
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.scrapingdog_api_key = scrapingdog_api_key
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def get_default_settings(cls) -> 'Settings':
        """Get default settings"""
        settings = cls()
                                                    
        settings.clean_rss_sources()
        return settings
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create Settings from dictionary"""
        settings = cls(
            user_id=data.get('user_id', 'default'),
            ai_provider=data.get('ai_provider', 'ollama'),
            ai_model=data.get('ai_model', 'qwen2:7b-instruct'),
            language=data.get('language', 'it'),
            articles_per_page=data.get('articles_per_page', 20),
            enable_multilingual=data.get('enable_multilingual', True),
            rss_sources=data.get('rss_sources', "https://www.ansa.it/sito/ansait_rss.xml\nhttps://www.repubblica.it/rss/homepage/rss2.0.xml\nhttps://www.corriere.it/rss/homepage.xml\nhttps://www.ilsole24ore.com/rss/homepage.xml"),
            openai_api_key=data.get('openai_api_key', ''),
            anthropic_api_key=data.get('anthropic_api_key', ''),
            scrapingdog_api_key=data.get('scrapingdog_api_key', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
                                          
        settings.clean_rss_sources()
        return settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'language': self.language,
            'articles_per_page': self.articles_per_page,
            'enable_multilingual': self.enable_multilingual,
            'rss_sources': self.rss_sources,
            'openai_api_key': self.openai_api_key,
            'anthropic_api_key': self.anthropic_api_key,
            'scrapingdog_api_key': self.scrapingdog_api_key,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self) -> str:
        """Save settings to database"""
        from app import mongo
        
                                         
        self.clean_rss_sources()
        self.updated_at = datetime.utcnow()
        
                                 
        existing = mongo.db.settings.find_one({'user_id': self.user_id})
        
        if existing:
                             
            mongo.db.settings.update_one(
                {'user_id': self.user_id},
                {'$set': self.to_dict()}
            )
            return existing['_id']
        else:
                        
            result = mongo.db.settings.insert_one(self.to_dict())
            return str(result.inserted_id)
    
    def clean_rss_sources(self):
        """Clean RSS sources from HTML entities and normalize line breaks"""
        if hasattr(self, 'rss_sources') and self.rss_sources:
            if isinstance(self.rss_sources, str):
                import html
                                                                
                cleaned_rss = html.unescape(self.rss_sources)
                                             
                cleaned_rss = cleaned_rss.replace('\r\n', '\n').replace('\r', '\n')
                                                        
                lines = [line.strip() for line in cleaned_rss.split('\n') if line.strip()]
                                                                                        
                if len(lines) > 0 and any(len(line) < 10 for line in lines):
                    self.rss_sources = "https://www.ansa.it/sito/ansait_rss.xml\nhttps://www.repubblica.it/rss/homepage/rss2.0.xml\nhttps://www.corriere.it/rss/homepage.xml\nhttps://www.ilsole24ore.com/rss/homepage.xml"
                else:
                    self.rss_sources = '\n'.join(lines)
    
    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional['Settings']:
        """Find settings by user ID"""
        from app import mongo
        
        data = mongo.db.settings.find_one({'user_id': user_id})
        if data:
            settings = cls.from_dict(data)
                                             
            settings.clean_rss_sources()
            return settings
        return None
    
    @classmethod
    def force_clean_and_save(cls, user_id: str = 'default') -> bool:
        """Force clean RSS sources and save to database"""
        try:
            settings = cls.find_by_user_id(user_id) or cls.get_default_settings()
            settings.clean_rss_sources()
            settings.save()
            return True
        except Exception as e:
            print(f"Error cleaning settings: {e}")
            return False
