from django.core.management.base import BaseCommand
from football.models import Team, Game
import requests
import json
from datetime import datetime
import pytz
from django.db import transaction
import time

class Command(BaseCommand):
    help = 'Fix 2025 NFL schedule by importing clean data from ESPN API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing 2025 games before importing new schedule'
        )
        parser.add_argument(
            '--save-json',
            action='store_true',
            help='Save API response to JSON file for future reference'
        )

    def handle(self, *args, **options):
        if options['clear_existing']:
            # Clear existing 2025 schedule data
            deleted_count = Game.objects.filter(season=2025).count()
            Game.objects.filter(season=2025).delete()
            self.stdout.write(f'Deleted {deleted_count} existing 2025 games')

        # ESPN API endpoint for NFL schedule
        # Use 2025 season - ESPN typically has schedule data available
        espn_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        
        games_created = 0
        api_responses = []
        
        # Try to get schedule for different date ranges in 2025
        # NFL season typically runs September-January
        date_ranges = [
            "20250901-20251231",  # September to December 2025
            "20260101-20260201",  # January 2026 (playoffs)
        ]
        
        for date_range in date_ranges:
            try:
                self.stdout.write(f'Fetching schedule for date range: {date_range}')
                
                # Add parameters for date range
                params = {
                    'dates': date_range,
                    'seasontype': 2,  # Regular season (1=preseason, 2=regular, 3=postseason)
                    'limit': 1000
                }
                
                response = requests.get(espn_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                api_responses.append({
                    'date_range': date_range,
                    'response': data,
                    'fetched_at': datetime.now().isoformat()
                })
                
                # Process games from this response
                if 'events' in data:
                    games_in_range = self.process_espn_games(data['events'])
                    games_created += games_in_range
                    self.stdout.write(f'  Processed {games_in_range} games from {date_range}')
                else:
                    self.stdout.write(f'  No events found for {date_range}')
                
                # Rate limiting - be respectful to ESPN API
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(f'Error fetching data for {date_range}: {e}')
                continue
            except Exception as e:
                self.stdout.write(f'Error processing data for {date_range}: {e}')
                continue
        
        # Save API responses to JSON file if requested
        if options['save_json']:
            json_filename = f'/Users/ares/Documents/_web/guessingfootball/guessingfootball/guessingfootball/espn_2025_schedule_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            try:
                with open(json_filename, 'w') as f:
                    json.dump(api_responses, f, indent=2)
                self.stdout.write(f'Saved API responses to: {json_filename}')
            except Exception as e:
                self.stdout.write(f'Error saving JSON file: {e}')
        
        # Final validation
        total_2025_games = Game.objects.filter(season=2025).count()
        total_teams = Team.objects.count()
        weeks_with_games = Game.objects.filter(season=2025).values('week').distinct().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== ESPN API Import Complete ===\n'
                f'Games created this run: {games_created}\n'
                f'Total 2025 games in database: {total_2025_games}\n'
                f'Total teams: {total_teams}\n'
                f'Weeks with games: {weeks_with_games}\n'
                f'Expected regular season games: 272\n'
                f'Data completeness: {(total_2025_games/272)*100:.1f}%'
            )
        )
        
        # Basic validation
        self.validate_schedule()

    def process_espn_games(self, events):
        """Process games from ESPN API response"""
        games_created = 0
        
        with transaction.atomic():
            for event in events:
                try:
                    # Extract game information
                    game_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                    
                    # Get teams
                    competitions = event.get('competitions', [])
                    if not competitions:
                        continue
                    
                    competition = competitions[0]
                    competitors = competition.get('competitors', [])
                    
                    if len(competitors) != 2:
                        continue
                    
                    # Identify home and away teams
                    home_team_data = None
                    away_team_data = None
                    
                    for competitor in competitors:
                        if competitor.get('homeAway') == 'home':
                            home_team_data = competitor
                        elif competitor.get('homeAway') == 'away':
                            away_team_data = competitor
                    
                    if not home_team_data or not away_team_data:
                        continue
                    
                    # Get team abbreviations
                    home_abbr = home_team_data['team']['abbreviation']
                    away_abbr = away_team_data['team']['abbreviation']
                    
                    # Handle team name mapping (if needed)
                    home_abbr = self.map_team_abbreviation(home_abbr)
                    away_abbr = self.map_team_abbreviation(away_abbr)
                    
                    # Get or create teams
                    home_team, _ = Team.objects.get_or_create(
                        name=home_abbr,
                        defaults={
                            'full_name': home_team_data['team'].get('displayName', home_abbr),
                            'city': home_team_data['team'].get('location', ''),
                        }
                    )
                    away_team, _ = Team.objects.get_or_create(
                        name=away_abbr,
                        defaults={
                            'full_name': away_team_data['team'].get('displayName', away_abbr),
                            'city': away_team_data['team'].get('location', ''),
                        }
                    )
                    
                    # Get scores (if game is completed)
                    home_score = 0
                    away_score = 0
                    
                    if competition.get('status', {}).get('type', {}).get('completed', False):
                        home_score = int(home_team_data.get('score', 0))
                        away_score = int(away_team_data.get('score', 0))
                    
                    # Determine week number (ESPN should provide this)
                    week_number = event.get('week', {}).get('number', 1)
                    
                    # Create or update game
                    game, created = Game.objects.get_or_create(
                        home_team=home_team,
                        away_team=away_team,
                        season=2025,
                        week=week_number,
                        defaults={
                            'game_date': game_date,
                            'home_score': home_score,
                            'away_score': away_score,
                        }
                    )
                    
                    if created:
                        games_created += 1
                        self.stdout.write(f'  ✓ {away_abbr} @ {home_abbr} - Week {week_number} - {game_date.strftime("%m/%d/%Y")}')
                    else:
                        # Update existing game if needed
                        updated = False
                        if game.game_date != game_date:
                            game.game_date = game_date
                            updated = True
                        if game.home_score != home_score:
                            game.home_score = home_score
                            updated = True
                        if game.away_score != away_score:
                            game.away_score = away_score
                            updated = True
                        
                        if updated:
                            game.save()
                            self.stdout.write(f'  ↻ Updated {away_abbr} @ {home_abbr} - Week {week_number}')
                
                except Exception as e:
                    self.stdout.write(f'Error processing game: {e}')
                    continue
        
        return games_created

    def map_team_abbreviation(self, espn_abbr):
        """Map ESPN team abbreviations to our database abbreviations"""
        mapping = {
            'WSH': 'WAS',  # Washington Commanders
            'LV': 'LV',    # Las Vegas Raiders
            'LAR': 'LA',   # Los Angeles Rams
            # Add other mappings as needed
        }
        return mapping.get(espn_abbr, espn_abbr)

    def validate_schedule(self):
        """Basic validation of imported schedule"""
        self.stdout.write('\n=== Schedule Validation ===')
        
        # Check team game counts
        teams_with_issues = []
        all_teams = Team.objects.all()
        
        for team in all_teams:
            from django.db.models import Q
            game_count = Game.objects.filter(
                Q(home_team=team, season=2025) | Q(away_team=team, season=2025)
            ).count()
            
            if game_count != 17:  # Expected regular season games
                teams_with_issues.append(f'{team.name}: {game_count} games')
        
        if teams_with_issues:
            self.stdout.write('Teams with incorrect game counts:')
            for issue in teams_with_issues[:10]:  # Show first 10
                self.stdout.write(f'  - {issue}')
            if len(teams_with_issues) > 10:
                self.stdout.write(f'  ... and {len(teams_with_issues) - 10} more')
        else:
            self.stdout.write('✓ All teams have correct game counts')
        
        # Check for scheduling conflicts
        conflicts = 0
        for week in range(1, 19):
            week_games = Game.objects.filter(season=2025, week=week)
            teams_this_week = []
            
            for game in week_games:
                if game.home_team in teams_this_week or game.away_team in teams_this_week:
                    conflicts += 1
                teams_this_week.extend([game.home_team, game.away_team])
        
        if conflicts > 0:
            self.stdout.write(f'⚠ Found {conflicts} scheduling conflicts')
        else:
            self.stdout.write('✓ No scheduling conflicts detected')