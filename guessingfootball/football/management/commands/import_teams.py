from django.core.management.base import BaseCommand
from football.models import Team

class Command(BaseCommand):
    help = 'Import team data from teams.py with corrections'

    def handle(self, *args, **options):
        # Updated teams data with corrections
        teams_data = [
            {'id': 'BUF', 'city': 'Buffalo', 'lname': 'Bills', 'conf': 'AFC', 'div': 'East'},
            {'id': 'MIA', 'city': 'Miami', 'lname': 'Dolphins', 'conf': 'AFC', 'div': 'East'},
            {'id': 'NE', 'city': 'New England', 'lname': 'Patriots', 'conf': 'AFC', 'div': 'East'},
            {'id': 'NYJ', 'city': 'New York', 'lname': 'Jets', 'conf': 'AFC', 'div': 'East'},
            {'id': 'BAL', 'city': 'Baltimore', 'lname': 'Ravens', 'conf': 'AFC', 'div': 'North'},
            {'id': 'CIN', 'city': 'Cincinnati', 'lname': 'Bengals', 'conf': 'AFC', 'div': 'North'},
            {'id': 'CLE', 'city': 'Cleveland', 'lname': 'Browns', 'conf': 'AFC', 'div': 'North'},
            {'id': 'PIT', 'city': 'Pittsburgh', 'lname': 'Steelers', 'conf': 'AFC', 'div': 'North'},
            {'id': 'HOU', 'city': 'Houston', 'lname': 'Texans', 'conf': 'AFC', 'div': 'South'},
            {'id': 'IND', 'city': 'Indianapolis', 'lname': 'Colts', 'conf': 'AFC', 'div': 'South'},
            {'id': 'JAX', 'city': 'Jacksonville', 'lname': 'Jaguars', 'conf': 'AFC', 'div': 'South'},  # Corrected from JAC to JAX
            {'id': 'TEN', 'city': 'Tennessee', 'lname': 'Titans', 'conf': 'AFC', 'div': 'South'},
            {'id': 'DEN', 'city': 'Denver', 'lname': 'Broncos', 'conf': 'AFC', 'div': 'West'},
            {'id': 'KC', 'city': 'Kansas City', 'lname': 'Chiefs', 'conf': 'AFC', 'div': 'West'},
            {'id': 'LV', 'city': 'Las Vegas', 'lname': 'Raiders', 'conf': 'AFC', 'div': 'West'},
            {'id': 'LAC', 'city': 'Los Angeles', 'lname': 'Chargers', 'conf': 'AFC', 'div': 'West'},
            {'id': 'DAL', 'city': 'Dallas', 'lname': 'Cowboys', 'conf': 'NFC', 'div': 'East'},
            {'id': 'NYG', 'city': 'New York', 'lname': 'Giants', 'conf': 'NFC', 'div': 'East'},
            {'id': 'PHI', 'city': 'Philadelphia', 'lname': 'Eagles', 'conf': 'NFC', 'div': 'East'},
            {'id': 'WAS', 'city': 'Washington', 'lname': 'Commanders', 'conf': 'NFC', 'div': 'East'},  # Updated from Redskins to Commanders
            {'id': 'CHI', 'city': 'Chicago', 'lname': 'Bears', 'conf': 'NFC', 'div': 'North'},
            {'id': 'DET', 'city': 'Detroit', 'lname': 'Lions', 'conf': 'NFC', 'div': 'North'},
            {'id': 'GB', 'city': 'Green Bay', 'lname': 'Packers', 'conf': 'NFC', 'div': 'North'},
            {'id': 'MIN', 'city': 'Minnesota', 'lname': 'Vikings', 'conf': 'NFC', 'div': 'North'},
            {'id': 'ATL', 'city': 'Atlanta', 'lname': 'Falcons', 'conf': 'NFC', 'div': 'South'},
            {'id': 'CAR', 'city': 'Carolina', 'lname': 'Panthers', 'conf': 'NFC', 'div': 'South'},
            {'id': 'NO', 'city': 'New Orleans', 'lname': 'Saints', 'conf': 'NFC', 'div': 'South'},
            {'id': 'TB', 'city': 'Tampa Bay', 'lname': 'Buccaneers', 'conf': 'NFC', 'div': 'South'},
            {'id': 'ARI', 'city': 'Arizona', 'lname': 'Cardinals', 'conf': 'NFC', 'div': 'West'},
            {'id': 'SF', 'city': 'San Francisco', 'lname': '49ers', 'conf': 'NFC', 'div': 'West'},
            {'id': 'SEA', 'city': 'Seattle', 'lname': 'Seahawks', 'conf': 'NFC', 'div': 'West'},
            {'id': 'LA', 'city': 'Los Angeles', 'lname': 'Rams', 'conf': 'NFC', 'div': 'West'}
        ]
        
        updated_teams = 0
        created_teams = 0
        
        for team_data in teams_data:
            team_id = team_data['id']
            city = team_data['city']
            team_name = team_data['lname']
            conference = team_data['conf']
            division = team_data['div']
            full_name = f"{city} {team_name}"
            
            # Get or create team
            team, created = Team.objects.get_or_create(
                name=team_id,
                defaults={
                    'full_name': full_name,
                    'city': city,
                    'conference': conference,
                    'division': division
                }
            )
            
            if created:
                created_teams += 1
                self.stdout.write(f'  Created: {team_id} - {full_name}')
            else:
                # Update existing team with new information
                team.full_name = full_name
                team.city = city
                team.conference = conference
                team.division = division
                team.save()
                updated_teams += 1
                self.stdout.write(f'  Updated: {team_id} - {full_name}')
        
        # Handle deprecated team abbreviations
        deprecated_teams = ['JAC', 'WSH', 'OAK']  # JAC->JAX, WSH->WAS, OAK->LV
        for deprecated_id in deprecated_teams:
            try:
                deprecated_team = Team.objects.get(name=deprecated_id)
                # Check if this team has any games
                if deprecated_team.home_games.exists() or deprecated_team.away_games.exists():
                    self.stdout.write(f'  Warning: {deprecated_id} has games but is deprecated. Manual migration needed.')
                else:
                    deprecated_team.delete()
                    self.stdout.write(f'  Removed deprecated team: {deprecated_id}')
            except Team.DoesNotExist:
                pass
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTeam import completed:\n'
                f'- Teams created: {created_teams}\n'
                f'- Teams updated: {updated_teams}\n'
                f'- Total teams in database: {Team.objects.count()}'
            )
        )
        
        # Show summary by conference and division
        self.stdout.write('\nTeam summary by conference/division:')
        for conf in ['AFC', 'NFC']:
            self.stdout.write(f'\n{conf}:')
            for div in ['East', 'North', 'South', 'West']:
                teams_in_div = Team.objects.filter(conference=conf, division=div).order_by('name')
                team_names = [f"{team.name} ({team.city})" for team in teams_in_div]
                self.stdout.write(f'  {div}: {", ".join(team_names)}')