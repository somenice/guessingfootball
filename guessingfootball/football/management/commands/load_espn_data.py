from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime
import requests
import json
import time

class Command(BaseCommand):
    help = 'Load NFL season data from ESPN API (2020-2025)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-year',
            type=int,
            default=2020,
            help='Starting year to load data from (default: 2020)'
        )
        parser.add_argument(
            '--end-year',
            type=int,
            default=2025,
            help='Ending year to load data to (default: 2025)'
        )
        parser.add_argument(
            '--season-type',
            type=int,
            default=2,
            help='Season type: 2=Regular Season, 3=Post-Season (default: 2)'
        )
        parser.add_argument(
            '--week',
            type=int,
            help='Specific week to load (optional, loads all weeks if not specified)'
        )
        parser.add_argument(
            '--clear-new',
            action='store_true',
            help='Clear games from 2020 onwards before loading'
        )

    def handle(self, *args, **options):
        start_year = options['start_year']
        end_year = options['end_year']
        season_type = options['season_type']
        specific_week = options.get('week')
        
        if options['clear_new']:
            self.stdout.write('Clearing games from 2020 onwards...')
            Game.objects.filter(season__gte=2020).delete()
            self.stdout.write('Cleared existing 2020+ data.')
        
        # Team abbreviation mapping to handle changes
        team_mapping = {
            'LV': 'LV',   # Las Vegas Raiders (2020+)
            'OAK': 'LV',  # Oakland Raiders -> Las Vegas Raiders
            'LAR': 'LA',  # Los Angeles Rams
            'LAC': 'LAC', # Los Angeles Chargers  
            'WAS': 'WAS', # Washington (was WSH in some sources)
        }
        
        total_games_loaded = 0
        total_teams_created = 0
        
        for year in range(start_year, end_year + 1):
            self.stdout.write(f'\nLoading {year} NFL season data...')
            
            # Construct API URL
            url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype={season_type}'
            if specific_week:
                url += f'&week={specific_week}'
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'events' not in data:
                    self.stdout.write(f'No events found for {year}')
                    continue
                
                games_this_year = 0
                
                for event in data['events']:
                    try:
                        # Skip Pro Bowl and other special events
                        event_name = event.get('name', '').lower()
                        if any(skip_term in event_name for skip_term in ['pro bowl', 'all-star', 'hall of fame']):
                            continue
                        
                        # Extract game information
                        game_id = event['id']
                        game_date_str = event['date']
                        game_date = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
                        
                        # Get season info
                        season_info = event.get('season', {})
                        actual_season = season_info.get('year', year)
                        
                        # Extract week information if available
                        week = event.get('week', {}).get('number', 1)
                        
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
                        
                        # Create or get teams
                        home_team, created = Team.objects.get_or_create(name=home_team_abbr)
                        if created:
                            total_teams_created += 1
                            self.stdout.write(f'  Created team: {home_team_abbr}')
                        
                        away_team, created = Team.objects.get_or_create(name=away_team_abbr)
                        if created:
                            total_teams_created += 1
                            self.stdout.write(f'  Created team: {away_team_abbr}')
                        
                        # Create game
                        game, created = Game.objects.get_or_create(
                            home_team=home_team,
                            away_team=away_team,
                            game_date=game_date,
                            defaults={
                                'home_score': home_score,
                                'away_score': away_score,
                                'week': week,
                                'season': actual_season
                            }
                        )
                        
                        if created:
                            total_games_loaded += 1
                            games_this_year += 1
                            
                    except Exception as e:
                        self.stdout.write(f'  Error processing game {event.get("id", "unknown")}: {str(e)}')
                        continue
                
                self.stdout.write(f'  {year}: {games_this_year} games loaded')
                
                # Small delay between years to be respectful to the API
                time.sleep(1)
                
            except requests.RequestException as e:
                self.stdout.write(f'Error fetching data for {year}: {str(e)}')
                continue
            except Exception as e:
                self.stdout.write(f'Error processing {year} data: {str(e)}')
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully loaded ESPN data:\n'
                f'- Teams created: {total_teams_created}\n'
                f'- Games loaded: {total_games_loaded}\n'
                f'- Years processed: {start_year}-{end_year}\n'
                f'- Total teams in database: {Team.objects.count()}\n'
                f'- Total games in database: {Game.objects.count()}'
            )
        )