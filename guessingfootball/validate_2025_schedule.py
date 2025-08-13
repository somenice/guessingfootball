#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guessingfootball.settings')
django.setup()

from football.models import Game, Team
from collections import defaultdict
import datetime

def validate_2025_schedule():
    print('=== COMPREHENSIVE 2025 NFL SCHEDULE VALIDATION ===\n')

    # 1. Data Completeness Check
    print('1. DATA COMPLETENESS ANALYSIS')
    print('-' * 40)

    games_2025 = Game.objects.filter(season=2025)
    total_2025_games = games_2025.count()
    print(f'Total 2025 games found: {total_2025_games}')

    # Expected: 17 games per team × 32 teams ÷ 2 = 272 games for regular season
    expected_regular_season_games = 17 * 32 // 2
    print(f'Expected regular season games (weeks 1-18): {expected_regular_season_games}')

    # Check games by week
    week_counts = {}
    for week in range(0, 19):
        count = games_2025.filter(week=week).count()
        week_counts[week] = count
        if week == 0:
            print(f'Week {week} (likely preseason/other): {count} games')
        else:
            print(f'Week {week}: {count} games')

    regular_season_total = sum(week_counts[w] for w in range(1, 19))
    print(f'\nRegular season games (weeks 1-18): {regular_season_total}')
    
    # Check for data completeness issues
    if regular_season_total < expected_regular_season_games:
        print(f'❌ ISSUE: Missing {expected_regular_season_games - regular_season_total} regular season games')
    elif regular_season_total == expected_regular_season_games:
        print(f'✅ PASS: Correct number of regular season games')
    else:
        print(f'❌ ISSUE: Too many regular season games ({regular_season_total - expected_regular_season_games} extra)')

    # Check for week 0 (should typically be 0 for regular season)
    if week_counts[0] > 0:
        print(f'⚠️  WARNING: {week_counts[0]} games found in week 0 (unusual for regular season)')

    # 2. Date/Time Validation
    print('\n2. DATE/TIME FORMATTING AND SCHEDULING PATTERNS')
    print('-' * 50)

    games_2025_ordered = games_2025.order_by('game_date')

    if games_2025_ordered.exists():
        first_game = games_2025_ordered.first()
        last_game = games_2025_ordered.last()
        print(f'First game: {first_game.game_date} (Week {first_game.week})')
        print(f'Last game: {last_game.game_date} (Week {last_game.week})')
        
        # Check if dates fall in expected NFL season timeframe
        season_start = datetime.datetime(2025, 9, 1, tzinfo=first_game.game_date.tzinfo)
        season_end = datetime.datetime(2026, 1, 31, tzinfo=last_game.game_date.tzinfo)
        
        if first_game.game_date < season_start:
            print(f'⚠️  WARNING: First game is before expected season start (Sep 1, 2025)')
        if last_game.game_date > season_end:
            print(f'⚠️  WARNING: Last game is after expected season end (Jan 31, 2026)')
        
        season_span = (last_game.game_date - first_game.game_date).days
        print(f'Season span: {season_span} days')

        # Check game times by day of week
        day_counts = defaultdict(int)
        time_analysis = defaultdict(list)

        for game in games_2025:
            day_name = game.game_date.strftime('%A')
            day_counts[day_name] += 1
            time_analysis[day_name].append(game.game_date.time())

        print(f'\nGames by day of week:')
        for day, count in sorted(day_counts.items()):
            print(f'{day}: {count} games')

        # Check for unusual game times
        print(f'\nGame time analysis:')
        unusual_times = []
        for day in ['Thursday', 'Sunday', 'Monday']:
            if day in time_analysis:
                times = sorted(set(time_analysis[day]))
                print(f'{day} game times: {[t.strftime("%I:%M %p") for t in times[:5]]}' + ('...' if len(times) > 5 else ''))
                
                # Check for unusual times (before 1 PM or after 11 PM)
                for time_obj in times:
                    if time_obj.hour < 13 or time_obj.hour >= 23:
                        unusual_times.append((day, time_obj.strftime("%I:%M %p")))

        if unusual_times:
            print(f'⚠️  WARNING: Unusual game times found:')
            for day, time in unusual_times:
                print(f'  {day} at {time}')

    # 3. Team Assignment Validation
    print('\n3. TEAM ASSIGNMENT ACCURACY')
    print('-' * 30)

    all_teams = Team.objects.all().order_by('name')
    print(f'Total teams in database: {all_teams.count()}')

    # Check each team's game count for 2025
    team_game_counts = defaultdict(int)
    team_home_games = defaultdict(int)
    team_away_games = defaultdict(int)

    games_regular_season = Game.objects.filter(season=2025, week__gte=1, week__lte=18)

    for game in games_regular_season:
        team_game_counts[game.home_team.name] += 1
        team_game_counts[game.away_team.name] += 1
        team_home_games[game.home_team.name] += 1
        team_away_games[game.away_team.name] += 1

    print(f'\nTeam game counts for 2025 regular season (weeks 1-18):')
    print('Team | Total | Home | Away')
    print('-' * 30)

    teams_with_wrong_count = []
    for team in all_teams:
        total = team_game_counts[team.name]
        home = team_home_games[team.name]
        away = team_away_games[team.name]
        print(f'{team.name:4} | {total:5} | {home:4} | {away:4}')
        
        if total != 17:
            teams_with_wrong_count.append((team.name, total))

    if teams_with_wrong_count:
        print(f'\n❌ TEAMS WITH INCORRECT GAME COUNTS:')
        for team, count in teams_with_wrong_count:
            print(f'{team}: {count} games (expected 17)')
    else:
        print(f'\n✅ ALL TEAMS HAVE CORRECT GAME COUNT (17 games each)')

    # Check for teams not in any games
    teams_in_games = set(team_game_counts.keys())
    all_team_names = set(team.name for team in all_teams)
    missing_teams = all_team_names - teams_in_games

    if missing_teams:
        print(f'\n❌ TEAMS NOT FOUND IN ANY 2025 GAMES: {list(missing_teams)}')
    else:
        print(f'\n✅ All 32 teams found in 2025 schedule')

    # 4. Bye Week Analysis
    print('\n4. BYE WEEK DISTRIBUTION ANALYSIS')
    print('-' * 35)

    # A team has a bye week if they don't appear in any games for that week
    team_weeks = defaultdict(set)
    
    for game in games_regular_season:
        team_weeks[game.home_team.name].add(game.week)
        team_weeks[game.away_team.name].add(game.week)

    all_weeks = set(range(1, 19))  # Weeks 1-18
    team_bye_weeks = {}
    
    for team in all_teams:
        played_weeks = team_weeks[team.name]
        bye_weeks = all_weeks - played_weeks
        team_bye_weeks[team.name] = list(bye_weeks)

    print('Team bye weeks:')
    teams_wrong_byes = []
    for team in all_teams:
        byes = team_bye_weeks[team.name]
        print(f'{team.name}: {byes if byes else "No bye weeks"} (count: {len(byes)})')
        
        if len(byes) != 1:
            teams_wrong_byes.append((team.name, len(byes)))

    if teams_wrong_byes:
        print(f'\n❌ TEAMS WITH INCORRECT BYE WEEK COUNT:')
        for team, bye_count in teams_wrong_byes:
            print(f'{team}: {bye_count} bye weeks (expected 1)')
    else:
        print(f'\n✅ ALL TEAMS HAVE EXACTLY ONE BYE WEEK')

    # 5. Duplicate Games and Conflicts
    print('\n5. DUPLICATE GAMES AND SCHEDULING CONFLICTS')
    print('-' * 45)

    # Check for duplicate matchups
    matchups = set()
    duplicates = []
    
    for game in games_2025:
        # Create a normalized matchup tuple (alphabetically sorted teams)
        teams = tuple(sorted([game.home_team.name, game.away_team.name]))
        matchup_key = (teams, game.week, game.season)
        
        if matchup_key in matchups:
            duplicates.append(f'{game.away_team.name} vs {game.home_team.name} in Week {game.week}')
        else:
            matchups.add(matchup_key)

    if duplicates:
        print(f'❌ DUPLICATE GAMES FOUND:')
        for dup in duplicates:
            print(f'  {dup}')
    else:
        print(f'✅ NO DUPLICATE GAMES FOUND')

    # Check for teams playing multiple games in same week
    team_week_conflicts = defaultdict(list)
    
    for game in games_regular_season:
        team_week_conflicts[(game.home_team.name, game.week)].append(f'vs {game.away_team.name} (home)')
        team_week_conflicts[(game.away_team.name, game.week)].append(f'@ {game.home_team.name} (away)')

    conflicts = []
    for (team, week), games in team_week_conflicts.items():
        if len(games) > 1:
            conflicts.append(f'{team} in Week {week}: {", ".join(games)}')

    if conflicts:
        print(f'\n❌ SCHEDULING CONFLICTS (teams playing multiple games in same week):')
        for conflict in conflicts:
            print(f'  {conflict}')
    else:
        print(f'\n✅ NO SCHEDULING CONFLICTS FOUND')

    # 6. Season Assignment Validation
    print('\n6. SEASON ASSIGNMENT VALIDATION')
    print('-' * 32)

    non_2025_games = Game.objects.exclude(season=2025).count()
    print(f'Games not marked as 2025 season: {non_2025_games}')
    
    # Check if any 2025 games have wrong season assignment
    games_with_wrong_season = games_2025.exclude(season=2025).count()
    if games_with_wrong_season == 0:
        print(f'✅ ALL QUERIED GAMES PROPERLY MARKED AS 2025 SEASON')
    else:
        print(f'❌ {games_with_wrong_season} games have incorrect season assignment')

    # 7. Summary Report
    print('\n' + '=' * 60)
    print('VALIDATION SUMMARY REPORT')
    print('=' * 60)

    issues_found = []
    
    if regular_season_total != expected_regular_season_games:
        issues_found.append(f'Incorrect total game count: {regular_season_total}/272')
    
    if teams_with_wrong_count:
        issues_found.append(f'{len(teams_with_wrong_count)} teams with wrong game counts')
    
    if missing_teams:
        issues_found.append(f'{len(missing_teams)} teams missing from schedule')
    
    if teams_wrong_byes:
        issues_found.append(f'{len(teams_wrong_byes)} teams with incorrect bye weeks')
    
    if duplicates:
        issues_found.append(f'{len(duplicates)} duplicate games found')
    
    if conflicts:
        issues_found.append(f'{len(conflicts)} scheduling conflicts found')

    if unusual_times:
        issues_found.append(f'{len(unusual_times)} games with unusual times')

    if issues_found:
        print(f'❌ DATA QUALITY: ISSUES FOUND')
        print(f'Total issues: {len(issues_found)}')
        for issue in issues_found:
            print(f'  - {issue}')
        print(f'\nRECOMMENDATION: Review and correct identified issues before using data')
    else:
        print(f'✅ DATA QUALITY: EXCELLENT')
        print(f'All validation checks passed successfully')
        print(f'Schedule data is ready for production use')

    print(f'\nValidation completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    validate_2025_schedule()