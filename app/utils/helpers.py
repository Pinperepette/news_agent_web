"""
Helper functions for News Agent Web
"""

from datetime import datetime
from typing import Optional

def format_date(date_obj: Optional[datetime], format_str: str = "%d/%m/%Y %H:%M") -> str:
    """Format date object to string"""
    if not date_obj:
        return "N/A"
    
    try:
        return date_obj.strftime(format_str)
    except:
        return "N/A"

def truncate_text(text: str, max_length: int = 150, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_source_icon(source: str) -> str:
    """Get icon for news source"""
    source_icons = {
        'ANSA': '🇮🇹',
        'La Repubblica': '📰',
        'Corriere della Sera': '📰',
        'Il Sole 24 Ore': '💰',
        'Reuters': '🌍',
        'BBC News': '🇬🇧',
        'CNN': '🇺🇸',
        'The New York Times': '🇺🇸',
        'The Guardian': '🇬🇧',
        'Le Monde': '🇫🇷',
        'Der Spiegel': '🇩🇪'
    }
    
    return source_icons.get(source, '📰')

def get_credibility_color(score: int) -> str:
    """Get color class for credibility score"""
    if score >= 8:
        return 'text-success'
    elif score >= 6:
        return 'text-warning'
    elif score >= 4:
        return 'text-info'
    else:
        return 'text-danger'

def get_verosimiglianza_color(verosimiglianza: str) -> str:
    """Get color class for verosimiglianza"""
    colors = {
        'alta': 'text-success',
        'media': 'text-warning',
        'bassa': 'text-danger'
    }
    return colors.get(verosimiglianza.lower(), 'text-secondary')
