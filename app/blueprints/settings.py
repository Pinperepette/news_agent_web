"""
Settings blueprint for configuration management
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from app.models.settings import Settings
from app.config import Config
import json
import html

settings_bp = Blueprint('settings', __name__)


def _mask_key_for_display(key: str) -> str:
    """Return a masked representation of an API key for UI display.
    Shows a fixed number of asterisks so the real length isn't leaked.
    """
    if not key:
        return ''
    return '************'                

@settings_bp.route('/')
def index():
    """Settings main page"""
                          
    settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
    
                                                          
    if hasattr(settings, 'rss_sources') and settings.rss_sources:
        if '&#10;' in str(settings.rss_sources) or len(str(settings.rss_sources)) < 50:
            settings.rss_sources = "https://www.ansa.it/sito/ansait_rss.xml\nhttps://www.repubblica.it/rss/homepage/rss2.0.xml\nhttps://www.corriere.it/rss/homepage.xml\nhttps://www.ilsole24ore.com/rss/homepage.xml"
            settings.save()
    
    return render_template('settings/index.html', 
                         settings=settings, 
                         config=Config)

@settings_bp.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get current settings"""
    settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
    
                                        
    rss_sources = settings.rss_sources
    if isinstance(rss_sources, str):
                                                        
        rss_sources = html.unescape(rss_sources)
                                     
        rss_sources = rss_sources.replace('\r\n', '\n').replace('\r', '\n')
                                                
        lines = [line.strip() for line in rss_sources.split('\n') if line.strip()]
        rss_sources = '\n'.join(lines)
    
    return jsonify({
        'ai_provider': settings.ai_provider,
        'ai_model': settings.ai_model,
        'language': settings.language,
        'articles_per_page': settings.articles_per_page,
        'enable_multilingual': settings.enable_multilingual,
        'rss_sources': rss_sources
    })

@settings_bp.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update settings"""
    try:
                                        
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
                                    
            data['enable_multilingual'] = 'enable_multilingual' in data
        
                              
        settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        
                         
        if 'ai_provider' in data:
            settings.ai_provider = data['ai_provider']
        if 'ai_model' in data:
            settings.ai_model = data['ai_model']
        if 'language' in data:
            settings.language = data['language']
        if 'articles_per_page' in data:
            settings.articles_per_page = int(data['articles_per_page'])
        if 'enable_multilingual' in data:
            settings.enable_multilingual = bool(data['enable_multilingual'])
        if 'rss_sources' in data:
                                                                                    
            rss_sources = data['rss_sources']
            if isinstance(rss_sources, str):
                                                                
                rss_sources = html.unescape(rss_sources)
                                             
                rss_sources = rss_sources.replace('\r\n', '\n').replace('\r', '\n')
                                                        
                lines = [line.strip() for line in rss_sources.split('\n') if line.strip()]
                rss_sources = '\n'.join(lines)
            settings.rss_sources = rss_sources
        
                       
        settings.save()
        
                              
        return jsonify({
            'success': True,
            'message': 'Impostazioni salvate con successo! Le modifiche sono state applicate immediatamente.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/api-keys', methods=['POST'])
def api_update_api_keys():
    """Update API keys"""
    try:
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
                              
        settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        print(f"DEBUG: Current settings before update: openai='{settings.openai_api_key}', anthropic='{settings.anthropic_api_key}', scrapingdog='{settings.scrapingdog_api_key}'")
        
                         
        saved_openai = False
        saved_anthropic = False
        saved_scrapingdog = False

        if 'openai_api_key' in data:
            val = data['openai_api_key'] or ''
            print(f"DEBUG: Processing openai key: '{val}' (length: {len(val)})")
                                                                                      
            if not (set(val) == {'*'} and len(val) > 0):
                settings.openai_api_key = val
                saved_openai = bool(val)
                print(f"DEBUG: Saved openai key: {saved_openai}")
            else:
                print(f"DEBUG: Skipped openai key (masked)")
        if 'anthropic_api_key' in data:
            val = data['anthropic_api_key'] or ''
            print(f"DEBUG: Processing anthropic key: '{val}' (length: {len(val)})")
            if not (set(val) == {'*'} and len(val) > 0):
                settings.anthropic_api_key = val
                saved_anthropic = bool(val)
                print(f"DEBUG: Saved anthropic key: {saved_anthropic}")
            else:
                print(f"DEBUG: Skipped anthropic key (masked)")
        if 'scrapingdog_api_key' in data:
            val = data['scrapingdog_api_key'] or ''
            print(f"DEBUG: Processing scrapingdog key: '{val}' (length: {len(val)})")
            if not (set(val) == {'*'} and len(val) > 0):
                settings.scrapingdog_api_key = val
                saved_scrapingdog = bool(val)
                print(f"DEBUG: Saved scrapingdog key: {saved_scrapingdog}")
            else:
                print(f"DEBUG: Skipped scrapingdog key (masked)")
        
        print(f"DEBUG: Settings before save: openai='{settings.openai_api_key}', anthropic='{settings.anthropic_api_key}', scrapingdog='{settings.scrapingdog_api_key}'")
        
                       
        result = settings.save()
        print(f"DEBUG: Save result: {result}")
        
        print(f"DEBUG: Settings after save: openai='{settings.openai_api_key}', anthropic='{settings.anthropic_api_key}', scrapingdog='{settings.scrapingdog_api_key}'")
        
        return jsonify({
            'success': True,
            'message': 'API keys updated successfully',
            'openai_masked': _mask_key_for_display(settings.openai_api_key),
            'anthropic_masked': _mask_key_for_display(settings.anthropic_api_key),
            'scrapingdog_masked': _mask_key_for_display(settings.scrapingdog_api_key),
            'saved_openai': saved_openai,
            'saved_anthropic': saved_anthropic,
            'saved_scrapingdog': saved_scrapingdog
        })
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/force-clean', methods=['POST'])
def api_force_clean():
    """Force clean RSS sources and save"""
    try:
        success = Settings.force_clean_and_save('default')
        if success:
            return jsonify({
                'success': True,
                'message': 'RSS sources cleaned and saved successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clean RSS sources'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/clean-api-keys', methods=['POST'])
def api_clean_api_keys():
    """Clean corrupted API keys and reset them"""
    try:
        settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
        
                                  
        if settings.openai_api_key and len(settings.openai_api_key) > 100:                       
            settings.openai_api_key = ""
        if settings.anthropic_api_key and len(settings.anthropic_api_key) > 100:                       
            settings.anthropic_api_key = ""
        if settings.scrapingdog_api_key and len(settings.scrapingdog_api_key) > 100:                       
            settings.scrapingdog_api_key = ""
        
                               
        settings.save()
        
        return jsonify({
            'success': True,
            'message': 'API keys cleaned successfully!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/api-keys', methods=['GET'])
def api_get_api_keys():
    """Return masked API keys presence for UI display."""
    settings = Settings.find_by_user_id('default') or Settings.get_default_settings()
    return jsonify({
        'openai_masked': _mask_key_for_display(settings.openai_api_key),
        'anthropic_masked': _mask_key_for_display(settings.anthropic_api_key),
        'scrapingdog_masked': _mask_key_for_display(settings.scrapingdog_api_key)
    })

@settings_bp.route('/api/config')
def api_config():
    """Get configuration info"""
    return jsonify({
        'debug': current_app.config.get('DEBUG', False),
        'environment': current_app.config.get('ENV', 'production')
    })
