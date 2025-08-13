from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    conference = models.CharField(max_length=3, choices=[('AFC', 'AFC'), ('NFC', 'NFC')], blank=True)
    division = models.CharField(max_length=10, blank=True)
    
    # 2024 Season Rankings
    rank_2024_league = models.IntegerField(null=True, blank=True)
    rank_2024_conference = models.IntegerField(null=True, blank=True) 
    rank_2024_division = models.IntegerField(null=True, blank=True)
    wins_2024 = models.IntegerField(default=0)
    losses_2024 = models.IntegerField(default=0)
    ties_2024 = models.IntegerField(default=0)
    points_for_2024 = models.IntegerField(default=0)
    points_against_2024 = models.IntegerField(default=0)
    
    # Offense/Defense Rankings (based on points for/against)
    rank_2024_offense_league = models.IntegerField(null=True, blank=True)
    rank_2024_offense_conference = models.IntegerField(null=True, blank=True)
    rank_2024_offense_division = models.IntegerField(null=True, blank=True)
    rank_2024_defense_league = models.IntegerField(null=True, blank=True)
    rank_2024_defense_conference = models.IntegerField(null=True, blank=True) 
    rank_2024_defense_division = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    @property
    def win_percentage_2024(self):
        """Calculate 2024 win percentage"""
        total_games = self.wins_2024 + self.losses_2024 + self.ties_2024
        if total_games == 0:
            return 0.0
        return (self.wins_2024 + (self.ties_2024 * 0.5)) / total_games
    
    @property
    def ranking_display_2024(self):
        """Format 2024 rankings for display"""
        if not self.rank_2024_league:
            return "Rankings not calculated"
        
        parts = []
        
        # League ranking
        if self.rank_2024_league == 1:
            parts.append("1st in league")
        elif self.rank_2024_league == 2:
            parts.append("2nd in league") 
        elif self.rank_2024_league == 3:
            parts.append("3rd in league")
        else:
            parts.append(f"{self.rank_2024_league}th in league")
        
        # Conference ranking
        if self.rank_2024_conference:
            if self.rank_2024_conference == 1:
                parts.append("1st in conference")
            elif self.rank_2024_conference == 2:
                parts.append("2nd in conference")
            elif self.rank_2024_conference == 3:
                parts.append("3rd in conference")
            else:
                # Check for ties by counting teams with same conference ranking
                tied_teams = Team.objects.filter(
                    conference=self.conference,
                    rank_2024_conference=self.rank_2024_conference
                ).count()
                
                if tied_teams > 1:
                    if self.rank_2024_conference <= 3:
                        ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
                        parts.append(f"Tied for {ordinals[self.rank_2024_conference]} in conference")
                    else:
                        parts.append(f"Tied for {self.rank_2024_conference}th in conference")
                else:
                    parts.append(f"{self.rank_2024_conference}th in conference")
        
        # Division ranking
        if self.rank_2024_division:
            division_teams = Team.objects.filter(
                conference=self.conference,
                division=self.division
            ).count()
            
            if self.rank_2024_division == 1:
                parts.append("1st in division")
            elif self.rank_2024_division == division_teams:
                parts.append("last in division")
            elif self.rank_2024_division == 2:
                parts.append("2nd in division")
            elif self.rank_2024_division == 3:
                parts.append("3rd in division")
            else:
                parts.append(f"{self.rank_2024_division}th in division")
        
        return ", ".join(parts)
    
    @property
    def offense_ranking_display_2024(self):
        """Format 2024 offense rankings for display"""
        if not self.rank_2024_offense_league:
            return "Rankings not calculated"
        
        parts = []
        
        # League ranking
        if self.rank_2024_offense_league == 1:
            parts.append("1st in league")
        elif self.rank_2024_offense_league == 2:
            parts.append("2nd in league") 
        elif self.rank_2024_offense_league == 3:
            parts.append("3rd in league")
        else:
            parts.append(f"{self.rank_2024_offense_league}th in league")
        
        # Conference ranking
        if self.rank_2024_offense_conference:
            if self.rank_2024_offense_conference <= 3:
                ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
                parts.append(f"{ordinals[self.rank_2024_offense_conference]} in conference")
            else:
                parts.append(f"{self.rank_2024_offense_conference}th in conference")
        
        # Division ranking
        if self.rank_2024_offense_division:
            if self.rank_2024_offense_division == 1:
                parts.append("1st in division")
            elif self.rank_2024_offense_division == 2:
                parts.append("2nd in division")
            elif self.rank_2024_offense_division == 3:
                parts.append("3rd in division")
            else:
                parts.append("last in division")
        
        return ", ".join(parts)
    
    @property
    def defense_ranking_display_2024(self):
        """Format 2024 defense rankings for display"""
        if not self.rank_2024_defense_league:
            return "Rankings not calculated"
        
        parts = []
        
        # League ranking
        if self.rank_2024_defense_league == 1:
            parts.append("1st in league")
        elif self.rank_2024_defense_league == 2:
            parts.append("2nd in league") 
        elif self.rank_2024_defense_league == 3:
            parts.append("3rd in league")
        else:
            parts.append(f"{self.rank_2024_defense_league}th in league")
        
        # Conference ranking
        if self.rank_2024_defense_conference:
            if self.rank_2024_defense_conference <= 3:
                ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
                parts.append(f"{ordinals[self.rank_2024_defense_conference]} in conference")
            else:
                parts.append(f"{self.rank_2024_defense_conference}th in conference")
        
        # Division ranking
        if self.rank_2024_defense_division:
            if self.rank_2024_defense_division == 1:
                parts.append("1st in division")
            elif self.rank_2024_defense_division == 2:
                parts.append("2nd in division")
            elif self.rank_2024_defense_division == 3:
                parts.append("3rd in division")
            else:
                parts.append("last in division")
        
        return ", ".join(parts)
    
    @classmethod
    def calculate_2024_rankings(cls):
        """Calculate and update 2024 season rankings for all teams"""
        from django.db.models import Count, Q, F
        
        # Calculate 2024 stats for each team
        teams_data = []
        for team in cls.objects.all():
            # Get 2024 games
            home_games = team.home_games.filter(season=2024)
            away_games = team.away_games.filter(season=2024)
            
            wins = losses = ties = 0
            points_for = points_against = 0
            
            # Count home results
            for game in home_games:
                if game.home_score == 0 and game.away_score == 0:
                    continue  # Skip unplayed games
                points_for += game.home_score
                points_against += game.away_score
                if game.home_score > game.away_score:
                    wins += 1
                elif game.home_score < game.away_score:
                    losses += 1
                else:
                    ties += 1
            
            # Count away results
            for game in away_games:
                if game.home_score == 0 and game.away_score == 0:
                    continue  # Skip unplayed games
                points_for += game.away_score
                points_against += game.home_score
                if game.away_score > game.home_score:
                    wins += 1
                elif game.away_score < game.home_score:
                    losses += 1
                else:
                    ties += 1
            
            # Update team stats
            team.wins_2024 = wins
            team.losses_2024 = losses
            team.ties_2024 = ties
            team.points_for_2024 = points_for
            team.points_against_2024 = points_against
            
            win_pct = team.win_percentage_2024
            teams_data.append((team, win_pct, points_for, points_against))
        
        # Sort by win percentage (descending)
        teams_data.sort(key=lambda x: x[1], reverse=True)
        
        # Assign league rankings (by win percentage)
        for i, (team, win_pct, points_for, points_against) in enumerate(teams_data):
            team.rank_2024_league = i + 1
        
        # Calculate conference rankings
        for conference in ['AFC', 'NFC']:
            conf_teams = [(team, win_pct, points_for, points_against) for team, win_pct, points_for, points_against in teams_data if team.conference == conference]
            for i, (team, win_pct, points_for, points_against) in enumerate(conf_teams):
                team.rank_2024_conference = i + 1
        
        # Calculate division rankings
        divisions = [
            ('AFC', 'North'), ('AFC', 'East'), ('AFC', 'South'), ('AFC', 'West'),
            ('NFC', 'North'), ('NFC', 'East'), ('NFC', 'South'), ('NFC', 'West')
        ]
        
        for conference, division in divisions:
            div_teams = [(team, win_pct, points_for, points_against) for team, win_pct, points_for, points_against in teams_data 
                        if team.conference == conference and team.division == division]
            for i, (team, win_pct, points_for, points_against) in enumerate(div_teams):
                team.rank_2024_division = i + 1
        
        # Calculate OFFENSE rankings (based on points for - higher is better)
        offense_data = [(team, points_for) for team, win_pct, points_for, points_against in teams_data]
        offense_data.sort(key=lambda x: x[1], reverse=True)  # Sort by points for (descending)
        
        # League offense rankings
        for i, (team, points_for) in enumerate(offense_data):
            team.rank_2024_offense_league = i + 1
        
        # Conference offense rankings
        for conference in ['AFC', 'NFC']:
            conf_offense = [(team, points_for) for team, points_for in offense_data if team.conference == conference]
            for i, (team, points_for) in enumerate(conf_offense):
                team.rank_2024_offense_conference = i + 1
        
        # Division offense rankings
        for conference, division in divisions:
            div_offense = [(team, points_for) for team, points_for in offense_data 
                          if team.conference == conference and team.division == division]
            for i, (team, points_for) in enumerate(div_offense):
                team.rank_2024_offense_division = i + 1
        
        # Calculate DEFENSE rankings (based on points against - lower is better)
        defense_data = [(team, points_against) for team, win_pct, points_for, points_against in teams_data]
        defense_data.sort(key=lambda x: x[1])  # Sort by points against (ascending)
        
        # League defense rankings
        for i, (team, points_against) in enumerate(defense_data):
            team.rank_2024_defense_league = i + 1
        
        # Conference defense rankings
        for conference in ['AFC', 'NFC']:
            conf_defense = [(team, points_against) for team, points_against in defense_data if team.conference == conference]
            for i, (team, points_against) in enumerate(conf_defense):
                team.rank_2024_defense_conference = i + 1
        
        # Division defense rankings
        for conference, division in divisions:
            div_defense = [(team, points_against) for team, points_against in defense_data 
                          if team.conference == conference and team.division == division]
            for i, (team, points_against) in enumerate(div_defense):
                team.rank_2024_defense_division = i + 1
        
        # Save all teams
        for team, _, _, _ in teams_data:
            team.save()
        
        return len(teams_data)
    
    class Meta:
        ordering = ['name']

class Game(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_games')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_games')
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    game_date = models.DateTimeField()
    week = models.IntegerField()
    season = models.IntegerField()
    
    # Live game status fields
    is_live = models.BooleanField(default=False)
    game_status = models.CharField(max_length=50, blank=True)  # "In Progress", "Halftime", etc.
    current_quarter = models.IntegerField(null=True, blank=True)
    time_remaining = models.CharField(max_length=20, blank=True)  # "12:34", "00:00", etc.
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.away_team} @ {self.home_team} ({self.game_date.strftime('%Y-%m-%d')})"
    
    @property
    def winner(self):
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None
    
    @property
    def is_finished(self):
        """Check if game is completed"""
        return not self.is_live and (self.home_score > 0 or self.away_score > 0)
    
    @property
    def quarter_display(self):
        """Get formatted quarter display"""
        if not self.current_quarter:
            return ""
        if self.current_quarter == 1:
            return "1st"
        elif self.current_quarter == 2:
            return "2nd"
        elif self.current_quarter == 3:
            return "3rd"
        elif self.current_quarter == 4:
            return "4th"
        elif self.current_quarter > 4:
            return f"OT{self.current_quarter - 4 if self.current_quarter > 5 else ''}"
        return ""
    
    @classmethod
    def get_live_games(cls):
        """Get all currently live games"""
        return cls.objects.filter(is_live=True).order_by('game_date')
    
    class Meta:
        ordering = ['game_date']
        unique_together = ['home_team', 'away_team', 'game_date']
