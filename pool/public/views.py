from django.shortcuts import render

from pool.league.models import Season, Player, Match, Team

def index(request):
    season = Season.objects.all().order_by('-start_date').first()

    # get all matches for this season, grouped by player
    players = list(Player.objects.filter(scores__match__season=season).distinct())
    for player in players:
        player.set_season(season)

    # get all teams for this season
    teams = list(Team.season_summary(season))
    players = sorted(players, key=lambda p: p.avg, reverse=True)
    matches = Match.objects.filter(season=season).order_by('date')

    context = dict(season=season, players=players, matches=matches, teams=teams)
    return render(request, 'index.html', context)

def player(request, player_id):
    player = Player.objects.get(id=player_id)

    context = dict(player=player, games=player.get_games(), weeks=player.get_week_averages())
    return render(request, 'player.html', context)

