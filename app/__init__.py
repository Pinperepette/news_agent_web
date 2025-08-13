"""
News Agent Web - Flask Application
A web-based news analysis platform with AI-powered critical analysis
"""

import os
from flask import Flask, render_template
from flask_pymongo import PyMongo
from dotenv import load_dotenv

                            
load_dotenv()

                       
mongo = PyMongo()

def create_app(config_name=None):
    """Application factory pattern for Flask"""
    
    app = Flask(__name__)
    
                   
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/news_agent_web')
    
                           
    mongo.init_app(app)
    
                             
    from app.utils.helpers import format_date, truncate_text, get_source_icon, get_credibility_color, get_verosimiglianza_color
    
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['truncate_text'] = truncate_text
    app.jinja_env.globals['get_source_icon'] = get_source_icon
    app.jinja_env.globals['get_credibility_color'] = get_credibility_color
    app.jinja_env.globals['get_verosimiglianza_color'] = get_verosimiglianza_color
    
                         
    from .blueprints.news import news_bp
    from .blueprints.analysis import analysis_bp
    from .blueprints.settings import settings_bp
    from .blueprints.mcp import mcp_bp
    
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(mcp_bp, url_prefix='/mcp')
    
                    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
                
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app
