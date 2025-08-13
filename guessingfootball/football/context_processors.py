from datetime import datetime, timedelta
from .models import Game
import pytz

def current_week(request):
    """Add current NFL week to all template contexts"""
    def get_current_nfl_week():
        """Determine the current NFL week based on the current date"""
        now = datetime.now(pytz.UTC)
        
        # Get all regular season weeks with games in 2025 (exclude preseason week 0)
        weeks_with_games = Game.objects.filter(
            season=2025, 
            week__gte=1, 
            week__lte=18
        ).values_list('week', flat=True).distinct().order_by('week')
        
        # If no regular season games yet, default to Week 1
        if not weeks_with_games:
            return 1
        
        for week_num in weeks_with_games:
            # Get all games for this week
            week_games = Game.objects.filter(season=2025, week=week_num).order_by('game_date')
            
            if week_games.exists():
                # Get the last game of the week
                last_game = week_games.last()
                
                # Calculate Tuesday after the last game
                # Most NFL weeks end on Sunday/Monday night
                last_game_date = last_game.game_date
                
                # Find the next Tuesday after the last game
                days_until_tuesday = (1 - last_game_date.weekday() + 7) % 7  # 1 = Tuesday
                if days_until_tuesday == 0:  # If it's already Tuesday
                    days_until_tuesday = 7  # Go to next Tuesday
                
                week_transition = last_game_date + timedelta(days=days_until_tuesday)
                
                # If we haven't reached Tuesday after the last game, this is the current week
                if now < week_transition:
                    return week_num
        
        # If we're past all weeks, return the last week
        return weeks_with_games.last() if weeks_with_games else 1
    
    return {
        'current_nfl_week': get_current_nfl_week()
    }