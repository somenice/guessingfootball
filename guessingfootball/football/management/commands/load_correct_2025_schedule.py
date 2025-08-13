from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime, timedelta
import pytz

class Command(BaseCommand):
    help = 'Load the correct 2025 NFL regular season schedule'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing 2025 games before creating new schedule'
        )

    def handle(self, *args, **options):
        if options['clear_existing']:
            deleted_count = Game.objects.filter(season=2025).count()
            Game.objects.filter(season=2025).delete()
            self.stdout.write(f'Deleted {deleted_count} existing 2025 games')
        
        # Create timezone object for Eastern Time
        eastern = pytz.timezone('US/Eastern')
        
        # Week 1 schedule - starting Thursday, September 4, 2025
        week1_games = [
            # Thursday Night Football - Week 1 Opener
            ('DAL', 'PHI', datetime(2025, 9, 4, 20, 20, tzinfo=pytz.UTC)),  # 5:20 PM ET = 9:20 PM UTC
            
            # Sunday, September 7, 2025 - Early games (1:00 PM ET)
            ('CIN', 'NE', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),   # 1:00 PM ET
            ('HOU', 'IND', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('JAX', 'MIA', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('CAR', 'NO', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('PIT', 'ATL', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('TEN', 'CHI', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('CLE', 'WSH', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            ('MIN', 'TB', datetime(2025, 9, 7, 18, 0, tzinfo=pytz.UTC)),
            
            # Sunday, September 7, 2025 - Late games (4:05/4:25 PM ET)
            ('GB', 'BUF', datetime(2025, 9, 7, 21, 5, tzinfo=pytz.UTC)),   # 4:05 PM ET
            ('ARI', 'SF', datetime(2025, 9, 7, 21, 25, tzinfo=pytz.UTC)),  # 4:25 PM ET
            ('LV', 'DEN', datetime(2025, 9, 7, 21, 25, tzinfo=pytz.UTC)),
            ('LA', 'SEA', datetime(2025, 9, 7, 21, 25, tzinfo=pytz.UTC)),
            ('KC', 'LAC', datetime(2025, 9, 7, 21, 25, tzinfo=pytz.UTC)),
            
            # Sunday Night Football
            ('DET', 'NYG', datetime(2025, 9, 8, 1, 20, tzinfo=pytz.UTC)),   # 8:20 PM ET
            
            # Monday Night Football
            ('NYJ', 'BAL', datetime(2025, 9, 9, 1, 15, tzinfo=pytz.UTC)),   # 8:15 PM ET
        ]
        
        # Week 2 schedule - starting Thursday, September 11, 2025
        week2_games = [
            # Thursday Night Football
            ('WSH', 'PHI', datetime(2025, 9, 11, 20, 15, tzinfo=pytz.UTC)), # 8:15 PM ET
            
            # Sunday, September 14, 2025 - Early games (1:00 PM ET)
            ('NO', 'DAL', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('BAL', 'LV', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('LAC', 'CAR', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('NYJ', 'TEN', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('GB', 'IND', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('SEA', 'NE', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('NYG', 'CLE', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            ('MIA', 'BUF', datetime(2025, 9, 14, 18, 0, tzinfo=pytz.UTC)),
            
            # Sunday, September 14, 2025 - Late games (4:05/4:25 PM ET)
            ('ARI', 'LA', datetime(2025, 9, 14, 21, 5, tzinfo=pytz.UTC)),
            ('TB', 'DET', datetime(2025, 9, 14, 21, 25, tzinfo=pytz.UTC)),
            ('SF', 'MIN', datetime(2025, 9, 14, 21, 25, tzinfo=pytz.UTC)),
            ('KC', 'CIN', datetime(2025, 9, 14, 21, 25, tzinfo=pytz.UTC)),
            
            # Sunday Night Football
            ('JAX', 'HOU', datetime(2025, 9, 15, 1, 20, tzinfo=pytz.UTC)),
            
            # Monday Night Football
            ('DEN', 'PIT', datetime(2025, 9, 16, 1, 15, tzinfo=pytz.UTC)),
        ]
        
        all_weeks = {
            1: week1_games,
            2: week2_games,
        }
        
        games_created = 0
        
        for week_num, games in all_weeks.items():
            self.stdout.write(f'Creating Week {week_num} games...')
            
            for away_abbr, home_abbr, game_time in games:
                try:
                    # Get or create teams
                    away_team, created_away = Team.objects.get_or_create(name=away_abbr)
                    home_team, created_home = Team.objects.get_or_create(name=home_abbr)
                    
                    if created_away:
                        self.stdout.write(f'  Created team: {away_abbr}')
                    if created_home:
                        self.stdout.write(f'  Created team: {home_abbr}')
                    
                    # Create game
                    game, created = Game.objects.get_or_create(
                        home_team=home_team,
                        away_team=away_team,
                        season=2025,
                        week=week_num,
                        defaults={
                            'game_date': game_time,
                            'home_score': 0,
                            'away_score': 0,
                        }
                    )
                    
                    if created:
                        games_created += 1
                        # Convert to Eastern time for display
                        et_time = game_time.astimezone(eastern)
                        self.stdout.write(
                            f'  ✓ {away_abbr} @ {home_abbr} - {et_time.strftime("%A, %B %d at %I:%M %p ET")}'
                        )
                    else:
                        self.stdout.write(f'  Game already exists: {away_abbr} @ {home_abbr}')
                        
                except Exception as e:
                    self.stdout.write(f'  Error creating {away_abbr} @ {home_abbr}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created correct 2025 NFL schedule:\n'
                f'- Games created: {games_created}\n'
                f'- Week 1 opener: Dallas Cowboys @ Philadelphia Eagles\n'
                f'- Date: Thursday, September 4, 2025 at 8:20 PM ET\n'
                f'- Week 2 starts: Thursday, September 11, 2025'
            )
        )