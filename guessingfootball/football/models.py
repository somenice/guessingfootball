from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=10, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    conference = models.CharField(max_length=3, choices=[('AFC', 'AFC'), ('NFC', 'NFC')], blank=True)
    division = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return self.name
    
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
    
    def __str__(self):
        return f"{self.away_team} @ {self.home_team} ({self.game_date.strftime('%Y-%m-%d')})"
    
    @property
    def winner(self):
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None
    
    class Meta:
        ordering = ['game_date']
        unique_together = ['home_team', 'away_team', 'game_date']
