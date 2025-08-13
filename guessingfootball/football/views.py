from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F, Min, Max, Avg, Sum
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, Game
from .forms import CustomUserCreationForm, UserProfileForm
from .utils import get_live_games, check_live_games_exist

def teams_list(request):
    # Get teams that have games in the 2025 season and calculate their stats manually
    teams_with_2025_games = Team.objects.filter(
        Q(home_games__season=2025) | Q(away_games__season=2025)
    ).distinct()
    
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
    
    # Organize teams by conference and division
    # Define division order: North, East, South, West
    division_order = ['North', 'East', 'South', 'West']
    
    organized_teams = {
        'AFC': {},
        'NFC': {}
    }
    
    # Initialize divisions
    for conf in ['AFC', 'NFC']:
        for div in division_order:
            organized_teams[conf][div] = []
    
    # Sort teams into their divisions
    for team in teams_with_stats:
        if team.conference and team.division:
            if team.conference in organized_teams and team.division in organized_teams[team.conference]:
                organized_teams[team.conference][team.division].append(team)
    
    # Sort teams within each division by name
    for conf in organized_teams:
        for div in organized_teams[conf]:
            organized_teams[conf][div].sort(key=lambda t: t.name)
    
    # Get 2025 season stats
    total_2025_games = Game.objects.filter(season=2025).count()
    
    context = {
        'title': '2025 NFL Teams',
        'organized_teams': organized_teams,
        'division_order': division_order,
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
    
    # Calculate teams on bye week
    # Get all teams that have games this week
    teams_playing_this_week = set()
    for game in games:
        teams_playing_this_week.add(game.home_team)
        teams_playing_this_week.add(game.away_team)
    
    # Get all teams and find those not playing this week
    all_teams = Team.objects.filter(
        Q(home_games__season=2025) | Q(away_games__season=2025)
    ).distinct().order_by('name')
    
    bye_week_teams = []
    for team in all_teams:
        if team not in teams_playing_this_week:
            bye_week_teams.append(team)
    
    # Sort bye week teams by conference and division
    bye_week_teams.sort(key=lambda t: (t.conference or 'ZZZ', t.division or 'ZZZ', t.name))
    
    context = {
        'title': f'Week {week_number} - 2025 NFL Season',
        'week_number': week_number,
        'games': games,
        'total_games': total_games,
        'played_games': played_games,
        'bye_week_teams': bye_week_teams,
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

def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    # Only show regular season games (weeks 1-18)
    if game.week < 1 or game.week > 18:
        from django.http import Http404
        raise Http404("Only regular season games have detail pages")
    
    # Calculate team records and streaks leading up to this game
    away_team_stats = calculate_team_stats_before_game(game.away_team, game)
    home_team_stats = calculate_team_stats_before_game(game.home_team, game)
    
    # Get head-to-head record
    h2h_stats = calculate_head_to_head(game.away_team, game.home_team, before_date=game.game_date)
    
    # Check if game is completed
    is_completed = game.home_score > 0 or game.away_score > 0 or not game.is_live
    
    context = {
        'title': f'{game.away_team.name} @ {game.home_team.name} - Week {game.week}',
        'game': game,
        'away_team_stats': away_team_stats,
        'home_team_stats': home_team_stats,
        'h2h_stats': h2h_stats,
        'is_completed': is_completed,
        'season': game.season
    }
    
    return render(request, 'game_detail.jinja', context)

def calculate_team_stats_before_game(team, current_game):
    """Calculate team statistics before the current game"""
    # Get all games for this team in the same season before current game
    team_games = Game.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        season=current_game.season,
        game_date__lt=current_game.game_date
    ).exclude(home_score=0, away_score=0).order_by('game_date')
    
    wins = losses = ties = 0
    points_for = points_against = 0
    
    for game in team_games:
        if game.home_team == team:
            team_score = game.home_score
            opponent_score = game.away_score
        else:
            team_score = game.away_score  
            opponent_score = game.home_score
            
        points_for += team_score
        points_against += opponent_score
        
        if team_score > opponent_score:
            wins += 1
        elif team_score < opponent_score:
            losses += 1
        else:
            ties += 1
    
    total_games = wins + losses + ties
    win_pct = (wins + ties * 0.5) / total_games if total_games > 0 else 0
    
    return {
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'win_percentage': win_pct,
        'points_for': points_for,
        'points_against': points_against,
        'games_played': total_games
    }

def calculate_head_to_head(away_team, home_team, before_date=None):
    """Calculate head-to-head record between two teams"""
    h2h_games = Game.objects.filter(
        Q(home_team=home_team, away_team=away_team) |
        Q(home_team=away_team, away_team=home_team)
    )
    
    if before_date:
        h2h_games = h2h_games.filter(game_date__lt=before_date)
    
    h2h_games = h2h_games.exclude(home_score=0, away_score=0).order_by('-game_date')
    
    away_wins = home_wins = ties = 0
    
    for game in h2h_games:
        if game.home_team == home_team:
            # Home team is current home team
            if game.home_score > game.away_score:
                home_wins += 1
            elif game.home_score < game.away_score:
                away_wins += 1
            else:
                ties += 1
        else:
            # Away team is current home team (teams switched positions)
            if game.away_score > game.home_score:
                home_wins += 1
            elif game.away_score < game.home_score:
                away_wins += 1
            else:
                ties += 1
    
    return {
        'away_wins': away_wins,
        'home_wins': home_wins,
        'ties': ties,
        'recent_games': h2h_games[:5]  # Last 5 games
    }

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')
