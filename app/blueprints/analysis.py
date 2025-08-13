"""
Analysis blueprint for critical news analysis
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, redirect
from app.services.analysis_service import AnalysisService
from app.models.article import Article
from app.models.analysis import Analysis
import json

                                    
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

           
analysis_bp = Blueprint('analysis', __name__)

                       
@analysis_bp.app_template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to dict/list"""
    if isinstance(value, str):
        try:
            import json
                                             
            result = json.loads(value)
            logger.info(f"✅ Parsed JSON successfully: {len(str(result))} chars")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"❌ JSON parsing fallito: {e}")
            logger.error(f"   📝 Content preview: {value[:300]}...")
            
                                                                               
            try:
                import ast
                result = ast.literal_eval(value)
                logger.warning(f"⚠️ Fallback to Python dict parsing: {len(str(result))} chars")
                return result
            except (ValueError, SyntaxError) as ast_error:
                logger.error(f"❌ Anche ast.literal_eval è fallito: {ast_error}")
                return None
    return value

@analysis_bp.route('/')
def index():
    """Analysis main page"""
    logger.info("🏠 PAGINA PRINCIPALE ANALISI")
    
    try:
                             
        analysis_service = AnalysisService.with_orchestrator()
        recent_analyses = analysis_service.get_analysis_history(limit=50)                                      
        logger.info(f"   📊 Analisi recenti trovate: {len(recent_analyses)}")
        
                                                                
        for i, analysis in enumerate(recent_analyses[:3]):
            logger.info(f"   🔍 Analisi {i}: ID={getattr(analysis, 'id', 'N/A')}, Status={getattr(analysis, 'status', 'N/A')}, Type={getattr(analysis, 'analysis_type', 'N/A')}")
            logger.info(f"   🔍 Result type: {type(getattr(analysis, 'result', None))}")
            if hasattr(analysis, 'result') and analysis.result:
                result_preview = str(analysis.result)[:200] + "..." if len(str(analysis.result)) > 200 else str(analysis.result)
                logger.info(f"   🔍 Result preview: {result_preview}")
        
                                              
        all_statuses = [getattr(a, 'status', 'N/A') for a in recent_analyses]
        logger.info(f"   📊 Tutti gli status trovati: {all_statuses}")
        
                                                          
        try:
            from app import mongo
            db_statuses = list(mongo.db.analyses.find({}, {'status': 1, '_id': 0}))
            db_status_values = [doc.get('status', 'N/A') for doc in db_statuses]
            logger.info(f"   🗄️ Status dal database direttamente: {db_status_values}")
        except Exception as db_error:
            logger.error(f"   ❌ Errore lettura status dal DB: {db_error}")
        
                             
        stats = calculate_analysis_stats(recent_analyses)
        logger.info(f"   📈 Statistiche calcolate: {stats}")
        
                                 
        completed_count = sum(1 for a in recent_analyses if getattr(a, 'status', 'unknown') == 'completed')
        processing_count = sum(1 for a in recent_analyses if getattr(a, 'status', 'unknown') == 'processing')
        failed_count = sum(1 for a in recent_analyses if getattr(a, 'status', 'unknown') == 'failed')
        logger.info(f"   🔢 Conteggio manuale: completed={completed_count}, processing={processing_count}, failed={failed_count}")
        
        return render_template('analysis/index.html', analyses=recent_analyses, stats=stats)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nella pagina principale: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return render_template('analysis/index.html', analyses=[], stats=calculate_analysis_stats([]))

def calculate_analysis_stats(analyses):
    """Calculate statistics for analyses"""
    if not analyses:
        return {
            'completed': 0,
            'processing': 0,
            'failed': 0,
            'success_rate': 0.0
        }
    
    completed = sum(1 for a in analyses if getattr(a, 'status', 'unknown') == 'completed')
    processing = sum(1 for a in analyses if getattr(a, 'status', 'unknown') == 'processing')
    failed = sum(1 for a in analyses if getattr(a, 'status', 'unknown') == 'failed')
    
    total = len(analyses)
    success_rate = (completed / total * 100) if total > 0 else 0.0
    
    return {
        'completed': completed,
        'processing': processing,
        'failed': failed,
        'success_rate': success_rate
    }

@analysis_bp.route('/article/<article_id>')
def analyze_article(article_id):
    """Analyze a specific article"""
    logger.info(f"🔍 ANALISI ARTICOLO: {article_id}")
    
    try:
        article = Article.find_by_id(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        logger.info(f"   📰 Articolo trovato: {article.title[:50]}...")
        
                                                            
        if request.headers.get('HX-Request'):
            return render_template('analysis/analyze_article_modal.html', article=article)
        else:
                                                
                    return render_template('analysis/analyze_article.html', article=article)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nell'analisi articolo: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_article_form():
    """Form endpoint for article analysis - redirects to analysis page"""
    logger.info("📋 FORM ANALISI ARTICOLO")
    
    try:
        article_id = request.form.get('article_id')
        provider = request.form.get('provider', 'ollama')
        language = request.form.get('language', 'it')
        
        if not article_id:
            logger.error("   ❌ Article ID mancante")
            return redirect('/news')
        
        logger.info(f"   📰 Article ID: {article_id}")
        logger.info(f"   🤖 Provider: {provider}")
        logger.info(f"   🌍 Language: {language}")
        
                                                        
        return redirect(f'/analysis/article/{article_id}')
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE form analisi: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return redirect('/news')

@analysis_bp.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for article analysis"""
    logger.info("🔍 API ANALISI ARTICOLO")
    
    try:
                                
        logger.info(f"   📤 Content-Type: {request.content_type}")
        logger.info(f"   📤 Form data: {request.form}")
        logger.info(f"   📤 JSON data: {request.get_json(silent=True)}")
        
                                        
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
                              
            data = {
                'article_id': request.form.get('article_id'),
                'text': request.form.get('text'),
                'provider': request.form.get('provider', 'ollama'),
                'language': request.form.get('language', 'it')
            }
        
        logger.info(f"   📊 Dati processati: {data}")
        
        article_id = data.get('article_id')
        text = data.get('text')
        provider = data.get('provider', 'ollama')
        language = data.get('language', 'it')
        
        logger.info(f"   📰 Article ID: {article_id}, Text: {len(text) if text else 0} caratteri, Provider: {provider}, Lingua: {language}")
        
                                        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
                                                             
        try:
            logger.info("   🔧 Inizializzazione AnalysisService con orchestrator...")
            analysis_service = AnalysisService.with_orchestrator()
            logger.info("   ✅ AnalysisService con orchestrator inizializzato con successo")
        except Exception as service_error:
            logger.error(f"   ❌ Errore inizializzazione AnalysisService con orchestrator: {service_error}")
            logger.info("   🔄 Fallback a AnalysisService di default...")
            try:
                analysis_service = AnalysisService.create_default()
                logger.info("   ✅ AnalysisService di default inizializzato con successo")
            except Exception as fallback_error:
                logger.error(f"   ❌ Errore inizializzazione AnalysisService di default: {fallback_error}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Service initialization failed: {str(fallback_error)}'
                }), 500
                
        if article_id:
                                      
            try:
                logger.info(f"   🚀 Avvio analisi articolo per ID: {article_id}")
                result = analysis_service.analyze_article_critically(
                    article_id=article_id,
                    provider=provider,
                    language=language
                )
                logger.info(f"   ✅ Analisi completata con successo: {result}")
                return jsonify(result)
            except Exception as analysis_error:
                logger.error(f"   ❌ Errore durante analisi articolo: {analysis_error}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Analysis failed: {str(analysis_error)}'
                }), 500
        elif text:
                                 
            try:
                logger.info(f"   🚀 Avvio analisi testo per: {text[:50]}...")
                result = analysis_service.analyze_custom_text(
                    text=text,
                    title='Testo personalizzato',
                    provider=provider,
                    language=language
                )
                logger.info(f"   ✅ Analisi testo completata con successo: {result}")
                return jsonify(result)
            except Exception as text_error:
                logger.error(f"   ❌ Errore durante analisi testo: {text_error}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Text analysis failed: {str(text_error)}'
                }), 500
        else:
            return jsonify({'error': 'Either article_id or text is required'}), 400
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE in api_analyze: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analyze-text', methods=['POST'])
def api_analyze_text():
    """API endpoint for custom text analysis"""
    logger.info("📝 API ANALISI TESTO - ENDPOINT CHIAMATO!")
    logger.info(f"   📥 Request method: {request.method}")
    logger.info(f"   📥 Content-Type: {request.headers.get('Content-Type')}")
    logger.info(f"   📥 Request data: {request.data}")
    
    try:
        data = request.get_json()
        text = data.get('text')
        title = data.get('title', 'Testo personalizzato')
        provider = data.get('provider', 'ollama')
        language = data.get('language', 'it')
        
        if not text:
            return jsonify({'error': 'Text required'}), 400
        
        logger.info(f"   📝 Testo da analizzare: {len(text)} caratteri")
        logger.info(f"   📰 Titolo: {title}")
        logger.info(f"   🤖 Provider: {provider}")
        logger.info(f"   🌍 Lingua: {language}")
        
        analysis_service = AnalysisService.create_default()
        result = analysis_service.analyze_custom_text(
            text=text,
            title=title,
            provider=provider,
            language=language
        )
        
        logger.info(f"   ✅ Analisi testo completata")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nell'analisi testo: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analyze-url', methods=['POST'])
def api_analyze_url():
    """API endpoint for URL analysis"""
    logger.info("🔗 API ANALISI URL - ENDPOINT CHIAMATO!")
    logger.info(f"   📥 Request method: {request.method}")
    logger.info(f"   📥 Content-Type: {request.headers.get('Content-Type')}")
    logger.info(f"   📥 Request data: {request.data}")
    
    try:
        data = request.get_json()
        url = data.get('url')
        provider = data.get('provider', 'ollama')
        language = data.get('language', 'it')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        logger.info(f"   🔗 URL da analizzare: {url}")
        logger.info(f"   🤖 Provider: {provider}")
        logger.info(f"   🌍 Lingua: {language}")
        
        analysis_service = AnalysisService.create_default()
        result = analysis_service.analyze_url(
            url=url,
            provider=provider,
            language=language
        )
        
        logger.info(f"   ✅ Analisi URL completata")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nell'analisi URL: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analysis/<analysis_id>')
def api_get_analysis(analysis_id):
    """Get analysis by ID"""
    logger.info(f"📖 API GET ANALISI: {analysis_id}")
    
    try:
        analysis_service = AnalysisService.create_default()
        analysis = analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        logger.info(f"   ✅ Analisi trovata: {analysis_id}")
        
        return jsonify({
            'id': analysis.id,
            'article_id': analysis.article_id,
            'analysis_type': analysis.analysis_type,
            'provider': analysis.provider,
            'model': analysis.model,
            'language': analysis.language,
            'result': analysis.result,
            'status': analysis.status,
            'created_at': analysis.created_at.isoformat(),
            'updated_at': analysis.updated_at.isoformat(),
            'processing_time': analysis.processing_time,
            'error_message': analysis.error_message
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nel recupero analisi: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analyses')
def api_analyses():
    """Get recent analyses"""
    logger.info("📊 API ANALISI RECENTI")
    
    try:
        limit = request.args.get('limit', 20, type=int)
        logger.info(f"   📊 Limite: {limit}")
        
        analysis_service = AnalysisService.create_default()
        analyses = analysis_service.get_analysis_history(limit=limit)
        
        analyses_data = []
        for analysis in analyses:
            analyses_data.append({
                'id': analysis.id,
                'article_id': analysis.article_id,
                'analysis_type': analysis.analysis_type,
                'provider': analysis.provider,
                'model': analysis.model,
                'status': analysis.status,
                'created_at': analysis.created_at.isoformat(),
                'processing_time': analysis.processing_time
            })
        
        logger.info(f"   ✅ Analisi restituite: {len(analyses_data)}")
        
        return jsonify({
            'analyses': analyses_data,
            'total': len(analyses_data)
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE nel recupero analisi recenti: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analyses/refresh')
def api_refresh_analyses():
    """Refresh analyses data for real-time updates"""
    logger.info("🔄 API REFRESH ANALISI")
    
    try:
        analysis_service = AnalysisService.with_orchestrator()
        analyses = analysis_service.get_analysis_history(limit=50)
        
                                        
        stats = calculate_analysis_stats(analyses)
        
        return jsonify({
            'success': True,
            'analyses': [analysis.to_dict() if hasattr(analysis, 'to_dict') else str(analysis) for analysis in analyses],
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE API REFRESH ANALISI: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/articles/delete-all', methods=['DELETE'])
def api_delete_all_articles():
    """Delete all articles from database"""
    logger.info("🗑️ API ELIMINA TUTTI GLI ARTICOLI")
    
    try:
        from app import mongo
        
                                    
        result = mongo.db.articles.delete_many({})
        deleted_count = result.deleted_count
        
        logger.info(f"   ✅ Articoli eliminati: {deleted_count}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Eliminati {deleted_count} articoli'
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE eliminazione articoli: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/api/analyses/delete-all', methods=['DELETE'])
def api_delete_all_analyses():
    """Delete all analyses from database"""
    logger.info("🗑️ API ELIMINA TUTTE LE ANALISI")
    
    try:
        from app import mongo
        
                                  
        result = mongo.db.analyses.delete_many({})
        deleted_count = result.deleted_count
        
        logger.info(f"   ✅ Analisi eliminate: {deleted_count}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Eliminate {deleted_count} analisi'
        })
        
    except Exception as e:
        logger.error(f"   ❌ ERRORE eliminazione analisi: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/result/<analysis_id>')
def view_result(analysis_id):
    """View analysis result"""
    logger.info(f"📖 VISUALIZZAZIONE RISULTATO ANALISI: {analysis_id}")
    
    try:
        analysis_service = AnalysisService.create_default()
        analysis_data = analysis_service.get_analysis_by_id(analysis_id)
        
        if not analysis_data:
            return jsonify({'error': 'Analysis not found'}), 404
        
                                                                
        logger.info(f"   📊 Dati analisi ricevuti: {list(analysis_data.keys())}")
        
                                                                                            
        article = None
        analysis_type = analysis_data.get('analysis_type', '')
        
        if analysis_type in ['custom_url', 'custom_text']:
            logger.info(f"   🔗 Analisi personalizzata di tipo: {analysis_type}")
            
                                                                                   
            try:
                result = analysis_data.get('result', {})
                if isinstance(result, str):
                    import json
                    result = json.loads(result)
                
                                                               
                if analysis_type == 'custom_url' and 'scraped_article' in result:
                    scraped_data = result['scraped_article']
                                                                          
                    from app.models.article import Article
                    article = Article(
                        title=scraped_data.get('title', 'Analisi URL'),
                        content=scraped_data.get('content', ''),
                        source=scraped_data.get('source', ''),
                        link=scraped_data.get('url', result.get('scraped_url', '')),
                        author=scraped_data.get('author'),
                        published_date=None,                                         
                        language=analysis_data.get('language', 'it')
                    )
                    logger.info(f"   ✅ Pseudo-articolo creato da URL: {article.title[:50]}...")
                    
                elif analysis_type == 'custom_text':
                                                                      
                    from app.models.article import Article
                    article = Article(
                        title=result.get('custom_title', 'Analisi Testo Personalizzato'),
                        content=result.get('original_text', 'Testo non disponibile'),
                        source='Testo personalizzato',
                        link='',
                        author=None,
                        published_date=None,
                        language=analysis_data.get('language', 'it')
                    )
                    logger.info(f"   ✅ Pseudo-articolo creato da testo personalizzato: {article.title[:50]}...")
                    
            except Exception as custom_error:
                logger.error(f"   ❌ Errore creazione pseudo-articolo: {custom_error}")
                article = None
        
        elif analysis_data.get('article_id'):
                                      
            from app.models.article import Article
            article = Article.find_by_id(analysis_data['article_id'])
            logger.info(f"   📰 Articolo associato: {'✅ Trovato' if article else '❌ Non trovato'}")
        else:
            logger.warning("   ⚠️ Nessun article_id nell'analisi")

                                                                                    
        try:
            result = analysis_data.get('result', {})
            if isinstance(result, str):
                stripped = result.strip()
                if stripped.startswith('{') or stripped.startswith('['):
                    import json
                    analysis_data['result'] = json.loads(result)
                    logger.info("   ✅ Result JSON parsato correttamente")
        except Exception as parse_error:
            logger.warning(f"   ⚠️ Errore parsing result JSON: {parse_error}")
                                                 
        
        logger.info(f"   ✅ Risultato analisi caricato per template")
        
        return render_template('analysis/result.html', 
                             analysis=analysis_data,                       
                             article=article,
                             analysis_service=analysis_service)
                             
    except Exception as e:
        logger.error(f"   ❌ ERRORE nella visualizzazione risultato: {e}")
        logger.error("   📍 Stack trace completo:", exc_info=True)
        return jsonify({'error': str(e)}), 500
