from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime
import requests
import json
import time
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load missing 2024 NFL regular season data from ESPN API week by week'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without actually loading data'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Team abbreviation mapping to handle changes
        team_mapping = {
            'LV': 'LV',   # Las Vegas Raiders (2020+)
            'OAK': 'LV',  # Oakland Raiders -> Las Vegas Raiders
            'LAR': 'LA',  # Los Angeles Rams
            'LAC': 'LAC', # Los Angeles Chargers  
            'WAS': 'WAS', # Washington (was WSH in some sources)
        }
        
        # Find teams with missing 2024 games
        teams_with_incomplete_data = []
        all_teams = Team.objects.all()
        
        for team in all_teams:
            games_2024 = Game.objects.filter(
                Q(home_team=team, season=2024) | Q(away_team=team, season=2024)
            )
            if games_2024.count() < 17:  # Normal season is 17 games
                existing_weeks = set(games_2024.values_list('week', flat=True))
                missing_weeks = set(range(1, 19)) - existing_weeks
                teams_with_incomplete_data.append((team.name, missing_weeks))
        
        if not teams_with_incomplete_data:
            self.stdout.write(self.style.SUCCESS('All teams have complete 2024 data'))
            return
        
        self.stdout.write(f'Found {len(teams_with_incomplete_data)} teams with incomplete 2024 data')
        
        # Get all unique missing weeks
        all_missing_weeks = set()
        for team_name, missing_weeks in teams_with_incomplete_data:
            all_missing_weeks.update(missing_weeks)
        
        self.stdout.write(f'Missing weeks across all teams: {sorted(all_missing_weeks)}')
        
        if dry_run:
            for team_name, missing_weeks in teams_with_incomplete_data:
                self.stdout.write(f'{team_name}: missing weeks {sorted(missing_weeks)}')
            return
        
        total_games_loaded = 0
        
        # Process each missing week
        for week in sorted(all_missing_weeks):
            self.stdout.write(f'\nProcessing Week {week} of 2024...')
            
            # Check if this week actually has any missing games
            teams_missing_this_week = [name for name, weeks in teams_with_incomplete_data if week in weeks]
            if not teams_missing_this_week:
                self.stdout.write(f'  No teams missing Week {week}, skipping')
                continue
                
            self.stdout.write(f'  Teams missing this week: {teams_missing_this_week}')
            
            # Construct API URL for this specific week
            url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2024&seasontype=2&week={week}'
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'events' not in data:
                    self.stdout.write(f'  No events found for Week {week}')
                    time.sleep(2)  # Be gentle on the API
                    continue
                
                games_this_week = 0
                
                for event in data['events']:
                    try:
                        # Skip Pro Bowl and other special events
                        event_name = event.get('name', '').lower()
                        if any(skip_term in event_name for skip_term in ['pro bowl', 'all-star', 'hall of fame']):
                            continue
                        
                        # Extract game information
                        game_date_str = event['date']
                        game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                        
                        # Extract competitors (teams and scores)
                        competition = event['competitions'][0]
                        competitors = competition['competitors']
                        
                        if len(competitors) != 2:
                            continue
                            
                        # Identify home and away teams
                        home_team_info = None
                        away_team_info = None
                        
                        for comp in competitors:
                            home_away = comp.get('homeAway', '')
                            if home_away == 'home':
                                home_team_info = comp
                            elif home_away == 'away':
                                away_team_info = comp
                        
                        # Fallback if homeAway not available
                        if not home_team_info or not away_team_info:
                            home_team_info = competitors[0]  # Usually home team is first
                            away_team_info = competitors[1]
                        
                        # Extract team data
                        home_team_abbr = home_team_info['team']['abbreviation']
                        away_team_abbr = away_team_info['team']['abbreviation']
                        
                        # Skip if teams are conference abbreviations or other invalid teams
                        invalid_teams = ['AFC', 'NFC', 'PRO', 'ALL']
                        if home_team_abbr in invalid_teams or away_team_abbr in invalid_teams:
                            continue
                        
                        # Apply team mapping
                        home_team_abbr = team_mapping.get(home_team_abbr, home_team_abbr)
                        away_team_abbr = team_mapping.get(away_team_abbr, away_team_abbr)
                        
                        home_score = int(home_team_info.get('score', 0))
                        away_score = int(away_team_info.get('score', 0))
                        
                        # Get teams (they should already exist)
                        try:
                            home_team = Team.objects.get(name=home_team_abbr)
                            away_team = Team.objects.get(name=away_team_abbr)
                        except Team.DoesNotExist as e:
                            self.stdout.write(f'  Warning: Team not found: {e}')
                            continue
                        
                        # Check if this game already exists
                        existing_game = Game.objects.filter(
                            home_team=home_team,
                            away_team=away_team,
                            week=week,
                            season=2024
                        ).first()
                        
                        if existing_game:
                            self.stdout.write(f'  Game already exists: {away_team_abbr} @ {home_team_abbr}')
                            continue
                        
                        # Create game
                        game = Game.objects.create(
                            home_team=home_team,
                            away_team=away_team,
                            game_date=game_date,
                            home_score=home_score,
                            away_score=away_score,
                            week=week,
                            season=2024
                        )
                        
                        total_games_loaded += 1
                        games_this_week += 1
                        self.stdout.write(f'  ✓ Loaded: {away_team_abbr} @ {home_team_abbr} ({away_score}-{home_score})')
                        
                    except Exception as e:
                        self.stdout.write(f'  Error processing game {event.get("id", "unknown")}: {str(e)}')
                        continue
                
                self.stdout.write(f'  Week {week}: {games_this_week} games loaded')
                
                # Delay between weeks to be respectful to the API
                time.sleep(3)
                
            except requests.RequestException as e:
                self.stdout.write(f'  Error fetching data for Week {week}: {str(e)}')
                time.sleep(5)  # Longer delay on error
                continue
            except Exception as e:
                self.stdout.write(f'  Error processing Week {week} data: {str(e)}')
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded missing 2024 data:\n'
                f'- Games loaded: {total_games_loaded}\n'
                f'- Total games in database: {Game.objects.count()}\n'
                f'- Total 2024 games: {Game.objects.filter(season=2024).count()}'
            )
        )