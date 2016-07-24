from __future__ import unicode_literals

from smartmin.models import SmartModel
from django.db import models
from django.db.models import Avg, Count, Sum


class Player(SmartModel):
    name = models.CharField(max_length=128,
                            help_text="The player's name")

    def set_season(self, season):
        self.season = season

    def wins(self):
        return PlayerScore.objects.filter(match__season=self.season, player=self, score=10).count()

    def losses(self):
        return PlayerScore.objects.filter(match__season=self.season, player=self, score__lt=10).count()

    def points(self):
        sum = Player.objects.filter(scores__match__season=self.season, id=self.id).annotate(total_pts=Sum('scores__score'))
        if sum:
            return sum[0].total_pts
        else:
            return 0

    def avg(self):
        avg = Player.objects.filter(scores__match__season=self.season, id=self.id).annotate(avg_pts=Avg('scores__score'))
        if avg:
            return avg[0].avg_pts
        else:
            return 0

    def games(self):
        return PlayerScore.objects.filter(match__season=self.season, player=self).count()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Season(SmartModel):
    name = models.CharField(max_length=128,
                            help_text="Season Name")
    start_date = models.DateField(help_text="When the season started")
    end_date = models.DateField(help_text="When the season ended")

    def __unicode__(self):
        return self.name


class Team(SmartModel):
    season = models.ForeignKey(Season)
    name = models.CharField(max_length=128,
                            help_text="The team name")

    def __unicode__(self):
        return self.name


class Match(SmartModel):
    season = models.ForeignKey(Season, related_name='matches')
    team1 = models.ForeignKey(Team, related_name='team1_matches')
    team2 = models.ForeignKey(Team, related_name='team2_matches')
    date = models.DateField()

    def summary(self):
        rounds = []
        match = dict(rounds=rounds, score1=0, score2=0, wins1=0, wins2=0)

        for game_num in range(1, 26):
            if (game_num - 1) % 5 == 0:
                games = []
                round = dict(games=games, round=len(rounds)+1, score1=0, score2=0)
                rounds.append(round)

            p1_score = PlayerScore.objects.filter(match=self, team=self.team1, game=game_num).first()
            p2_score = PlayerScore.objects.filter(match=self, team=self.team2, game=game_num).first()

            if p1_score and p2_score:
                round['score1'] += p1_score.score
                round['score2'] += p2_score.score
                match['score1'] += p1_score.score
                match['score2'] += p2_score.score

                games.append(dict(game=game_num, round=(game_num-1) / 5,
                                  player1=p1_score.player, score1=p1_score.score,
                                  player2=p2_score.player, score2=p2_score.score))

        # calculate wins
        for round in rounds:
            if round['score1'] > round['score2']:
                match['wins1'] += 1
                round['win1'] = True
            elif round['score2'] > round['score1']:
                match['wins2'] += 1
                round['win2'] = True

        if match['score1'] > match['score2']:
            match['wins1'] += 1
            match['score1_win'] = True
        elif match['score2'] > match['score1']:
            match['wins2'] += 1
            match['score2_win'] = True

        if match['wins1'] > match['wins2']:
            match['win1'] = True
        elif match['wins2'] > match['wins1']:
            match['win2'] = True

        return match


class PlayerScore(SmartModel):
    match = models.ForeignKey(Match, related_name='scores')
    game = models.IntegerField()

    team = models.ForeignKey(Team, related_name='scores')
    player = models.ForeignKey(Player, related_name='scores')
    score = models.IntegerField()

    def __unicode__(self):
        return "%s: %d" % (self.player, self.score)
