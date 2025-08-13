import requests
import json
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from football.models import Team, Game

class Command(BaseCommand):
    help = 'Poll ESPN API for live game data and update current scores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            type=int,
            help='Specific week to check (default: current week)',
        )
        parser.add_argument(
            '--season',
            type=int,
            default=2025,
            help='Season year (default: 2025)',
        )
        parser.add_argument(
            '--seasontype',
            type=int,
            default=1,
            help='Season type: 1=preseason, 2=regular, 3=postseason (default: 1)',
        )

    def handle(self, *args, **options):
        season = options['season']
        week = options.get('week')
        seasontype = options['seasontype']
        
        # If no week specified, get current week based on today's date
        if not week:
            week = self.get_current_week()
        
        season_type_name = {1: 'preseason', 2: 'regular season', 3: 'postseason'}.get(seasontype, 'unknown')
        self.stdout.write(f'Polling ESPN API for Week {week} of {season} {season_type_name}...')
        
        # Poll ESPN API for the specified week and season type  
        if week:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={seasontype}&week={week}"
        else:
            # Get current live games without week specification
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype={seasontype}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            games_updated = 0
            live_games = []
            
            if 'events' in data:
                for event in data['events']:
                    game_data = self.process_game_event(event, season, week)
                    if game_data:
                        games_updated += 1
                        if game_data['is_live']:
                            live_games.append(game_data)
                            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {games_updated} games for Week {week}')
            )
            
            if live_games:
                self.stdout.write(self.style.WARNING(f'Found {len(live_games)} live games:'))
                for game in live_games:
                    self.stdout.write(f"  {game['away_team']} @ {game['home_team']} - {game['status']}")
            else:
                self.stdout.write('No live games found.')
                
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Error fetching data from ESPN API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing data: {e}'))

    def get_current_week(self):
        """Determine current NFL week based on current date"""
        # Simple logic - can be enhanced based on actual NFL schedule
        now = datetime.now()
        if now.month >= 9:  # September start
            return min(((now - datetime(now.year, 9, 1)).days // 7) + 1, 18)
        elif now.month <= 2:  # January/February
            return min(((now - datetime(now.year - 1, 9, 1)).days // 7) + 1, 18)
        else:
            return 1  # Default to week 1

    def process_game_event(self, event, season, week):
        """Process a single game event from ESPN API"""
        try:
            # Extract team information
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
                
            # Get team abbreviations
            home_abbr = home_competitor['team']['abbreviation']
            away_abbr = away_competitor['team']['abbreviation']
            
            # Map team abbreviations to our database
            home_team = self.get_team_by_abbr(home_abbr)
            away_team = self.get_team_by_abbr(away_abbr)
            
            if not home_team or not away_team:
                self.stdout.write(f'Warning: Could not find teams {home_abbr} or {away_abbr}')
                return None
                
            # Extract scores
            home_score = int(home_competitor.get('score', 0))
            away_score = int(away_competitor.get('score', 0))
            
            # Extract game status and time information
            status = competition.get('status', {})
            status_type = status.get('type', {})
            status_name = status_type.get('name', 'Unknown')
            status_description = status_type.get('description', '')
            
            # Check if game is live
            is_live = status_name in ['STATUS_IN_PROGRESS', 'STATUS_HALFTIME']
            
            # Extract detailed status information for live games
            clock = status.get('displayClock', '')
            period = status.get('period', 0)
            
            # Get or create game in database
            game_date_str = event.get('date')
            if game_date_str:
                game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
            else:
                game_date = datetime.now(timezone.utc)
                
            game, created = Game.objects.get_or_create(
                home_team=home_team,
                away_team=away_team,
                season=season,
                week=week,
                defaults={
                    'game_date': game_date,
                    'home_score': home_score,
                    'away_score': away_score,
                }
            )
            
            # Update game with current scores and status
            game.home_score = home_score
            game.away_score = away_score
            game.is_live = is_live
            game.game_status = status_description
            game.current_quarter = period if is_live else None
            game.time_remaining = clock if is_live else ''
            game.save()
            
            return {
                'home_team': home_team.name,
                'away_team': away_team.name,
                'home_score': home_score,
                'away_score': away_score,
                'is_live': is_live,
                'status': status_description,
                'clock': clock,
                'period': period,
                'quarter': self.get_quarter_display(period),
            }
            
        except Exception as e:
            self.stdout.write(f'Error processing game event: {e}')
            return None

    def get_team_by_abbr(self, abbr):
        """Map ESPN team abbreviation to our Team model"""
        # Handle common abbreviation differences
        abbr_mapping = {
            'WSH': 'WAS',  # Washington
            'LAR': 'LA',   # Los Angeles Rams
            'LV': 'LV',    # Las Vegas (already correct)
        }
        
        mapped_abbr = abbr_mapping.get(abbr, abbr)
        
        try:
            return Team.objects.get(name=mapped_abbr)
        except Team.DoesNotExist:
            return None

    def get_quarter_display(self, period):
        """Convert period number to quarter display"""
        if period == 1:
            return "1st Quarter"
        elif period == 2:
            return "2nd Quarter"
        elif period == 3:
            return "3rd Quarter"
        elif period == 4:
            return "4th Quarter"
        elif period > 4:
            return f"OT{period - 4 if period > 5 else ''}"
        else:
            return "Pre-Game"