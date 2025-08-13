from django.shortcuts import render
from datetime import datetime, timedelta
from football.models import Game
from football.utils import get_live_games, check_live_games_exist
import pytz

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

def home(request):
    # Get current NFL week
    current_week = get_current_nfl_week()
    
    # Get games for the current week (exclude Hall of Fame preseason games)
    current_week_games = Game.objects.filter(
        season=2025, 
        week=current_week
    ).exclude(
        away_team__name='LAC',
        home_team__name='DET',
        game_date__day=1,
        game_date__month=8
    ).order_by('game_date')
    
    # Count total and played games
    total_games = current_week_games.count()
    played_games = current_week_games.exclude(home_score=0, away_score=0).count()
    
    # Get live games
    live_games = get_live_games()
    has_live_games = check_live_games_exist()
    
    context = {
        'title': 'Home',
        'welcome_message': 'Welcome to Guessing Football - Your ultimate destination for NFL schedule and game predictions!',
        'features': [
            'NFL Schedule Tracking',
            'Game Prediction Analytics',
            'Statistical Analysis with PMF-based smoothing',
            'Data Visualization and Plotting',
            'Adaptive weighting algorithms',
            'Multi-season data (2011-2025)'
        ],
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current_week': current_week,
        'current_week_games': current_week_games,
        'total_games': total_games,
        'played_games': played_games,
        'live_games': live_games,
        'has_live_games': has_live_games
    }
    return render(request, 'home.jinja', context)

def terms_of_service(request):
    context = {
        'title': 'Terms of Service',
        'current_time': datetime.now().strftime('%B %d, %Y'),
    }
    return render(request, 'legal/terms.jinja', context)

def privacy_policy(request):
    context = {
        'title': 'Privacy Policy', 
        'current_time': datetime.now().strftime('%B %d, %Y'),
    }
    return render(request, 'legal/privacy.jinja', context)