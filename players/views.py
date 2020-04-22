from django.db import connection
from django.views.generic import ListView

from django.shortcuts import get_object_or_404, render


def do_sql(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        return columns, [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def view_players(request):
    columns, players = do_sql("SELECT * FROM players;")
    for column in columns:
        print(column)
    context = {'players': players, 'columns': columns}
    return render(request, 'players.html', context)
