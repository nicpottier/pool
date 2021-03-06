from smartmin.views import *
from .models import Season, Team, Player, Match, PlayerScore
from django import forms

class SeasonCRUDL(SmartCRUDL):
    actions = ('create', 'list', 'update')
    model = Season

    class List(SmartListView):
        fields = ('name', 'start_date', 'end_date')


class TeamCRUDL(SmartCRUDL):
    actions = ('create', 'list', 'update')
    model = Team

    class List(SmartListView):
        fields = ('name', 'season')


class PlayerCRUDL(SmartCRUDL):
    actions = ('create', 'list', 'update')
    model = Player

    class List(SmartListView):
        fields = ('name', 'created_on')


class MatchCRUDL(SmartCRUDL):
    actions = ('list', 'update', 'batch3', 'batch4', 'batch5', 'delete')
    model = Match

    class List(SmartListView):
        fields = ('season', 'date', 'team1', 'team2')

        def get_context_data(self, **kwargs):
            context = super(MatchCRUDL.List, self).get_context_data(**kwargs)
            context['season'] = Season.objects.filter(is_active=True).order_by('-pk').first()
            return context

    class Update(SmartUpdateView):
        fields = ('season', 'date', 'team1', 'team2')
        delete_url = 'id@league.match_delete'

    class Batch5(SmartFormView):
        class BatchForm(forms.Form):
            def __init__(self, season, **kwargs):
                super(MatchCRUDL.Batch5.BatchForm, self).__init__(**kwargs)
                if season:
                    self.fields['season'].queryset = Season.objects.filter(id=season.id)
                    self.fields['team1'].queryset = Team.objects.filter(season=season)
                    self.fields['team2'].queryset = Team.objects.filter(season=season)

            date = forms.DateField()
            season = forms.ModelChoiceField(Season.objects.all())
            team1 = forms.ModelChoiceField(Team.objects.all())
            team2 = forms.ModelChoiceField(Team.objects.all())

            player1 = forms.ModelChoiceField(Player.objects.all())
            player2 = forms.ModelChoiceField(Player.objects.all())
            player3 = forms.ModelChoiceField(Player.objects.all())
            player4 = forms.ModelChoiceField(Player.objects.all())
            player5 = forms.ModelChoiceField(Player.objects.all(), required=False)
            player6 = forms.ModelChoiceField(Player.objects.all())
            player7 = forms.ModelChoiceField(Player.objects.all())
            player8 = forms.ModelChoiceField(Player.objects.all())
            player9 = forms.ModelChoiceField(Player.objects.all())
            player10 = forms.ModelChoiceField(Player.objects.all(), required=False)

            g01_p1 = forms.IntegerField()
            g01_p2 = forms.IntegerField()
            g02_p1 = forms.IntegerField()
            g02_p2 = forms.IntegerField()
            g03_p1 = forms.IntegerField()
            g03_p2 = forms.IntegerField()
            g04_p1 = forms.IntegerField()
            g04_p2 = forms.IntegerField()
            g05_p1 = forms.IntegerField(required=False)
            g05_p2 = forms.IntegerField(required=False)

            g06_p1 = forms.IntegerField()
            g06_p2 = forms.IntegerField()
            g07_p1 = forms.IntegerField()
            g07_p2 = forms.IntegerField()
            g08_p1 = forms.IntegerField()
            g08_p2 = forms.IntegerField()
            g09_p1 = forms.IntegerField(required=False)
            g09_p2 = forms.IntegerField(required=False)
            g10_p1 = forms.IntegerField(required=False)
            g10_p2 = forms.IntegerField(required=False)

            g11_p1 = forms.IntegerField()
            g11_p2 = forms.IntegerField()
            g12_p1 = forms.IntegerField()
            g12_p2 = forms.IntegerField()
            g13_p1 = forms.IntegerField(required=False)
            g13_p2 = forms.IntegerField(required=False)
            g14_p1 = forms.IntegerField()
            g14_p2 = forms.IntegerField()
            g15_p1 = forms.IntegerField(required=False)
            g15_p2 = forms.IntegerField(required=False)

            g16_p1 = forms.IntegerField()
            g16_p2 = forms.IntegerField()
            g17_p1 = forms.IntegerField(required=False)
            g17_p2 = forms.IntegerField(required=False)
            g18_p1 = forms.IntegerField()
            g18_p2 = forms.IntegerField()
            g19_p1 = forms.IntegerField()
            g19_p2 = forms.IntegerField()
            g20_p1 = forms.IntegerField(required=False)
            g20_p2 = forms.IntegerField(required=False)

            g21_p1 = forms.IntegerField(required=False)
            g21_p2 = forms.IntegerField(required=False)
            g22_p1 = forms.IntegerField()
            g22_p2 = forms.IntegerField()
            g23_p1 = forms.IntegerField()
            g23_p2 = forms.IntegerField()
            g24_p1 = forms.IntegerField()
            g24_p2 = forms.IntegerField()
            g25_p1 = forms.IntegerField(required=False)
            g25_p2 = forms.IntegerField(required=False)

        form_class = BatchForm

        def get_form_kwargs(self):
            kwargs = super(MatchCRUDL.Batch5, self).get_form_kwargs()

            season_id = self.request.GET.get('season')
            if season_id:
                kwargs['season'] = Season.objects.get(id=season_id)
            else:
                kwargs['season'] = None
            return kwargs

        def form_valid(self, form):
            # create all our match objects
            season = form.cleaned_data['season']
            date = form.cleaned_data['date']
            team1 = form.cleaned_data['team1']
            team2 = form.cleaned_data['team2']

            match = Match.objects.create(season=season, date=date, team1=team1, team2=team2,
                                         created_by=self.request.user, modified_by=self.request.user)

            for game in range(1, 26):
                round_offset = (game-1) / 5

                p1_idx = ((game - 1) % 5) + 1
                p2_idx = p1_idx + 5 + round_offset
                if p2_idx > 10:
                    p2_idx -= 5

                p1 = form.cleaned_data['player%d' % p1_idx]
                p2 = form.cleaned_data['player%d' % p2_idx]

                p1_score = form.cleaned_data['g%02d_p1' % game]
                p2_score = form.cleaned_data['g%02d_p2' % game]

                print "[%02d] %d: %s - %d: %s" % (game, p1_idx, str(p1_score), p2_idx, str(p2_score))

                if p1 and p2:
                    PlayerScore.objects.create(team=team1, player=p1, score=p1_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)
                    PlayerScore.objects.create(team=team2, player=p2, score=p2_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)

            # calculate our stats
            match.calculate_stats()

            return HttpResponseRedirect('/')

    class Batch4(SmartFormView):
        class BatchForm(forms.Form):
            def __init__(self, season, **kwargs):
                super(MatchCRUDL.Batch4.BatchForm, self).__init__(**kwargs)
                if season:
                    self.fields['season'].queryset = Season.objects.filter(id=season.id)
                    self.fields['team1'].queryset = Team.objects.filter(season=season)
                    self.fields['team2'].queryset = Team.objects.filter(season=season)

            date = forms.DateField()
            season = forms.ModelChoiceField(Season.objects.all())
            team1 = forms.ModelChoiceField(Team.objects.all())
            team2 = forms.ModelChoiceField(Team.objects.all())

            player1 = forms.ModelChoiceField(Player.objects.all())
            player2 = forms.ModelChoiceField(Player.objects.all())
            player3 = forms.ModelChoiceField(Player.objects.all())
            player4 = forms.ModelChoiceField(Player.objects.all())
            player5 = forms.ModelChoiceField(Player.objects.all())
            player6 = forms.ModelChoiceField(Player.objects.all())
            player7 = forms.ModelChoiceField(Player.objects.all())
            player8 = forms.ModelChoiceField(Player.objects.all())

            g01_p1 = forms.IntegerField()
            g01_p2 = forms.IntegerField()
            g02_p1 = forms.IntegerField()
            g02_p2 = forms.IntegerField()
            g03_p1 = forms.IntegerField()
            g03_p2 = forms.IntegerField()
            g04_p1 = forms.IntegerField()
            g04_p2 = forms.IntegerField()

            g05_p1 = forms.IntegerField()
            g05_p2 = forms.IntegerField()
            g06_p1 = forms.IntegerField()
            g06_p2 = forms.IntegerField()
            g07_p1 = forms.IntegerField()
            g07_p2 = forms.IntegerField()
            g08_p1 = forms.IntegerField()
            g08_p2 = forms.IntegerField()

            g09_p1 = forms.IntegerField()
            g09_p2 = forms.IntegerField()
            g10_p1 = forms.IntegerField()
            g10_p2 = forms.IntegerField()
            g11_p1 = forms.IntegerField()
            g11_p2 = forms.IntegerField()
            g12_p1 = forms.IntegerField()
            g12_p2 = forms.IntegerField()

            g13_p1 = forms.IntegerField()
            g13_p2 = forms.IntegerField()
            g14_p1 = forms.IntegerField()
            g14_p2 = forms.IntegerField()
            g15_p1 = forms.IntegerField()
            g15_p2 = forms.IntegerField()
            g16_p1 = forms.IntegerField()
            g16_p2 = forms.IntegerField()

        form_class = BatchForm

        def get_form_kwargs(self):
            kwargs = super(MatchCRUDL.Batch4, self).get_form_kwargs()

            season_id = self.request.GET.get('season')
            if season_id:
                kwargs['season'] = Season.objects.get(id=season_id)
            else:
                kwargs['season'] = None
            return kwargs

        def form_valid(self, form):
            # create all our match objects
            season = form.cleaned_data['season']
            date = form.cleaned_data['date']
            team1 = form.cleaned_data['team1']
            team2 = form.cleaned_data['team2']

            match = Match.objects.create(season=season, date=date, team1=team1, team2=team2,
                                         created_by=self.request.user, modified_by=self.request.user)

            for game in range(1, 17):
                round_offset = (game - 1) / 4

                p1_idx = ((game - 1) % 4) + 1
                p2_idx = p1_idx + 4 + round_offset
                if p2_idx > 8:
                    p2_idx -= 4

                p1 = form.cleaned_data['player%d' % p1_idx]
                p2 = form.cleaned_data['player%d' % p2_idx]

                p1_score = form.cleaned_data['g%02d_p1' % game]
                p2_score = form.cleaned_data['g%02d_p2' % game]

                if p1 and p2 and (p1_score or p2_score):
                    print "[%02d] %d: %s - %d: %s" % (game, p1_idx, str(p1_score), p2_idx, str(p2_score))
                    PlayerScore.objects.create(team=team1, player=p1, score=p1_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)
                    PlayerScore.objects.create(team=team2, player=p2, score=p2_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)

            # calculate handicaps
            match.calculate_stats()

            return HttpResponseRedirect('/')

    class Batch3(SmartFormView):
        class BatchForm(forms.Form):
            def __init__(self, season, **kwargs):
                super(MatchCRUDL.Batch3.BatchForm, self).__init__(**kwargs)
                if season:
                    self.fields['season'].queryset = Season.objects.filter(id=season.id)
                    self.fields['team1'].queryset = Team.objects.filter(season=season)
                    self.fields['team2'].queryset = Team.objects.filter(season=season)

            date = forms.DateField()
            season = forms.ModelChoiceField(Season.objects.all())
            team1 = forms.ModelChoiceField(Team.objects.all())
            team2 = forms.ModelChoiceField(Team.objects.all())

            player1 = forms.ModelChoiceField(Player.objects.all())
            player2 = forms.ModelChoiceField(Player.objects.all())
            player3 = forms.ModelChoiceField(Player.objects.all())
            player4 = forms.ModelChoiceField(Player.objects.all())
            player5 = forms.ModelChoiceField(Player.objects.all())
            player6 = forms.ModelChoiceField(Player.objects.all())

            g01_p1 = forms.IntegerField()
            g01_p2 = forms.IntegerField()
            g02_p1 = forms.IntegerField()
            g02_p2 = forms.IntegerField()
            g03_p1 = forms.IntegerField()
            g03_p2 = forms.IntegerField()

            g04_p1 = forms.IntegerField()
            g04_p2 = forms.IntegerField()
            g05_p1 = forms.IntegerField()
            g05_p2 = forms.IntegerField()
            g06_p1 = forms.IntegerField()
            g06_p2 = forms.IntegerField()

            g07_p1 = forms.IntegerField()
            g07_p2 = forms.IntegerField()
            g08_p1 = forms.IntegerField()
            g08_p2 = forms.IntegerField()
            g09_p1 = forms.IntegerField()
            g09_p2 = forms.IntegerField()

        form_class = BatchForm

        def get_form_kwargs(self):
            kwargs = super(MatchCRUDL.Batch3, self).get_form_kwargs()

            season_id = self.request.GET.get('season')
            if season_id:
                kwargs['season'] = Season.objects.get(id=season_id)
            else:
                kwargs['season'] = None
            return kwargs

        def form_valid(self, form):
            # create all our match objects
            season = form.cleaned_data['season']
            date = form.cleaned_data['date']
            team1 = form.cleaned_data['team1']
            team2 = form.cleaned_data['team2']

            match = Match.objects.create(season=season, date=date, team1=team1, team2=team2,
                                         created_by=self.request.user, modified_by=self.request.user)

            for game in range(1, 10):
                round_offset = (game - 1) / 3

                p1_idx = ((game - 1) % 3) + 1
                p2_idx = p1_idx + 3 + round_offset
                if p2_idx > 6:
                    p2_idx -= 3

                p1 = form.cleaned_data['player%d' % p1_idx]
                p2 = form.cleaned_data['player%d' % p2_idx]

                p1_score = form.cleaned_data['g%02d_p1' % game]
                p2_score = form.cleaned_data['g%02d_p2' % game]

                if p1 and p2 and (p1_score or p2_score):
                    print "[%02d] %d: %s - %d: %s" % (game, p1_idx, str(p1_score), p2_idx, str(p2_score))
                    PlayerScore.objects.create(team=team1, player=p1, score=p1_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)
                    PlayerScore.objects.create(team=team2, player=p2, score=p2_score, match=match, game=game,
                                               created_by=self.request.user, modified_by=self.request.user)

            # calculate handicaps
            match.calculate_stats()

            return HttpResponseRedirect('/')




