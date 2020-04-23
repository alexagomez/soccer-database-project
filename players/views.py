from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote

from django.shortcuts import get_object_or_404, render, redirect

player_fields = ['long_name', 'age', 'dob', 'height_cm', 'weight_kg', 'nationality', 'passing', 'defending', 'shooting',
                 'dribbling', 'pace', 'overall', 'team_jersey_number', 'preferred_foot', 'wage_eur']


def do_sql(query, params=[]):
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, params)
        except OperationalError:
            return False

        if query.find("SELECT") != -1:
            columns = [col[0] for col in cursor.description]
            return columns, [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        else:
            return True


def get_fields_and_params(request_dict):
    fields = []
    params = []

    for field in player_fields:
        param = request_dict.get(field)
        if param is not None:
            fields.append(field + " = %s")
            params.append(param)

    return fields, params


'''
    Searches for all players based on query params. returns all players if no query params are present.
'''
def view_players(request):

    query = "SELECT * FROM players"
    fields, params = get_fields_and_params(request.GET)

    if len(fields) != 0:
        query += " WHERE " + " AND ".join(fields)
    query += ";"

    columns, players = do_sql(query, params)
    context = {'players': players, 'columns': columns, 'params': request.GET}
    return render(request, 'players.html', context)


'''
    Query parameter will just be the player's name. We will look up original values to populate current view and then
    when user clicks submit send all of the values in the update statement. Name cannot be changed.
'''
def edit_player(request):
    if request.method == 'GET':  # this is when the user clicks on a player's name from the players view
        player_name = request.GET.get('long_name', None)
        if player_name is None:
            context = {'player': {'long_name': 'None'}}
            return render(request, 'edit_player.html', context)

        query = "SELECT * FROM players"
        fields, params = get_fields_and_params(request.GET)

        if len(fields) != 0:
            query += " WHERE " + " AND ".join(fields)
        query += ";"

        columns, player = do_sql(query, params)

        context = {'player': player[0], 'columns': columns, 'params': request.GET}
        return render(request, 'edit_player.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE players"
        long_name = unquote(str(request.get_full_path()).split("=")[1])
        new_name = request.POST.get('long_name')

        fields, params = get_fields_and_params(request.POST)

        if len(fields) != 0:
            query += " SET " + ", ".join(fields) + " WHERE long_name = %s;"
            params.append(long_name)
            do_sql(query, params)

        return redirect('/players/edit?long_name='+new_name)


def add_player(request):
    if request.method == 'GET':
        context = {'player': 'None', 'columns': player_fields}
        return render(request, 'add_player.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO players VALUES ('

        fields, params = get_fields_and_params(request.POST)

        placeholders = ["%s"] * len(params)
        query += ", ".join(placeholders) + ");"
        if do_sql(query, params):
            return redirect('/players/view?long_name='+request.POST.get('long_name'))
        else:
            return redirect('/players/add')
