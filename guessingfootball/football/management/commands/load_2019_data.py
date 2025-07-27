from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime
import sys
import os

class Command(BaseCommand):
    help = 'Load 2019 NFL season data from results.py'

    def handle(self, *args, **options):
        # Import the results data
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        from results import results2019
        
        self.stdout.write('Loading 2019 NFL season data...')
        
        teams_created = 0
        games_created = 0
        
        # Process each week
        for week_num, week_games in enumerate(results2019, 1):
            self.stdout.write(f'Processing week {week_num}...')
            
            for game_data in week_games:
                # Parse game data: [('TEAM1', score1), ('TEAM2', score2), (year, month, day, hour, minute, second)]
                away_team_data, home_team_data, date_tuple = game_data
                
                away_team_name, away_score = away_team_data
                home_team_name, home_score = home_team_data
                year, month, day, hour, minute, second = date_tuple
                
                # Create or get teams
                away_team, created = Team.objects.get_or_create(name=away_team_name)
                if created:
                    teams_created += 1
                    self.stdout.write(f'Created team: {away_team_name}')
                
                home_team, created = Team.objects.get_or_create(name=home_team_name)
                if created:
                    teams_created += 1
                    self.stdout.write(f'Created team: {home_team_name}')
                
                # Create game
                game_date = datetime(year, month, day, hour, minute, second)
                
                game, created = Game.objects.get_or_create(
                    home_team=home_team,
                    away_team=away_team,
                    game_date=game_date,
                    defaults={
                        'home_score': home_score,
                        'away_score': away_score,
                        'week': week_num,
                        'season': 2019
                    }
                )
                
                if created:
                    games_created += 1
                    self.stdout.write(f'Created game: {away_team_name} @ {home_team_name} ({away_score}-{home_score})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {teams_created} teams and {games_created} games for 2019 season'
            )
        )