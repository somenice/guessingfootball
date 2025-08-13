from datetime import datetime, timezone
from .models import Game

def get_live_games():
    """Get all currently live games with detailed status"""
    live_games = Game.get_live_games()
    
    live_game_data = []
    for game in live_games:
        game_info = {
            'game': game,
            'home_team': game.home_team,
            'away_team': game.away_team,
            'home_score': game.home_score,
            'away_score': game.away_score,
            'quarter': game.quarter_display,
            'time_remaining': game.time_remaining,
            'status': game.game_status,
            'is_live': game.is_live,
            'last_updated': game.last_updated,
        }
        live_game_data.append(game_info)
    
    return live_game_data

def check_live_games_exist():
    """Quick check if any games are currently live"""
    return Game.objects.filter(is_live=True).exists()

def get_current_week():
    """Determine current NFL week based on current date"""
    now = datetime.now()
    if now.month >= 9:  # September start
        return min(((now - datetime(now.year, 9, 1)).days // 7) + 1, 18)
    elif now.month <= 2:  # January/February  
        return min(((now - datetime(now.year - 1, 9, 1)).days // 7) + 1, 18)
    else:
        return 1  # Default to week 1