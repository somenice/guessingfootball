from django.core.management.base import BaseCommand
from football.models import Team, Game
from django.db.models import Q
from django.core.cache import cache
import json

class Command(BaseCommand):
    help = 'Check data completeness for NFL seasons and cache results to avoid repeated API calls'

    def add_arguments(self, parser):
        parser.add_argument(
            '--season',
            type=int,
            default=2024,
            help='Season to check (default: 2024)'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force refresh of cached completeness data'
        )

    def handle(self, *args, **options):
        season = options['season']
        force_refresh = options['force_refresh']
        
        cache_key = f'data_completeness_{season}'
        
        # Check if we have cached results and use them unless forced to refresh
        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result:
                self.stdout.write(f'Using cached completeness data for {season}')
                self.display_results(cached_result, season)
                return
        
        self.stdout.write(f'Checking {season} season data completeness...')
        
        # Check all teams for season data completeness
        teams = Team.objects.all()
        complete_teams = []
        incomplete_teams = []
        
        total_games_in_season = Game.objects.filter(season=season).count()
        games_with_scores = Game.objects.filter(season=season).exclude(home_score=0, away_score=0).count()
        
        for team in teams:
            all_games = Game.objects.filter(
                Q(home_team=team, season=season) | Q(away_team=team, season=season)
            )
            
            total_games = all_games.count()
            games_with_scores_team = all_games.exclude(home_score=0, away_score=0).count()
            existing_weeks = set(all_games.values_list('week', flat=True))
            
            # For regular season, expect 17 games (18 weeks with 1 bye)
            expected_games = 17 if season >= 2021 else 16
            missing_weeks = set(range(1, 19)) - existing_weeks if season >= 2021 else set(range(1, 18)) - existing_weeks
            
            team_data = {
                'name': team.name,
                'total_games': total_games,
                'games_with_scores': games_with_scores_team,
                'existing_weeks': sorted(existing_weeks),
                'missing_weeks': sorted(missing_weeks),
                'is_complete': total_games >= expected_games and games_with_scores_team == total_games
            }
            
            if team_data['is_complete']:
                complete_teams.append(team_data)
            else:
                incomplete_teams.append(team_data)
        
        # Prepare results
        results = {
            'season': season,
            'total_teams': len(teams),
            'complete_teams': len(complete_teams),
            'incomplete_teams': len(incomplete_teams),
            'total_games_in_db': total_games_in_season,
            'games_with_scores': games_with_scores,
            'incomplete_team_details': incomplete_teams,
            'last_checked': str(cache.now() if hasattr(cache, 'now') else 'now')
        }
        
        # Cache the results for 1 hour to avoid repeated checks
        cache.set(cache_key, results, 3600)
        
        self.display_results(results, season)
    
    def display_results(self, results, season):
        """Display the completeness results"""
        self.stdout.write(f"\n{season} Season Data Completeness Report")
        self.stdout.write("=" * 50)
        
        self.stdout.write(f"Total Teams: {results['total_teams']}")
        self.stdout.write(f"Complete Teams: {results['complete_teams']}")
        self.stdout.write(f"Incomplete Teams: {results['incomplete_teams']}")
        self.stdout.write(f"Total Games in DB: {results['total_games_in_db']}")
        self.stdout.write(f"Games with Scores: {results['games_with_scores']}")
        
        if results['incomplete_teams'] > 0:
            self.stdout.write(f"\nIncomplete Teams ({results['incomplete_teams']}):")
            self.stdout.write("-" * 30)
            
            for team in results['incomplete_team_details']:
                missing_desc = f"missing weeks {team['missing_weeks']}" if team['missing_weeks'] else "all weeks present"
                self.stdout.write(
                    f"{team['name']}: {team['games_with_scores']}/{team['total_games']} games, {missing_desc}"
                )
                
            # Suggest which weeks need to be fetched
            all_missing_weeks = set()
            for team in results['incomplete_team_details']:
                all_missing_weeks.update(team['missing_weeks'])
            
            if all_missing_weeks:
                self.stdout.write(f"\nWeeks that need data fetching: {sorted(all_missing_weeks)}")
                self.stdout.write("Run: python manage.py load_missing_2024 to fetch missing data")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✓ All teams have complete {season} data!"))
        
        if 'last_checked' in results:
            self.stdout.write(f"\nLast checked: {results['last_checked']}")
            self.stdout.write("Use --force-refresh to update this cache")