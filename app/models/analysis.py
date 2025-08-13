"""
Analysis model for MongoDB
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId

class Analysis:
    """Analysis model for news analysis results"""
    
    def __init__(self, article_id: str, analysis_type: str, provider: str, 
                 model: str, language: str, result: str = "", 
                 status: str = "pending", processing_time: float = 0.0,
                 error_message: str = ""):
        self.article_id = article_id
        self.analysis_type = analysis_type
        self.provider = provider
        self.model = model
        self.language = language
        self.result = result
        self.status = status
        self.processing_time = processing_time
        self.error_message = error_message
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary"""
        return {
            'id': str(getattr(self, '_id', getattr(self, 'id', 'N/A'))),
            'article_id': self.article_id,
            'analysis_type': self.analysis_type,
            'provider': self.provider,
            'model': self.model,
            'language': self.language,
            'status': self.status,
            'result': self.result,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Analysis':
        """Create analysis from dictionary"""
        analysis = cls(
            article_id=data['article_id'],
            analysis_type=data['analysis_type'],
            provider=data['provider'],
            model=data['model'],
            language=data['language'],
            result=data.get('result', ''),
            status=data.get('status', 'pending'),
            processing_time=data.get('processing_time', 0.0),
            error_message=data.get('error_message', '')
        )
        if '_id' in data:
            analysis._id = data['_id']
            analysis.id = str(data['_id'])
        
                                     
        if 'created_at' in data:
            analysis.created_at = data['created_at']
        if 'updated_at' in data:
            analysis.updated_at = data['updated_at']
            
        return analysis
    
    def save(self) -> str:
        """Save analysis to database"""
        try:
            from app import mongo
            
                            
            if not self.created_at:
                self.created_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            
                              
            doc = {
                'article_id': self.article_id,
                'analysis_type': self.analysis_type,
                'provider': self.provider,
                'model': self.model,
                'language': self.language,
                'status': self.status,
                'result': self.result,
                'processing_time': self.processing_time,
                'error_message': self.error_message,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }
            
                                  
            result = mongo.db.analyses.insert_one(doc)
            self._id = result.inserted_id
            
            print(f"✅ Analysis saved with ID: {self._id}")
            return str(self._id)
            
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
            raise
    
    def update_status(self, status: str = None, result: Any = None, processing_time: float = None, error_message: str = None):
        """Update analysis status and result"""
        try:
            from app import mongo
            
                           
            if status is not None:
                self.status = status
            if result is not None:
                self.result = result
            if processing_time is not None:
                self.processing_time = processing_time
            if error_message is not None:
                self.error_message = error_message
            
                              
            self.updated_at = datetime.utcnow()
            
                                     
            update_doc = {}
            if status is not None:
                update_doc['status'] = status
            if result is not None:
                update_doc['result'] = result
            if processing_time is not None:
                update_doc['processing_time'] = processing_time
            if error_message is not None:
                update_doc['error_message'] = error_message
            
            update_doc['updated_at'] = self.updated_at
            
                                
            mongo.db.analyses.update_one(
                {'_id': self._id},
                {'$set': update_doc}
            )
            
            print(f"✅ Analysis {self._id} status updated to: {self.status}")
            
        except Exception as e:
            print(f"❌ Error updating analysis status: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, analysis_id: str) -> Optional['Analysis']:
        """Find analysis by ID"""
        try:
            from app import mongo
            data = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
            if data:
                return cls.from_dict(data)
        except Exception as e:
            print(f"❌ Error finding analysis by ID: {e}")
        return None
    
    @classmethod
    def find_by_article(cls, article_id: str, limit: int = 10) -> list['Analysis']:
        """Find analyses by article ID"""
        try:
            from app import mongo
            cursor = mongo.db.analyses.find(
                {'article_id': article_id}
            ).sort('created_at', -1).limit(limit)
            
            return [cls.from_dict(data) for data in cursor]
        except Exception as e:
            print(f"❌ Error finding analyses by article: {e}")
            return []
    
    @classmethod
    def find_recent(cls, limit: int = 10) -> List['Analysis']:
        """Find recent analyses"""
        try:
            from app import mongo
            cursor = mongo.db.analyses.find().sort('created_at', -1).limit(limit)
            analyses = []
            for doc in cursor:
                                                                  
                analysis = cls.from_dict(doc)
                                                            
                analysis.id = str(doc['_id'])
                analyses.append(analysis)
            
            return analyses
        except Exception as e:
            print(f"Error finding recent analyses: {e}")
            return []
    
    @classmethod
    def find_by_status(cls, status: str, limit: int = 20) -> list['Analysis']:
        """Find analyses by status"""
        try:
            from app import mongo
            cursor = mongo.db.analyses.find({'status': status}).sort('created_at', -1).limit(limit)
            return [cls.from_dict(data) for data in cursor]
        except Exception as e:
            print(f"❌ Error finding analyses by status: {e}")
            return []

    @classmethod
    def find_by_article_id(cls, article_id: str) -> Optional['Analysis']:
        """Find analysis by article ID"""
        try:
            from app import mongo
            doc = mongo.db.analyses.find_one({'article_id': article_id})
            if doc:
                analysis = cls.from_dict(doc)
                analysis.id = str(doc['_id'])
                return analysis
            return None
        except Exception as e:
            print(f"Error finding analysis by article ID: {e}")
            return None
