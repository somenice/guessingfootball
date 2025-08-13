from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Team, Game
import requests
import json
from datetime import datetime, timezone

class GameAdmin(admin.ModelAdmin):
    list_display = ['away_team', 'home_team', 'away_score', 'home_score', 'week', 'season', 'is_live', 'game_date']
    list_filter = ['season', 'week', 'is_live']
    search_fields = ['home_team__name', 'away_team__name']
    ordering = ['-game_date']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch-espn-data/', self.fetch_espn_data, name='fetch_espn_data'),
        ]
        return custom_urls + urls
        
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_fetch_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def fetch_espn_data(self, request):
        """Fetch current ESPN API data and update database"""
        if request.method == 'POST':
            try:
                # Use the current preseason endpoint
                url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=1"
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                games_updated = 0
                live_games_found = 0
                
                if 'events' in data:
                    for event in data['events']:
                        result = self.process_game_event(event)
                        if result:
                            games_updated += 1
                            if result['is_live']:
                                live_games_found += 1
                
                messages.success(
                    request, 
                    f'Successfully updated {games_updated} games from ESPN API. '
                    f'Found {live_games_found} live games.'
                )
                
            except requests.RequestException as e:
                messages.error(request, f'Error fetching ESPN API: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error processing data: {str(e)}')
                
            return redirect('admin:football_game_changelist')
        
        # GET request - show confirmation page
        return render(request, 'admin/football/game/fetch_espn_confirm.html')
    
    def process_game_event(self, event):
        """Process a single game event from ESPN API"""
        try:
            competitions = event.get('competitions', [])
            if not competitions:
                return None
                
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
                
            # Identify home and away teams
            home_competitor = next((c for c in competitors if c.get('homeAway') == 'home'), None)
            away_competitor = next((c for c in competitors if c.get('homeAway') == 'away'), None)
            
            if not home_competitor or not away_competitor:
                return None
                
            # Get team abbreviations and map them
            home_abbr = self.map_team_abbr(home_competitor['team']['abbreviation'])
            away_abbr = self.map_team_abbr(away_competitor['team']['abbreviation'])
            
            try:
                home_team = Team.objects.get(name=home_abbr)
                away_team = Team.objects.get(name=away_abbr)
            except Team.DoesNotExist as e:
                print(f'Team not found: {e}')
                return None
                
            # Extract scores
            home_score = int(home_competitor.get('score', 0))
            away_score = int(away_competitor.get('score', 0))
            
            # Extract game status
            status = competition.get('status', {})
            status_type = status.get('type', {})
            status_name = status_type.get('name', 'Unknown')
            status_description = status_type.get('description', '')
            
            # Check if game is live
            is_live = status_name in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']
            
            # Extract time and period info
            clock = status.get('displayClock', '')
            period = status.get('period', 0)
            
            # Get game date
            game_date_str = event.get('date')
            if game_date_str:
                game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
            else:
                game_date = datetime.now(timezone.utc)
            
            # Determine week and handle preseason properly
            week = competition.get('week', {}).get('number', 0)
            season = 2025  # Current season
            
            # For preseason games, use week 0 to distinguish from regular season
            if week is None or week == 1:
                # Check if it's actually a preseason game by looking at the date
                if game_date.month == 8 and game_date.day <= 15:  # Early August = preseason
                    week = 0
                
            # Get or create game
            game, created = Game.objects.get_or_create(
                home_team=home_team,
                away_team=away_team,
                season=season,
                week=week,
                defaults={
                    'game_date': game_date,
                    'home_score': home_score,
                    'away_score': away_score,
                    'is_live': is_live,
                    'game_status': status_description,
                    'current_quarter': period if is_live else None,
                    'time_remaining': clock if is_live else '',
                }
            )
            
            # Update existing game
            if not created:
                game.home_score = home_score
                game.away_score = away_score
                game.is_live = is_live
                game.game_status = status_description
                game.current_quarter = period if is_live else None
                game.time_remaining = clock if is_live else ''
                game.game_date = game_date
                game.save()
            
            return {
                'home_team': home_team.name,
                'away_team': away_team.name,
                'home_score': home_score,
                'away_score': away_score,
                'is_live': is_live,
                'status': status_description,
                'quarter': period,
                'clock': clock,
                'created': created
            }
            
        except Exception as e:
            print(f'Error processing game event: {e}')
            return None
    
    def map_team_abbr(self, abbr):
        """Map ESPN team abbreviations to our database"""
        mapping = {
            'WSH': 'WAS',
            'LAR': 'LA',
        }
        return mapping.get(abbr, abbr)

class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'full_name', 'city', 'conference', 'division', 'rank_2024_league', 'rank_2024_offense_league', 'rank_2024_defense_league', 'wins_2024', 'losses_2024']
    list_filter = ['conference', 'division']
    search_fields = ['name', 'full_name', 'city']
    ordering = ['name']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('calculate-rankings/', self.calculate_rankings, name='calculate_rankings'),
        ]
        return custom_urls + urls
        
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_rankings_button'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def calculate_rankings(self, request):
        """Calculate 2024 season rankings for all teams"""
        if request.method == 'POST':
            try:
                teams_updated = Team.calculate_2024_rankings()
                messages.success(
                    request, 
                    f'Successfully calculated 2024 season rankings for {teams_updated} teams.'
                )
            except Exception as e:
                messages.error(request, f'Error calculating rankings: {str(e)}')
                
            return redirect('admin:football_team_changelist')
        
        # GET request - show confirmation page
        return render(request, 'admin/football/team/calculate_rankings_confirm.html')

admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)
