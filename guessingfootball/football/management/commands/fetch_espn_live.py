from django.core.management.base import BaseCommand
from football.admin import GameAdmin
from football.models import Game
from django.contrib.admin.sites import AdminSite
import requests

class Command(BaseCommand):
    help = 'Fetch current ESPN preseason data (same as admin button)'

    def handle(self, *args, **options):
        # Create admin instance to use the same logic
        game_admin = GameAdmin(Game, AdminSite())
        
        self.stdout.write('Fetching ESPN preseason data...')
        
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=1"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            games_updated = 0
            live_games_found = 0
            
            if 'events' in data:
                for event in data['events']:
                    result = game_admin.process_game_event(event)
                    if result:
                        games_updated += 1
                        if result['is_live']:
                            live_games_found += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'LIVE: {result["away_team"]} {result["away_score"]} @ '
                                    f'{result["home_team"]} {result["home_score"]} - '
                                    f'Q{result["quarter"]} {result["clock"]}'
                                )
                            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {games_updated} games. Found {live_games_found} live games.'
                )
            )
            
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Error fetching ESPN API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing data: {e}'))