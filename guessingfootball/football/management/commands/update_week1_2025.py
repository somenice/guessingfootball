from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Update Week 1 2025 NFL games specifically'

    def handle(self, *args, **options):
        self.stdout.write('Updating Week 1 2025 NFL games...')
        
        # Clear existing Week 1 2025 games
        from football.models import Game
        Game.objects.filter(season=2025, week=1).delete()
        self.stdout.write('Cleared existing Week 1 2025 games.')
        
        # Load fresh Week 1 2025 data
        call_command('load_espn_data', 
                    start_year=2025, 
                    end_year=2025, 
                    week=1,
                    verbosity=2)
        
        # Show results
        week1_games = Game.objects.filter(season=2025, week=1)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated Week 1 2025: {week1_games.count()} games loaded'
            )
        )