from django.shortcuts import render
from datetime import datetime
from football.models import Game

def home(request):
    # Get week 1 2025 matchups (exclude Hall of Fame preseason game)
    week1_2025_games = Game.objects.filter(
        season=2025, 
        week=1
    ).exclude(
        away_team__name='LAC',
        home_team__name='DET',
        game_date__day=1,
        game_date__month=8
    ).order_by('game_date')
    
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
        'week1_2025_games': week1_2025_games
    }
    return render(request, 'home.jinja', context)