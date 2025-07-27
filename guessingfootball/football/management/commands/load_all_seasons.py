from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime, timedelta
import sys
import os

class Command(BaseCommand):
    help = 'Load all NFL season data from results.py (2011-2019)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading'
        )

    def handle(self, *args, **options):
        # Import the results data
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        from results import (
            results2019, results2018, results2017, results2016, results2015,
            results2014, results2013, results2012, results2011
        )
        
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Game.objects.all().delete()
            Team.objects.all().delete()
            self.stdout.write('Data cleared.')
        
        # Map of season data to year
        seasons_data = {
            2019: results2019,
            2018: results2018,
            2017: results2017,
            2016: results2016,
            2015: results2015,
            2014: results2014,
            2013: results2013,
            2012: results2012,
            2011: results2011,
        }
        
        total_teams_created = 0
        total_games_created = 0
        
        # Process each season
        for season_year in sorted(seasons_data.keys()):
            season_data = seasons_data[season_year]
            self.stdout.write(f'\nLoading {season_year} NFL season data...')
            
            games_this_season = 0
            
            # Process each week
            for week_num, week_games in enumerate(season_data, 1):
                self.stdout.write(f'  Processing {season_year} week {week_num}...')
                
                for game_data in week_games:
                    # Handle different data formats
                    if len(game_data) == 3:
                        # New format: [('TEAM1', score1), ('TEAM2', score2), (year, month, day, hour, minute, second)]
                        away_team_data, home_team_data, date_tuple = game_data
                        away_team_name, away_score = away_team_data
                        home_team_name, home_score = home_team_data
                        year, month, day, hour, minute, second = date_tuple
                        game_date = datetime(year, month, day, hour, minute, second)
                    elif len(game_data) == 2:
                        # Old format: [('TEAM1', score1), ('TEAM2', score2)]
                        away_team_data, home_team_data = game_data
                        away_team_name, away_score = away_team_data
                        home_team_name, home_score = home_team_data
                        # Use a default date for older seasons (week estimation)
                        # NFL season typically starts in September, account for month overflow
                        base_date = datetime(season_year, 9, 1, 13, 0, 0)
                        game_date = base_date + timedelta(days=(week_num - 1) * 7)
                    else:
                        self.stdout.write(f'    Skipping invalid game data: {game_data}')
                        continue
                    
                    # Create or get teams
                    away_team, created = Team.objects.get_or_create(name=away_team_name)
                    if created:
                        total_teams_created += 1
                        self.stdout.write(f'    Created team: {away_team_name}')
                    
                    home_team, created = Team.objects.get_or_create(name=home_team_name)
                    if created:
                        total_teams_created += 1
                        self.stdout.write(f'    Created team: {home_team_name}')
                    
                    game, created = Game.objects.get_or_create(
                        home_team=home_team,
                        away_team=away_team,
                        game_date=game_date,
                        defaults={
                            'home_score': home_score,
                            'away_score': away_score,
                            'week': week_num,
                            'season': season_year
                        }
                    )
                    
                    if created:
                        total_games_created += 1
                        games_this_season += 1
            
            self.stdout.write(f'  {season_year} season: {games_this_season} games loaded')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded all seasons:\n'
                f'- Teams: {total_teams_created} created\n'
                f'- Games: {total_games_created} created\n'
                f'- Seasons: 2011-2019 (9 seasons)\n'
                f'- Total teams in database: {Team.objects.count()}\n'
                f'- Total games in database: {Game.objects.count()}'
            )
        )