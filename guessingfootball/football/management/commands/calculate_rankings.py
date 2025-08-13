from django.core.management.base import BaseCommand
from football.models import Team

class Command(BaseCommand):
    help = 'Calculate 2024 season rankings for all teams'

    def handle(self, *args, **options):
        self.stdout.write('Calculating 2024 season rankings...')
        
        try:
            teams_updated = Team.calculate_2024_rankings()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully calculated rankings for {teams_updated} teams.'
                )
            )
            
            # Show top 5 and bottom 5
            self.stdout.write('\nTop 5 teams:')
            top_teams = Team.objects.filter(rank_2024_league__isnull=False).order_by('rank_2024_league')[:5]
            for team in top_teams:
                self.stdout.write(
                    f'  {team.rank_2024_league}. {team.name}: {team.wins_2024}-{team.losses_2024}-{team.ties_2024} '
                    f'({team.win_percentage_2024:.3f})'
                )
            
            self.stdout.write('\nBottom 5 teams:')
            bottom_teams = Team.objects.filter(rank_2024_league__isnull=False).order_by('-rank_2024_league')[:5]
            for team in bottom_teams:
                self.stdout.write(
                    f'  {team.rank_2024_league}. {team.name}: {team.wins_2024}-{team.losses_2024}-{team.ties_2024} '
                    f'({team.win_percentage_2024:.3f})'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error calculating rankings: {e}')
            )