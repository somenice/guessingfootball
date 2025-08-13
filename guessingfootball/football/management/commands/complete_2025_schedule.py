from django.core.management.base import BaseCommand
from football.models import Team, Game
from datetime import datetime, timedelta
import pytz

class Command(BaseCommand):
    help = 'Complete the 2025 NFL regular season schedule for weeks 3-18'

    def handle(self, *args, **options):
        # Get all NFL teams
        teams = list(Team.objects.all())
        team_names = [team.name for team in teams]
        
        self.stdout.write(f'Found {len(teams)} teams: {", ".join(team_names)}')
        
        # Create timezone object for Eastern Time
        eastern = pytz.timezone('US/Eastern')
        
        # Season starts September 4, 2025
        season_start = datetime(2025, 9, 4, tzinfo=pytz.UTC)
        
        games_created = 0
        
        # Create remaining weeks 3-18
        for week_num in range(3, 19):
            week_start = season_start + timedelta(weeks=week_num-1)
            
            self.stdout.write(f'Creating Week {week_num} games...')
            
            # Calculate the Thursday of this week
            thursday = week_start + timedelta(days=(3 - week_start.weekday()) % 7)
            if thursday < week_start:
                thursday += timedelta(days=7)
            
            # Create a reasonable number of games for each week (13-16 games typical)
            # We'll create matchups by rotating through teams
            
            # Thursday Night Football (8:15 PM ET)
            if week_num >= 3:  # TNF typically starts week 2/3
                tnf_time = thursday.replace(hour=0, minute=15) + timedelta(hours=20, minutes=15)  # 8:15 PM ET
                
                # Pick two teams for Thursday night
                if len(teams) >= 2:
                    away_team = teams[(week_num * 2 - 1) % len(teams)]
                    home_team = teams[(week_num * 2) % len(teams)]
                    
                    if away_team != home_team:
                        game, created = Game.objects.get_or_create(
                            home_team=home_team,
                            away_team=away_team,
                            season=2025,
                            week=week_num,
                            defaults={
                                'game_date': tnf_time,
                                'home_score': 0,
                                'away_score': 0,
                            }
                        )
                        if created:
                            games_created += 1
                            et_time = tnf_time.astimezone(eastern)
                            self.stdout.write(f'  ✓ TNF: {away_team.name} @ {home_team.name} - {et_time.strftime("%A %I:%M %p ET")}')
            
            # Sunday games
            sunday = thursday + timedelta(days=3)
            
            # Early Sunday games (1:00 PM ET)
            early_sunday = sunday.replace(hour=18, minute=0)  # 1:00 PM ET = 18:00 UTC
            
            # Create 8-10 early Sunday games
            for game_idx in range(8):
                team_offset = (week_num * 16 + game_idx * 2) % len(teams)
                away_team = teams[team_offset]
                home_team = teams[(team_offset + 1) % len(teams)]
                
                if away_team != home_team:
                    # Check if this matchup already exists for this week
                    existing = Game.objects.filter(
                        season=2025, 
                        week=week_num,
                        home_team=home_team,
                        away_team=away_team
                    ).exists()
                    
                    if not existing:
                        game, created = Game.objects.get_or_create(
                            home_team=home_team,
                            away_team=away_team,
                            season=2025,
                            week=week_num,
                            defaults={
                                'game_date': early_sunday,
                                'home_score': 0,
                                'away_score': 0,
                            }
                        )
                        if created:
                            games_created += 1
            
            # Late Sunday games (4:05/4:25 PM ET)
            late_sunday_405 = sunday.replace(hour=21, minute=5)   # 4:05 PM ET
            late_sunday_425 = sunday.replace(hour=21, minute=25)  # 4:25 PM ET
            
            # Create 3-4 late Sunday games
            for game_idx in range(3):
                team_offset = (week_num * 16 + game_idx * 2 + 20) % len(teams)
                away_team = teams[team_offset]
                home_team = teams[(team_offset + 1) % len(teams)]
                
                if away_team != home_team:
                    game_time = late_sunday_425 if game_idx > 0 else late_sunday_405
                    
                    existing = Game.objects.filter(
                        season=2025, 
                        week=week_num,
                        home_team=home_team,
                        away_team=away_team
                    ).exists()
                    
                    if not existing:
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
            
            # Sunday Night Football (8:20 PM ET)
            snf_time = sunday.replace(hour=1, minute=20) + timedelta(days=1)  # 8:20 PM ET Sunday = 1:20 AM Monday UTC
            
            team_offset = (week_num * 7 + 30) % len(teams)
            away_team = teams[team_offset]
            home_team = teams[(team_offset + 3) % len(teams)]
            
            if away_team != home_team:
                existing = Game.objects.filter(
                    season=2025, 
                    week=week_num,
                    home_team=home_team,
                    away_team=away_team
                ).exists()
                
                if not existing:
                    game, created = Game.objects.get_or_create(
                        home_team=home_team,
                        away_team=away_team,
                        season=2025,
                        week=week_num,
                        defaults={
                            'game_date': snf_time,
                            'home_score': 0,
                            'away_score': 0,
                        }
                    )
                    if created:
                        games_created += 1
                        et_time = snf_time.astimezone(eastern)
                        self.stdout.write(f'  ✓ SNF: {away_team.name} @ {home_team.name} - {et_time.strftime("%A %I:%M %p ET")}')
            
            # Monday Night Football (8:15 PM ET) - not every week
            if week_num <= 17:  # MNF typically runs through Week 17
                monday = sunday + timedelta(days=1)
                mnf_time = monday.replace(hour=1, minute=15) + timedelta(days=1)  # 8:15 PM Monday = 1:15 AM Tuesday UTC
                
                team_offset = (week_num * 11 + 40) % len(teams)
                away_team = teams[team_offset]
                home_team = teams[(team_offset + 5) % len(teams)]
                
                if away_team != home_team:
                    existing = Game.objects.filter(
                        season=2025, 
                        week=week_num,
                        home_team=home_team,
                        away_team=away_team
                    ).exists()
                    
                    if not existing:
                        game, created = Game.objects.get_or_create(
                            home_team=home_team,
                            away_team=away_team,
                            season=2025,
                            week=week_num,
                            defaults={
                                'game_date': mnf_time,
                                'home_score': 0,
                                'away_score': 0,
                            }
                        )
                        if created:
                            games_created += 1
                            et_time = mnf_time.astimezone(eastern)
                            self.stdout.write(f'  ✓ MNF: {away_team.name} @ {home_team.name} - {et_time.strftime("%A %I:%M %p ET")}')
            
            # Count games created for this week
            week_games = Game.objects.filter(season=2025, week=week_num).count()
            self.stdout.write(f'  Week {week_num}: {week_games} total games')
        
        # Final summary
        total_2025_games = Game.objects.filter(season=2025).count()
        weeks_with_games = Game.objects.filter(season=2025).values('week').distinct().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted 2025 NFL Regular Season:\n'
                f'- New games created: {games_created}\n'
                f'- Total 2025 games: {total_2025_games}\n'
                f'- Weeks with games: {weeks_with_games}/18\n'
                f'- Schedule spans: September 4, 2025 - January 5, 2026'
            )
        )