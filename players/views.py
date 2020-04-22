from django.db import connection

from django.shortcuts import get_object_or_404, render

player_fields = ['long_name', 'age', 'dob', 'height_cm', 'weight_kg', 'nationality', 'passing', 'defending', 'shooting',
                 'dribbling', 'pace', 'overall', 'team_jersey_numbe']


def do_sql(query, params=[]):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return columns, [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def view_players(request):
    params = []
    query = "SELECT * FROM players"
    first_param = True
    for field in player_fields:
        param = request.GET.get(field)
        print("field=", field, "param=", param)
        if param is not None:
            if first_param:
                query += " WHERE"
                first_param = False
            else:
                query += " AND"
            query += " " + field + " = %s"
            params.append(param)

    query += ";"

    columns, players = do_sql(query, params)
    for column in columns:
        print(column)
    context = {'players': players, 'columns': columns}
    return render(request, 'players.html', context)
