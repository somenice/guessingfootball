from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F, Min, Max, Avg, Sum
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, Game
from .forms import CustomUserCreationForm, UserProfileForm

def teams_list(request):
    # Get teams that have games in the 2025 season and calculate their stats manually
    teams_with_2025_games = Team.objects.filter(
        Q(home_games__season=2025) | Q(away_games__season=2025)
    ).distinct().order_by('name')
    
    # Calculate 2025 stats for each team manually
    teams_with_stats = []
    for team in teams_with_2025_games:
        home_games_2025 = team.home_games.filter(season=2025)
        away_games_2025 = team.away_games.filter(season=2025)
        
        total_scheduled_games_2025 = home_games_2025.count() + away_games_2025.count()
        wins_2025 = 0
        losses_2025 = 0
        ties_2025 = 0
        
        # Count home wins/losses/ties (exclude unplayed games with 0-0 score)
        for game in home_games_2025:
            # Skip unplayed games (both scores are 0)
            if game.home_score == 0 and game.away_score == 0:
                continue
            
            if game.home_score > game.away_score:
                wins_2025 += 1
            elif game.home_score < game.away_score:
                losses_2025 += 1
            else:
                ties_2025 += 1
        
        # Count away wins/losses/ties (exclude unplayed games with 0-0 score)
        for game in away_games_2025:
            # Skip unplayed games (both scores are 0)
            if game.home_score == 0 and game.away_score == 0:
                continue
                
            if game.away_score > game.home_score:
                wins_2025 += 1
            elif game.away_score < game.home_score:
                losses_2025 += 1
            else:
                ties_2025 += 1
        
        # Calculate played games (only games with actual results)
        played_games_2025 = wins_2025 + losses_2025 + ties_2025
        
        # Add calculated stats to team object
        team.total_games_2025 = played_games_2025  # Show played games, not scheduled
        team.total_scheduled_games_2025 = total_scheduled_games_2025  # Keep scheduled for reference
        team.wins_2025 = wins_2025
        team.losses_2025 = losses_2025
        team.ties_2025 = ties_2025
        teams_with_stats.append(team)
    
    # Get 2025 season stats
    total_2025_games = Game.objects.filter(season=2025).count()
    
    context = {
        'title': '2025 NFL Teams',
        'teams': teams_with_stats,
        'total_teams': len(teams_with_stats),
        'total_2025_games': total_2025_games,
        'season': 2025
    }
    return render(request, 'teams.jinja', context)

def team_detail(request, team_abbr):
    team = get_object_or_404(Team, name=team_abbr.upper())
    
    # Get only 2025 season games for this team
    home_games_2025 = team.home_games.filter(season=2025)
    away_games_2025 = team.away_games.filter(season=2025)
    
    # Combine games using Q objects instead of UNION to avoid ORDER BY issues
    all_games_2025 = Game.objects.filter(
        Q(home_team=team, season=2025) | Q(away_team=team, season=2025)
    ).order_by('-game_date')
    
    # Calculate 2025 team statistics
    total_games_2025 = all_games_2025.count()
    
    # Calculate wins, losses, ties for 2025
    wins_2025 = 0
    losses_2025 = 0
    ties_2025 = 0
    points_for_2025 = 0
    points_against_2025 = 0
    
    for game in all_games_2025:
        # Skip unplayed games (both scores are 0) for record calculation
        if game.home_score == 0 and game.away_score == 0:
            continue
            
        if game.home_team == team:
            # Team played at home
            team_score = game.home_score
            opponent_score = game.away_score
            points_for_2025 += team_score
            points_against_2025 += opponent_score
        else:
            # Team played away
            team_score = game.away_score
            opponent_score = game.home_score
            points_for_2025 += team_score
            points_against_2025 += opponent_score
        
        if team_score > opponent_score:
            wins_2025 += 1
        elif team_score < opponent_score:
            losses_2025 += 1
        else:
            ties_2025 += 1
    
    # Calculate averages for 2025 (only based on played games)
    played_games_2025 = wins_2025 + losses_2025 + ties_2025
    avg_points_for_2025 = points_for_2025 / played_games_2025 if played_games_2025 > 0 else 0
    avg_points_against_2025 = points_against_2025 / played_games_2025 if played_games_2025 > 0 else 0
    win_percentage_2025 = wins_2025 / played_games_2025 if played_games_2025 > 0 else 0
    
    # Create week-by-week schedule including bye weeks
    # Get all 2025 games ordered by week
    games_by_week = {}
    for game in all_games_2025.order_by('week'):
        games_by_week[game.week] = game
    
    # Create complete 18-week schedule with bye weeks
    complete_schedule = []
    for week in range(1, 19):  # Weeks 1-18
        if week in games_by_week:
            # Team has a game this week
            complete_schedule.append({
                'week': week,
                'type': 'game',
                'game': games_by_week[week]
            })
        else:
            # Team has a bye week
            complete_schedule.append({
                'week': week,
                'type': 'bye',
                'game': None
            })
    
    # Calculate 2024 season statistics
    all_games_2024 = Game.objects.filter(
        Q(home_team=team, season=2024) | Q(away_team=team, season=2024)
    ).order_by('-game_date')
    
    # Calculate 2024 team statistics
    wins_2024 = 0
    losses_2024 = 0
    ties_2024 = 0
    points_for_2024 = 0
    points_against_2024 = 0
    
    for game in all_games_2024:
        # Skip unplayed games (both scores are 0) for record calculation
        if game.home_score == 0 and game.away_score == 0:
            continue
            
        if game.home_team == team:
            # Team played at home
            team_score = game.home_score
            opponent_score = game.away_score
            points_for_2024 += team_score
            points_against_2024 += opponent_score
        else:
            # Team played away
            team_score = game.away_score
            opponent_score = game.home_score
            points_for_2024 += team_score
            points_against_2024 += opponent_score
        
        if team_score > opponent_score:
            wins_2024 += 1
        elif team_score < opponent_score:
            losses_2024 += 1
        else:
            ties_2024 += 1
    
    # Calculate averages for 2024 (only based on played games)
    played_games_2024 = wins_2024 + losses_2024 + ties_2024
    avg_points_for_2024 = points_for_2024 / played_games_2024 if played_games_2024 > 0 else 0
    avg_points_against_2024 = points_against_2024 / played_games_2024 if played_games_2024 > 0 else 0
    win_percentage_2024 = wins_2024 / played_games_2024 if played_games_2024 > 0 else 0
    
    context = {
        'title': f'{team.name} - 2025 Season',
        'team': team,
        'total_games_2025': played_games_2025,  # Show played games, not all scheduled
        'total_scheduled_games_2025': total_games_2025,  # Keep scheduled count for reference
        'wins_2025': wins_2025,
        'losses_2025': losses_2025,
        'ties_2025': ties_2025,
        'win_percentage_2025': win_percentage_2025,
        'points_for_2025': points_for_2025,
        'points_against_2025': points_against_2025,
        'avg_points_for_2025': avg_points_for_2025,
        'avg_points_against_2025': avg_points_against_2025,
        'complete_schedule_2025': complete_schedule,
        'season': 2025,
        # 2024 season statistics
        'total_games_2024': played_games_2024,
        'wins_2024': wins_2024,
        'losses_2024': losses_2024,
        'ties_2024': ties_2024,
        'win_percentage_2024': win_percentage_2024,
        'points_for_2024': points_for_2024,
        'points_against_2024': points_against_2024,
        'avg_points_for_2024': avg_points_for_2024,
        'avg_points_against_2024': avg_points_against_2024,
        'games_2024': all_games_2024,
    }
    
    return render(request, 'team_detail.jinja', context)

def week_detail(request, week_number):
    # Get all games for the specified week in 2025 season
    games = Game.objects.filter(
        season=2025, 
        week=week_number
    ).exclude(
        # Exclude Hall of Fame game if it exists in this week
        away_team__name='LAC',
        home_team__name='DET',
        game_date__day=1,
        game_date__month=8
    ).order_by('game_date')
    
    # Check if week exists
    if not games.exists():
        # Check if week number is valid (1-18 for regular season + playoffs)
        if week_number < 1 or week_number > 22:
            from django.http import Http404
            raise Http404("Invalid week number")
    
    # Count total games scheduled vs played
    total_games = games.count()
    played_games = games.exclude(home_score=0, away_score=0).count()
    
    context = {
        'title': f'Week {week_number} - 2025 NFL Season',
        'week_number': week_number,
        'games': games,
        'total_games': total_games,
        'played_games': played_games,
        'season': 2025
    }
    
    return render(request, 'week_detail.jinja', context)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'title': 'Sign Up',
        'form': form
    }
    return render(request, 'registration/signup.jinja', context)

@login_required
def account(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('account')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'title': 'My Account',
        'form': form,
        'user': request.user
    }
    return render(request, 'registration/account.jinja', context)
