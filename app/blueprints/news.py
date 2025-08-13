"""
News blueprint for article management
"""

import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from app.services.news_service import NewsService
from app.models.article import Article
from app.models.settings import Settings
import json

                                    
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

           
news_bp = Blueprint('news', __name__)

@news_bp.route('/')
def index():
    """Main news page"""
    logger.info("📰 PAGINA PRINCIPALE NEWS")
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        language = request.args.get('language', 'it')
        source_filter = request.args.get('source', '')                          
        
                                                                                       
        if source_filter and 'per_page' in request.args:
            from flask import redirect, url_for
            return redirect(url_for('news.index', language=language, source=source_filter))
        
        logger.info(f"   📊 Pagina: {page}, Per pagina: {per_page}, Lingua: {language}, Fonte: {source_filter}")
        
                      
        settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        
                                                               
        from app import mongo
        sources_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        sources_data = list(mongo.db.articles.aggregate(sources_pipeline))
        
                                                       
        logger.info(f"   📊 DEBUG CONTEGGIO FONTI:")
        for doc in sources_data:
            logger.info(f"     - Fonte: '{doc['_id']}' -> {doc['count']} articoli")
        
        available_sources = [
            {
                'name': doc['_id'], 
                'count': doc['count'],
                'display_name': doc['_id'].title() if len(doc['_id']) < 30 else doc['_id']
            } 
            for doc in sources_data if doc['_id'] and doc['_id'].strip()
        ]
        logger.info(f"   📊 Fonti disponibili: {len(available_sources)}")
        
                                                  
        if source_filter:
                                                   
            from app import mongo
            
                                                   
            total_articles = mongo.db.articles.count_documents({})
            logger.info(f"   📊 DEBUG: Articoli totali nel database: {total_articles}")
            
                                       
            articles_by_lang = mongo.db.articles.count_documents({'language': language})
            logger.info(f"   📊 DEBUG: Articoli per lingua '{language}': {articles_by_lang}")
            
                                                       
            articles_by_source_exact = mongo.db.articles.count_documents({'source': source_filter})
            logger.info(f"   📊 DEBUG: Articoli per fonte ESATTA '{source_filter}': {articles_by_source_exact}")
            
                                                         
            import re
            articles_by_source_regex = mongo.db.articles.count_documents({'source': {'$regex': f'^{re.escape(source_filter)}$', '$options': 'i'}})
            logger.info(f"   📊 DEBUG: Articoli per fonte CASE-INSENSITIVE '{source_filter}': {articles_by_source_regex}")
            
                                                       
            all_sources = mongo.db.articles.distinct('source')
            logger.info(f"   📊 DEBUG: Tutte le fonti nel database: {all_sources}")
            
                                                            
            filter_query = {'source': source_filter}                            
            logger.info(f"   📊 DEBUG: Query finale: {filter_query}")
            
                                      
            cursor = mongo.db.articles.find(filter_query).sort([('published_date', -1), ('created_at', -1)])
            raw_data = list(cursor)                            
            logger.info(f"   📊 DEBUG: Dati raw trovati: {len(raw_data)}")
            
                                             
            articles = []
            for i, data in enumerate(raw_data):
                try:
                    article = Article.from_dict(data)
                    articles.append(article)
                    logger.info(f"   📊 DEBUG: Articolo {i+1} convertito: {data.get('title', 'N/A')[:50]}...")
                except Exception as e:
                    logger.error(f"   ❌ DEBUG: Errore conversione articolo {i+1}: {e}")
            
            logger.info(f"   ✅ Articoli trovati per fonte '{source_filter}': {len(articles)} (tutti - query diretta)")
        else:
                                                      
            articles = Article.find_recent(limit=per_page, language=language)
            logger.info(f"   ✅ Articoli trovati: {len(articles)}")
        
        logger.info(f"   🎨 Rendering template con source_filter='{source_filter}'")
        
        return render_template('news/index.html', 
                             articles=articles, 
                             page=page, 
                             per_page=per_page,
                             language=language,
                             source_filter=source_filter,
                             available_sources=available_sources,
                             settings=settings)
                             
    except Exception as e:
        logger.error(f"   ❌ ERRORE nella pagina principale news: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return render_template('news/index.html', 
                             articles=[], 
                             page=1, 
                             per_page=15, 
                             language='it',
                             source_filter='',
                             available_sources=[],
                             settings=Settings.get_default_settings())

@news_bp.route('/fetch')
def fetch_news():
    """Fetch fresh news from RSS feeds"""
    logger.info("🔄 FETCH NEWS DA RSS")
    
    try:
        news_service = NewsService()
        articles = news_service.fetch_multiple_sources(max_articles_per_source=10)
        logger.info(f"   📰 Articoli recuperati: {len(articles)}")
        
                          
        saved_ids = news_service.save_articles_to_db(articles)
        logger.info(f"   💾 Articoli salvati: {len(saved_ids)}")
        
                                          
        if request.headers.get('HX-Request'):
                                             
            recent_articles = Article.find_recent(limit=20, language='it')
                                           
            return render_template('news/timeline.html', articles=recent_articles)
        else:
                                                   
            return jsonify({
                'success': True,
                'message': f'Fetched {len(articles)} articles, saved {len(saved_ids)} new ones',
                'articles_count': len(articles),
                'saved_count': len(saved_ids)
            })
            
    except Exception as e:
        logger.error(f"   ❌ ERRORE nel fetch news: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        
        if request.headers.get('HX-Request'):
            return f'<div class="alert alert-danger">Errore nel caricamento: {str(e)}</div>', 500
        else:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@news_bp.route('/article/<article_id>')
def view_article(article_id):
    """View single article"""
    logger.info(f"📖 VISUALIZZAZIONE ARTICOLO: {article_id}")
    
    try:
        article = Article.find_by_id(article_id)
        logger.info(f"   📊 Articolo trovato: {'✅' if article else '❌'}")
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        return render_template('news/article.html', article=article)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nella visualizzazione articolo: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@news_bp.route('/api/articles')
def api_articles():
    """API endpoint for articles"""
    logger.info("📡 API ARTICOLI")
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        language = request.args.get('language', 'it')
        source = request.args.get('source')
        
        logger.info(f"   📊 Pagina: {page}, Per pagina: {per_page}, Lingua: {language}, Fonte: {source}")
        
                     
        query = {'language': language}
        if source:
            query['source'] = source
        
                                    
        articles = Article.find_recent(limit=per_page, language=language)
        
                                             
        articles_data = []
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'source': article.source,
                'author': article.author,
                'link': article.link,
                'published_date': article.published_date.isoformat() if article.published_date else None,
                'language': article.language
            })
        
                                        
        total_count = Article.count_articles(language=language)
        
        logger.info(f"   ✅ Articoli restituiti: {len(articles_data)}")
        
        return jsonify({
            'articles': articles_data,
            'page': page,
            'per_page': per_page,
            'total': total_count
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API articoli: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@news_bp.route('/update-existing', methods=['POST'])
def update_existing_articles():
    """Update existing articles without creating duplicates"""
    logger.info("🔄 AGGIORNAMENTO ARTICOLI ESISTENTI")
    
    try:
        news_service = NewsService()
        
                            
        articles = news_service.fetch_multiple_sources(max_articles_per_source=10)
        logger.info(f"   📰 Articoli recuperati: {len(articles)}")
        
                                                            
        saved_ids = news_service.save_articles_to_db(articles)
        logger.info(f"   💾 Articoli nuovi salvati: {len(saved_ids)}")
        
        return jsonify({
            'success': True,
            'message': f'Aggiornamento completato: {len(saved_ids)} nuovi articoli aggiunti',
            'total_fetched': len(articles),
            'new_articles': len(saved_ids)
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE aggiornamento articoli: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@news_bp.route('/api/debug/articles')
def api_debug_articles():
    """Debug articles database"""
    logger.info("🐛 API DEBUG ARTICOLI")
    
    try:
        from app import mongo
        
                              
        total_count = mongo.db.articles.count_documents({})
        
                           
        db_name = mongo.db.name
        collection_name = 'articles'
        
                             
        sample_articles = list(mongo.db.articles.find().limit(3))
        sample_count = len(sample_articles)
        
                              
        try:
            collection_stats = mongo.db.command("collStats", "articles")
            collection_size = collection_stats.get('size', 0)
        except:
            collection_size = 0
        
        logger.info(f"   📊 Debug risultati: {total_count} articoli nel database")
        
        return jsonify({
            'success': True,
            'total_count': total_count,
            'database_name': db_name,
            'collection_name': collection_name,
            'sample_count': sample_count,
            'collection_size': collection_size,
            'message': f'Database funzionante correttamente con {total_count} articoli'
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE DEBUG articoli: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@news_bp.route('/timeline')
def get_timeline():
    """Get timeline of recent articles for display"""
    logger.info("📅 TIMELINE ARTICOLI")
    
    try:
                                                             
        articles = Article.find_recent(limit=4, language='it')
        logger.info(f"   ✅ Timeline articoli: {len(articles)}")
        
        return render_template('news/timeline.html', articles=articles, has_more=True)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE timeline: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return f'<div class="alert alert-danger">Errore nel caricamento: {str(e)}</div>', 500

@news_bp.route('/timeline/more')
def get_more_timeline():
    """Get more articles for infinite scroll"""
    logger.info("📅 TIMELINE MORE ARTICOLI")
    
    try:
        offset = request.args.get('offset', 0, type=int)
        limit = 4                                           
        
        logger.info(f"   📊 Offset: {offset}, Limite: {limit}")
        
                                  
        articles = Article.find_recent_with_offset(limit=limit, offset=offset, language='it')
        
                                          
        total_count = Article.count_articles(language='it')
        has_more = (offset + limit) < total_count
        
        logger.info(f"   ✅ Articoli caricati: {len(articles)}, Has more: {has_more}")
        
        return render_template('news/timeline_more.html', articles=articles, has_more=has_more, offset=offset + limit)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE timeline more: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return f'<div class="alert alert-danger">Errore nel caricamento: {str(e)}</div>', 500

@news_bp.route('/api/sources')
def api_sources():
    """Get available news sources with article counts"""
    logger.info("📊 API FONTI DISPONIBILI")
    
    try:
        from app import mongo
        
                                                                            
        pipeline = [
            {"$group": {
                "_id": "$source",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},                                               
            {"$limit": 50}                             
        ]
        
        sources_data = list(mongo.db.articles.aggregate(pipeline))
        
                              
        sources = []
        total_articles = 0
        
        for source_doc in sources_data:
            source_name = source_doc['_id']
            article_count = source_doc['count']
            
            if source_name and source_name.strip():                     
                sources.append({
                    'name': source_name,
                    'count': article_count,
                    'display_name': source_name.title() if len(source_name) < 30 else source_name
                })
                total_articles += article_count
        
        logger.info(f"   ✅ Fonti trovate: {len(sources)}")
        logger.info(f"   📰 Articoli totali: {total_articles}")
        
        return jsonify({
            'success': True,
            'sources': sources,
            'total_sources': len(sources),
            'total_articles': total_articles
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API fonti: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@news_bp.route('/api/articles/<article_id>')
def api_article(article_id):
    """Get single article by ID"""
    logger.info(f"📡 API ARTICOLO SINGOLO: {article_id}")
    
    try:
        article = Article.find_by_id(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        logger.info(f"   ✅ Articolo trovato: {article.title[:50]}...")
        
        return jsonify({
            'id': article.id,
            'title': article.title,
            'summary': article.summary,
            'content': article.content,
            'source': article.source,
            'author': article.author,
            'link': article.link,
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'language': article.language
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API articolo singolo: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@news_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Quick analysis endpoint for text or URL"""
    logger.info("🔍 API ANALISI RAPIDA")
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text or URL required'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Text or URL cannot be empty'}), 400
        
        logger.info(f"   📝 Testo da analizzare: {len(text)} caratteri")
        
                                                 
                                         
        analysis_result = {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'sentiment': 'neutral',
            'key_topics': ['news', 'information'],
            'summary': f'Analisi del testo: {len(text)} caratteri analizzati',
            'confidence': 0.85
        }
        
        logger.info(f"   ✅ Analisi completata")
        
        return jsonify({
            'success': True,
            'analysis': analysis_result
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API analisi: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@news_bp.route('/api/stats')
def api_dashboard_stats():
    """Dashboard statistics endpoint"""
    logger.info("📊 API STATISTICHE DASHBOARD - INIZIO")
    
    try:
        from app.models.article import Article
        from app.models.settings import Settings
        from datetime import datetime, timedelta
        
                                  
        total_articles = Article.count_articles()
        
                                                                                     
        settings = Settings.find_by_user_id('default')
        total_sources = 0
        if settings and settings.rss_sources:
                                                  
            sources_list = [s.strip() for s in settings.rss_sources.split('\n') if s.strip()]
            total_sources = len(sources_list)
        else:
                                                
            default_settings = Settings.get_default_settings()
            sources_list = [s.strip() for s in default_settings.rss_sources.split('\n') if s.strip()]
            total_sources = len(sources_list)
        
                                                                  
        if settings and settings.ai_provider:
            ai_provider = 'Ollama' if settings.ai_provider == 'ollama' else 'OpenAI'
        else:
            ai_provider = 'Ollama'                      
        
                                                    
        try:
            from app.models.analysis import Analysis
            from app import mongo
            
                                      
            total_analysis = mongo.db.analyses.count_documents({'status': 'completed'})
            
                                              
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_analysis = mongo.db.analyses.count_documents({
                'status': 'completed',
                'created_at': {'$gte': today_start}
            })
            
            logger.info(f"   📊 Analisi completate: totali={total_analysis}, oggi={today_analysis}")
            
        except Exception as analysis_error:
            logger.error(f"   ❌ Errore conteggio analisi: {analysis_error}")
            total_analysis = 0
            today_analysis = 0
        
                                                    
        ai_used_count = 0
        
                                                                      
        if total_analysis > 0:
            ai_used_count = 1
        else:
            ai_used_count = 0
        
                                                             
        try:
            last_article = mongo.db.articles.find().sort('created_at', -1).limit(1)
            last_article_doc = list(last_article)
            if last_article_doc:
                last_update = last_article_doc[0]['created_at'].strftime('%d/%m/%Y %H:%M')
            else:
                last_update = 'Nessun articolo'
        except:
            last_update = datetime.now().strftime('%d/%m/%Y %H:%M')
        
                                  
        sources_status = 'OK' if total_sources > 0 else 'Nessuna fonte'
        
        stats = {
            'total_articles': total_articles,
            'total_sources': total_sources,
            'ai_used_count': ai_used_count,
            'ai_provider': ai_provider,
            'total_analysis': total_analysis,
            'today_analysis': today_analysis,
            'last_update': last_update,
            'sources_status': sources_status
        }
        
        logger.info(f"   ✅ Statistiche calcolate: {total_articles} articoli, {total_sources} fonti, {ai_used_count} AI")
        logger.info(f"   📊 FINE API STATISTICHE - Restituisco: {stats}")
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API statistiche: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
