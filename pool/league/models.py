from __future__ import unicode_literals

from smartmin.models import SmartModel
from django.db import models
from django.db.models import Avg, Sum, Q


class Player(SmartModel):
    name = models.CharField(max_length=128,
                            help_text="The player's name")

    def avg(self, before_date):
        last_24 = list(PlayerScore.objects.filter(match__date__lt=before_date, player=self).order_by('-match__date')[:24])

        # less than 4 games? default to average
        if len(last_24) < 4:
            return 7
        else:
            return float(sum([ps.score for ps in last_24])) / len(last_24)

    def avg_17(self, before_date):
        last_24 = list(PlayerScore.objects.filter(match__date__lt=before_date, player=self).order_by('-match__date')[:24])

        # less than 4 games? default to average
        if len(last_24) < 4:
            return 10
        else:
            q = Q(match_id__lt=0)
            for score in last_24:
                q |= (Q(match=score.match, game=score.game) & ~Q(player=self))

            last_24_opp = list(PlayerScore.objects.filter(q))

            points = sum([ps.score for ps in last_24])
            opp_balls_left = sum([7 - ps.score if ps.score < 10 else 0 for ps in last_24_opp])
            return float(points + opp_balls_left) / len(last_24)

    def set_season(self, season):
        self.season = season

        # get last 24 games
        last_24 = list(PlayerScore.objects.filter(player=self).order_by('-match__date')[:24])

        self.wins = sum([1 if ps.score == 10 else 0 for ps in last_24])
        self.losses = sum([1 if ps.score < 10 else 0 for ps in last_24])

        self.games = len(last_24)
        self.points = sum([ps.score for ps in last_24])

        self.avg = float(self.points) / self.games if self.games > 0 else 0

        q = Q(match_id__lt=0)
        for score in last_24:
            q |= (Q(match=score.match, game=score.game) & ~Q(player=self))

        last_24_opp = list(PlayerScore.objects.filter(q))

        self.opponent_points = sum([ps.score for ps in last_24_opp])
        self.opp_balls_left = sum([7 - ps.score if ps.score < 10 else 0 for ps in last_24_opp])
        self.avg_17 = float(self.points + self.opp_balls_left) / self.games if self.games > 0 else 0

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

    @classmethod
    def season_summary(cls, season):
        teams = dict()
        for team in Team.objects.filter(season=season).distinct():
            team.points = 0
            team.games = 0
            team.wins = 0
            team.losses = 0
            teams[team] = team

        for match in Match.objects.filter(season=season):
            games = match.scores.count() / 2
            team1 = teams[match.team1]
            team2 = teams[match.team2]

            team1.points += match.points1
            team1_wins = match.scores.filter(team=match.team1, score=10).count()
            team1_losses = games - team1_wins
            team1.wins += team1_wins
            team1.losses += team1_losses
            team1.games += games

            team2.points += match.points2
            team2_wins = match.scores.filter(team=match.team2, score=10).count()
            team2_losses = games - team2_wins
            team2.wins += team2_wins
            team2.losses += team2_losses
            team2.games += games

        # sort our values by points
        return sorted(teams.values(), key=lambda t: t.points, reverse=True)

    def __unicode__(self):
        return self.name


class Match(SmartModel):
    season = models.ForeignKey(Season, related_name='matches')

    team1 = models.ForeignKey(Team, related_name='team1_matches')
    team2 = models.ForeignKey(Team, related_name='team2_matches')

    handicap1 = models.IntegerField(default=0)
    handicap2 = models.IntegerField(default=0)

    points1 = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    points2 = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    date = models.DateField()

    def sum_for_players(self, players):
        player_sum = 0
        for player in players:
            player_avg = player.avg(self.date)
            print "%s: %f" % (player.name, player_avg)
            player_sum += player_avg

        return player_sum

    def calculate_handicaps(self):
        # calculate average score for team 1 players for this season before this date
        print "Team1----------"
        team1_sum = self.sum_for_players(Player.objects.filter(scores__match=self, scores__team=self.team1).distinct())
        print team1_sum
        print "Team2----------"
        team2_sum = self.sum_for_players(Player.objects.filter(scores__match=self, scores__team=self.team2).distinct())
        print team2_sum

        if team1_sum > team2_sum:
            self.handicap1 = 0
            self.handicap2 = round(team1_sum - team2_sum - .01)
        else:
            self.handicap1 = round(team2_sum - team1_sum - .01)
            self.handicap2 = 0

    def summary(self):
        rounds = []
        match = dict(rounds=rounds, score1=0, score2=0, points1=0, points2=0)

        # are we 16 games or 25?
        last_game = PlayerScore.objects.filter(match=self).order_by('-game').first()
        games = 25
        if last_game:
            games = last_game.game

        if games == 16:
            num_rounds = 4
        else:
            num_rounds = 5

        for game_num in range(1, games+1):
            if (game_num - 1) % num_rounds == 0:
                games = []
                round = dict(games=games, round=len(rounds)+1, score1=0, score2=0)
                rounds.append(round)

            p1_score = PlayerScore.objects.filter(match=self, team=self.team1, game=game_num).first()
            p2_score = PlayerScore.objects.filter(match=self, team=self.team2, game=game_num).first()

            if p1_score and p2_score:
                round['score1'] += p1_score.score
                round['score2'] += p2_score.score

                games.append(dict(game=game_num, round=(game_num-1) / num_rounds,
                                  player1=p1_score.player, score1=p1_score.score,
                                  player2=p2_score.player, score2=p2_score.score))

        # add in handicaps
        for round in rounds:
            round['hscore1'] = round['score1'] + self.handicap1
            round['hscore2'] = round['score2'] + self.handicap2
            match['score1'] += round['hscore1']
            match['score2'] += round['hscore2']

        # calculate wins
        for round in rounds:
            if round['hscore1'] > round['hscore2']:
                match['points1'] += 1
                round['win1'] = True

            elif round['hscore2'] > round['hscore1']:
                match['points2'] += 1
                round['win2'] = True

            else:
                match['points1'] += .5
                match['points2'] += .5
                round['win1'] = True
                round['win2'] = True

        if match['score1'] > match['score2']:
            match['points1'] += 1
            match['score1_win'] = True

        elif match['score2'] > match['score1']:
            match['points2'] += 1
            match['score2_win'] = True

        if match['points1'] > match['points2']:
            match['win1'] = True
        elif match['points2'] > match['points1']:
            match['win2'] = True

        match['handicap1'] = self.handicap1
        match['handicap2'] = self.handicap2

        return match

    def calculate_stats(self):
        # calculate handicaps
        self.calculate_handicaps()

        # calculate wins
        summary = self.summary()
        self.points1 = summary['points1']
        self.points2 = summary['points2']
        self.save()

    def __unicode__(self):
        return "%s vs %s on %s" % (str(self.team1), str(self.team2), str(self.date))

    class Meta:
        verbose_name_plural = "Matches"


class PlayerScore(SmartModel):
    match = models.ForeignKey(Match, related_name='scores')
    game = models.IntegerField()

    team = models.ForeignKey(Team, related_name='scores')
    player = models.ForeignKey(Player, related_name='scores')
    score = models.IntegerField()

    def __unicode__(self):
        return "%s: %d" % (self.player, self.score)
