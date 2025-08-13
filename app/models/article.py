"""
Article model for MongoDB
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from flask import current_app

class Article:
    """Article model for news articles"""
    
    def __init__(self, title: str, link: str, source: str, 
                 summary: str = "", author: str = "", 
                 published_date: Optional[datetime] = None,
                 content: str = "", language: str = "it"):
        self.title = title
        self.link = link
        self.source = source
        self.summary = summary
        self.author = author
        self.published_date = published_date or datetime.utcnow()
        self.content = content
        self.language = language
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._id = None                    
    
    @property
    def id(self):
        """Property to access the ID as string"""
        return str(self._id) if self._id else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert article to dictionary"""
        return {
            '_id': str(self._id),
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'author': self.author,
            'link': self.link,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """Create article from dictionary"""
        try:
            print(f"🔧 Creazione Article da dict: {data.get('title', 'N/A')[:30]}...")
            
            article = cls(
                title=data['title'],
                link=data['link'],
                source=data['source'],
                summary=data.get('summary', ''),
                author=data.get('author', ''),
                published_date=data.get('published_date'),
                content=data.get('content', ''),
                language=data.get('language', 'it')
            )
            
                            
            if '_id' in data:
                article._id = data['_id']
                print(f"   🆔 ID impostato: {article._id}")
            
                            
            if 'created_at' in data:
                article.created_at = data['created_at']
            if 'updated_at' in data:
                article.updated_at = data['updated_at']
            
            print(f"   ✅ Article creato con successo")
            return article
            
        except Exception as e:
            print(f"❌ Errore creazione Article: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def save(self) -> str:
        """Save article to database"""
        try:
            from app import mongo
            
                            
            if not self.created_at:
                self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            
                              
            doc = {
                'title': self.title,
                'content': self.content,
                'summary': self.summary,
                'source': self.source,
                'author': self.author,
                'link': self.link,
                'language': self.language,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }
            
                                             
            if self.published_date:
                doc['published_date'] = self.published_date
            
                                  
            result = mongo.db.articles.insert_one(doc)
            self._id = result.inserted_id
            
            print(f"✅ Article saved with ID: {self._id}")
            return str(self._id)
            
        except Exception as e:
            print(f"❌ Error saving article: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, article_id: str) -> Optional['Article']:
        """Find article by ID"""
        try:
            from app import mongo
            data = mongo.db.articles.find_one({'_id': ObjectId(article_id)})
            if data:
                return cls.from_dict(data)
        except Exception as e:
            print(f"❌ Error finding article by ID: {e}")
        return None
    
    @classmethod
    def find_by_link(cls, link: str) -> Optional['Article']:
        """Find article by link"""
        try:
            from app import mongo
            data = mongo.db.articles.find_one({'link': link})
            if data:
                return cls.from_dict(data)
        except Exception as e:
            print(f"❌ Error finding article by link: {e}")
        return None
    
    @classmethod
    def find_recent(cls, limit: int = 50, language: str = "it") -> list['Article']:
        """Find recent articles"""
        try:
            from app import mongo
            print(f"🔍 Cerca articoli recenti: limit={limit}, language={language}")
            
                                                   
            total_all = mongo.db.articles.count_documents({})
            print(f"   📊 Totale articoli nel database: {total_all}")
            
                                       
            total_lang = mongo.db.articles.count_documents({'language': language})
            print(f"   🌍 Articoli per lingua '{language}': {total_lang}")
            
                                              
                                                                         
            cursor = mongo.db.articles.find(
                {'language': language}
            ).sort([('published_date', -1), ('created_at', -1)]).limit(limit)
            
            articles = [cls.from_dict(data) for data in cursor]
            print(f"   ✅ Articoli trovati: {len(articles)}")
            
            return articles
        except Exception as e:
            print(f"❌ Error finding recent articles: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @classmethod
    def find_recent_by_source(cls, source: str, limit: int = 50, language: str = "it") -> list['Article']:
        """Find recent articles by source"""
        try:
            from app import mongo
            print(f"🔍 Cerca articoli recenti per fonte: source={source}, limit={limit}, language={language}")
            
                                               
            filter_query = {'language': language, 'source': source}
            total_source = mongo.db.articles.count_documents(filter_query)
            print(f"   📊 Articoli per fonte '{source}' e lingua '{language}': {total_source}")
            
                                                      
            cursor = mongo.db.articles.find(
                filter_query
            ).sort([('published_date', -1), ('created_at', -1)]).limit(limit)
            
            articles = [cls.from_dict(data) for data in cursor]
            print(f"   ✅ Articoli trovati: {len(articles)}")
            
            return articles
        except Exception as e:
            print(f"❌ Error finding recent articles by source: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @classmethod
    def find_recent_with_offset(cls, limit: int = 6, offset: int = 0, language: str = "it") -> list['Article']:
        """Find recent articles with offset for pagination"""
        try:
            from app import mongo
            print(f"🔍 Cerca articoli con offset: limit={limit}, offset={offset}, language={language}")
            
            cursor = mongo.db.articles.find(
                {'language': language}
            ).sort([('published_date', -1), ('created_at', -1)]).skip(offset).limit(limit)
            
            articles = [cls.from_dict(data) for data in cursor]
            print(f"   ✅ Articoli trovati con offset: {len(articles)}")
            
            return articles
        except Exception as e:
            print(f"❌ Error finding recent articles with offset: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @classmethod
    def count_articles(cls, language: str = "it") -> int:
        """Count total articles for a language"""
        try:
            from app import mongo
            count = mongo.db.articles.count_documents({'language': language})
            print(f"🔢 Conta articoli per lingua '{language}': {count}")
            return count
        except Exception as e:
            print(f"❌ Error counting articles: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    @classmethod
    def find_by_source(cls, source: str, limit: int = 20) -> list['Article']:
        """Find articles by source"""
        try:
            from app import mongo
            cursor = mongo.db.articles.find(
                {'source': source}
            ).sort([('published_date', -1), ('created_at', -1)]).limit(limit)
            
            return [cls.from_dict(data) for data in cursor]
        except Exception as e:
            print(f"❌ Error finding articles by source: {e}")
            return []
    
    def update_content(self, content: str):
        """Update article content"""
        try:
            from app import mongo
            self.content = content
            self.updated_at = datetime.utcnow()
            
            mongo.db.articles.update_one(
                {'_id': self._id},
                {'$set': {
                    'content': content,
                    'updated_at': self.updated_at
                }}
            )
        except Exception as e:
            print(f"❌ Error updating article content: {e}")
            raise

    @classmethod
    def find_all(cls) -> List['Article']:
        """Find all articles"""
        try:
            from app import mongo
            cursor = mongo.db.articles.find().sort('created_at', -1)
            articles = []
            for doc in cursor:
                article = cls()
                article._id = doc['_id']
                article.title = doc.get('title', '')
                article.content = doc.get('content', '')
                article.summary = doc.get('summary', '')
                article.source = doc.get('source', '')
                article.author = doc.get('author', '')
                article.link = doc.get('link', '')
                article.language = doc.get('language', 'it')
                
                             
                if 'published_date' in doc and doc['published_date']:
                    article.published_date = doc['published_date']
                if 'created_at' in doc and doc['created_at']:
                    article.created_at = doc['created_at']
                if 'updated_at' in doc and doc['updated_at']:
                    article.updated_at = doc['updated_at']
                
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Error finding all articles: {e}")
            return []
    
    @classmethod
    def find_by_url(cls, url: str) -> Optional['Article']:
        """Find article by URL (link)"""
        try:
            from app import mongo
            doc = mongo.db.articles.find_one({'link': url})
            if doc:
                return cls.from_dict(doc)
            return None
        except Exception as e:
            print(f"❌ Error finding article by URL: {e}")
            return None
    
    @classmethod
    def find_by_title_and_source(cls, title: str, source: str) -> Optional['Article']:
        """Find article by title and source combination"""
        try:
            from app import mongo
            doc = mongo.db.articles.find_one({
                'title': title,
                'source': source
            })
            if doc:
                return cls.from_dict(doc)
            return None
        except Exception as e:
            print(f"❌ Error finding article by title and source: {e}")
            return None
    
    @classmethod
    def find_similar_title(cls, title: str, similarity_threshold: float = 0.8) -> Optional['Article']:
        """Find article with similar title using basic similarity check"""
        try:
            from app import mongo
            import difflib
            
                                                   
            normalized_title = title.lower().strip()
            
                                              
            cursor = mongo.db.articles.find({})
            
            for doc in cursor:
                existing_title = doc.get('title', '').lower().strip()
                
                                                   
                similarity = difflib.SequenceMatcher(None, normalized_title, existing_title).ratio()
                
                if similarity >= similarity_threshold:
                    return cls.from_dict(doc)
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding similar title: {e}")
            return None
    
    @classmethod
    def find_by_content_similarity(cls, content: str, similarity_threshold: float = 0.8) -> Optional['Article']:
        """Find article with similar content using content similarity check"""
        try:
            from app import mongo
            import difflib
            
                                                      
            normalized_content = content.lower().strip()
            
                                                 
            cursor = mongo.db.articles.find({'content': {'$exists': True, '$ne': ''}})
            
            for doc in cursor:
                existing_content = doc.get('content', '').lower().strip()
                
                if len(existing_content) < 50:                           
                    continue
                
                                                   
                similarity = difflib.SequenceMatcher(None, normalized_content, existing_content).ratio()
                
                if similarity >= similarity_threshold:
                    return cls.from_dict(doc)
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding similar content: {e}")
            return None
    
    @classmethod
    def find_by_date_and_source(cls, published_date: datetime, source: str, hours_window: int = 24) -> List['Article']:
        """Find articles by published date and source within a time window"""
        try:
            from app import mongo
            from datetime import timedelta
            
                                   
            start_time = published_date - timedelta(hours=hours_window)
            end_time = published_date + timedelta(hours=hours_window)
            
                                                                     
            cursor = mongo.db.articles.find({
                'source': source,
                'published_date': {
                    '$gte': start_time,
                    '$lte': end_time
                }
            }).sort('published_date', -1)
            
            articles = [cls.from_dict(doc) for doc in cursor]
            return articles
            
        except Exception as e:
            print(f"❌ Error finding articles by date and source: {e}")
            return []
