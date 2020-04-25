import copy

from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'players'
primary_key = 'long_name'
table_columns = ['long_name', 'age', 'dob', 'height_cm', 'weight_kg', 'nationality', 'passing', 'defending', 'shooting',
                 'dribbling', 'pace', 'overall', 'team_jersey_number', 'preferred_foot', 'wage_eur']

alt_tables = {
    'player_positions': {
        'primary_key': 'long_name',
        'table_columns': ['long_name', 'position']
    },
    'plays_or_coaches_for': {
        'primary_key': 'long_name',
        'table_columns': ['long_name', 'club_team', 'national_team']
    }
}


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
    field_to_param = {}

    for field in table_columns:
        param = request_dict.get(field)
        if param is not None:
            field_to_param[field + " = %s"] = param

    for table_info in alt_tables.values():
        for field in table_info['table_columns']:
            if field != primary_key:
                param = request_dict.get(field)
                if param is not None:
                    field_to_param[field + " = %s"] = param

    return field_to_param


def combine_multi_values(query_set, primary_key_vals, multi_value_field):
    unique_records = []
    for pk in primary_key_vals:
        entries = list(filter(lambda record: (record[primary_key] == pk[primary_key]), query_set))
        first_entry = entries[0]

        multi_list = []
        for i in range(0, len(entries)):
            multi_list.append(entries[i][multi_value_field])

        first_entry[multi_value_field] = ", ".join(multi_list)
        unique_records.append(first_entry)

    return unique_records


def view_players(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())

    if len(fields_and_params) != 0:
        pk_val_query += " WHERE " + " AND ".join(fields_and_params.keys())
    pk_val_query += ";"
    pk, pk_vals = do_sql(pk_val_query, fields_and_params.values())

    query = "SELECT * FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())
    fields_and_params = get_fields_and_params(request.GET)

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
    query += ";"
    columns, records = do_sql(query, fields_and_params.values())

    records = combine_multi_values(records, pk_vals, 'position')
    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, table_name + '.html', context)


def view_individual(request):
    """
        Gives a view of the person's full set of attributes
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(
        alt_tables.keys())

    if len(fields_and_params) != 0:
        pk_val_query += " WHERE " + " AND ".join(fields_and_params.keys())
    pk_val_query += ";"
    pk, pk_vals = do_sql(pk_val_query, fields_and_params.values())

    player_name = request.GET.get(primary_key, None)
    if player_name is None:
        context = {'record': {primary_key: 'None'}}
        return render(request, 'edit_player.html', context)

    query = "SELECT * FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())
    fields_and_params = get_fields_and_params(request.GET)

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
    query += ";"

    columns, record = do_sql(query, fields_and_params.values())
    record = combine_multi_values(record, pk_vals, 'position')

    context = {'record': record[0], 'columns': columns, 'params': request.GET}
    return render(request, 'view_individual.html', context)




def edit_player(request):
    """
        Query parameter will just be the player's name. We will look up original values to populate current view and then
        when user clicks submit send all of the values in the update statement. Name cannot be changed.
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(
        alt_tables.keys())

    if len(fields_and_params) != 0:
        pk_val_query += " WHERE " + " AND ".join(fields_and_params.keys())
    pk_val_query += ";"
    pk, pk_vals = do_sql(pk_val_query, fields_and_params.values())

    if request.method == 'GET':  # this is when the user clicks on a record's pk from the view template
        player_name = request.GET.get(primary_key, None)
        if player_name is None:
            context = {'record': {primary_key: 'None'}}
            return render(request, 'edit_player.html', context)

        query = "SELECT * FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())
        fields_and_params = get_fields_and_params(request.GET)

        if len(fields_and_params) != 0:
            query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"

        columns, record = do_sql(query, fields_and_params.values())
        record = combine_multi_values(record, pk_vals, 'position')

        context = {'record': record[0], 'columns': columns, 'params': request.GET}
        return render(request, 'edit_player.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE " + table_name
        old_pk_val = unquote(str(request.get_full_path()).split("=")[1])
        new_pk_val = request.POST.get(primary_key)

        fields_and_params = get_fields_and_params(request.POST)

        if len(fields_and_params) != 0:
            main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
            query += " SET " + ", ".join(main_dict.keys()) + " WHERE " + \
                     primary_key + " = %s;"
            params = list(main_dict.values())
            params.append(old_pk_val)
            all_performed = do_sql(query, params)

            for alt_table_name, table_info in alt_tables.items():
                alt_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_info['table_columns']}
                query = "UPDATE " + alt_table_name
                query += " SET " + ", ".join(alt_dict.keys()) \
                         + " WHERE " + primary_key + " = %s;"
                params = list(alt_dict.values())
                params.append(old_pk_val)
                if not do_sql(query, params):
                    all_performed = False

            if all_performed:
                return redirect('/' + table_name + '/view_individual?' + primary_key + '=' + new_pk_val)

        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)


def add_player(request):
    if request.method == 'GET':
        full_columns = copy.deepcopy(table_columns)
        for table_info in alt_tables.values():
            full_columns += table_info['table_columns'][1:]
        context = {'record': 'None', 'columns': full_columns}
        return render(request, 'add_player.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO ' + table_name + ' VALUES ('

        fields_and_params = get_fields_and_params(request.POST)
        main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
        placeholders = ["%s"] * len(main_dict)
        query += ", ".join(placeholders) + ");"
        all_performed = do_sql(query, main_dict.values())
        for alt_table_name, table_info in alt_tables.items():
            alt_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_info['table_columns']}
            query = 'INSERT INTO ' + alt_table_name + ' VALUES ('
            placeholders = ["%s"] * len(alt_dict)
            query += ", ".join(placeholders) + ");"
            if not do_sql(query, alt_dict.values()):
                all_performed = False

        if all_performed:
            return redirect('/' + table_name + '/view?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add')


def add_favorite_player(request, long_name):
        query = 'INSERT INTO favorite_players VALUES (%s, %s);'
        params = (request.session["user"], long_name)
        print('here')
        if do_sql(query, params):
            return redirect(reverse('view_players'))
        else:
            return redirect(reverse('add_favorite'))
