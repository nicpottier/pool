from __future__ import unicode_literals

from smartmin.models import SmartModel
from django.db import models
from django.db.models import Avg, Sum, Q

WEEK_AVG = 8
AVG_GAMES = 72

class Player(SmartModel):
    name = models.CharField(max_length=128,
                            help_text="The player's name")

    def get_games(self):
        scores = list(PlayerScore.objects.filter(player=self).order_by('-match__date'))

        # create a dict of match / game to score
        match_games = dict()
        for score in scores:
            match_games['%d_%d' % (score.match_id, score.game)] = [score]

        q = Q(match_id__lt=0)
        for score in scores:
            q |= (Q(match=score.match, game=score.game) & ~Q(player=self))

        for opp_score in PlayerScore.objects.filter(q):
            match_games['%d_%d' % (opp_score.match_id, opp_score.game)].append(opp_score)

        games = []
        for score in scores:
            opp_score = match_games['%d_%d' % (score.match_id, score.game)][1]
            games.append(dict(date=score.match.date, score=score.score, opponent=opp_score.player.name, opp_score=opp_score.score))

        return games

    def get_week_averages(self):
        scores = list(PlayerScore.objects.filter(player=self).order_by('match__date'))

        weeks = list()
        current_week = dict()

        for score in scores:
            if not current_week or score.match.date != current_week['date']:
                if current_week:
                    current_week['avg'] = float(current_week['total']) / current_week['games']
                    weeks.append(current_week)

                current_week = dict(date=score.match.date, total=score.score, games=1)

            else:
                current_week['total'] += score.score
                current_week['games'] += 1

        if current_week:
            current_week['avg'] = float(current_week['total']) / current_week['games']
            weeks.append(current_week)

        # now build the week avg for each week
        for i in range(len(weeks)):
            game_count = sum(w['games'] for w in weeks[max(0, i-WEEK_AVG):i+1])
            game_total = sum(w['total'] for w in weeks[max(0, i-WEEK_AVG):i+1])
            weeks[i]['running_avg'] = game_total / float(game_count)

        return weeks

    def avg(self, before_date):
        last = list(PlayerScore.objects.filter(match__date__lt=before_date, player=self).order_by('-match__date')[:AVG_GAMES])

        # less than 6 games? default to average
        if len(last) < 6:
            return 7
        else:
            # build up our scores and sort them
            scores = sorted([ps.score for ps in last])

            # figure out our eighth size
            eighth = len(scores) / 8

            # strip off the top and bottom quartile
            scores = scores[eighth:-eighth]

            return float(sum(scores)) / len(scores) if len(scores) > 0 else 0

    def set_season(self, season):
        self.season = season

        # get last games
        last = list(PlayerScore.objects.filter(player=self).order_by('-match__date')[:AVG_GAMES])

        self.wins = sum([1 if ps.score == 10 else 0 for ps in last])
        self.losses = sum([1 if ps.score < 10 else 0 for ps in last])

        self.games = len(last)
        self.points = sum([ps.score for ps in last])

        # build up our scores and sort them
        scores = sorted([ps.score for ps in last])

        # figure out our quartile size
        eighth = len(scores) / 8 if len(scores) > 0 else 0

        # strip off the top and bottom quartile
        scores = scores[eighth:-eighth]
        self.avg = float(sum(scores)) / len(scores) if len(scores) > 0 else 0

        q = Q(match_id__lt=0)
        for score in last:
            q |= (Q(match=score.match, game=score.game) & ~Q(player=self))

        last_opp = list(PlayerScore.objects.filter(q))

        self.opponent_points = sum([ps.score for ps in last_opp])
        self.mpg = float(self.points - self.opponent_points) / self.games if self.games > 0 else 0

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

        if games <= 9:
            num_rounds = 3
        elif games <= 16:
            num_rounds = 4
        elif games <= 24:
            num_rounds = 5
        else:
            raise Exception("unknown number of games")

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
