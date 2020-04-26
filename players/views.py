import copy

import datetime

from django.db import connection, IntegrityError
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'players'
primary_key = 'long_name'
table_columns = ['long_name', 'age', 'dob', 'height_cm', 'weight_kg', 'nationality', 'passing', 'defending', 'shooting',
                 'dribbling', 'pace', 'overall', 'team_jersey_number', 'preferred_foot', 'wage_eur']
drop_columns = ['passing', 'defending', 'shooting', 'dribbling', 'pace']

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

field_restrictions = {
    'ints': {
        'age': 11,
        'height_cm': 11,
        'weight_kg': 11,
        'passing': 11,
        'defending': 11,
        'shooting': 11,
        'dribbling': 11,
        'pace': 11,
        'overall': 11,
        'team_jersey_number': 11,
        'wage_eur': 11
    },
    'str': {
        'long_name': 100,
        'nationality': 100,
        'preferred_foot': 5,
        'position': 4,
        'club_team': 100,
        'national_team': 100
    },
    'date': {
        'dob': '%Y-%m-%d'
    }
}

nullable = ['team_jersey_number', 'wage_eur', 'club_team', 'national_team']
failed_columns = []


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


def check_valid_vals(fields_and_params):
    """
        Takes a dictionary of fields mapped to the values that are trying to be set, then check before trying to execute
        if they match restrictions of database. Returns True if all ok, false otherwise.
    """
    global failed_columns
    failed_columns = []
    for column_name in field_restrictions['ints'].keys():  # check if all ints are set appropriately
        val = fields_and_params.get(column_name + " = %s")
        if val.strip() == "" and column_name not in nullable:
            failed_columns.append(column_name)

        if val.strip() != "":
            try:
                int(val.strip())
            except ValueError:
                failed_columns.append(column_name)

    for column_name, length in field_restrictions['str'].items():
        val = fields_and_params.get(column_name + " = %s")
        if val.strip() == "" and column_name not in nullable:
            failed_columns.append(column_name)

        if len(val.strip()) > length:
            failed_columns.append(column_name)

    for column_name, form in field_restrictions['date'].items():
        val = fields_and_params.get(column_name + " = %s")
        if val is None or val.strip() == "":
            failed_columns.append(column_name)

        try:
            datetime.datetime.strptime(val.strip(), form)
        except ValueError:
            failed_columns.append(column_name)

    if len(failed_columns) > 0:
        failed_columns = list(set(failed_columns))
        return False

    return True


def view_players(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT DISTINCT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())

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

    columns = [item for item in columns if item not in drop_columns]

    records = combine_multi_values(records, pk_vals, 'position')
    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, table_name + '.html', context)


def view_individual(request):
    """
        Gives a view of the person's full set of attributes
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT DISTINCT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(
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
    pk_val_query = "SELECT DISTINCT " + primary_key + " FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(
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
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)

        if len(fields_and_params) != 0:
            main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
            query += " SET " + ", ".join(main_dict.keys()) + " WHERE " + \
                     primary_key + " = %s;"
            params = list(main_dict.values())
            params.append(old_pk_val)
            try:
                all_performed = do_sql(query, params)
            except IntegrityError as err:
                messages.error(request, 'Could not update information for the player due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)

            for alt_table_name, table_info in alt_tables.items():
                alt_dict = {k: v for k, v in fields_and_params.items() if
                            k.split(" ")[0] in table_info['table_columns']}

                if alt_table_name == 'player_positions':
                    query = "DELETE FROM " + alt_table_name + " WHERE long_name = %s;"
                    try:
                        all_performed = do_sql(query, [old_pk_val])
                    except IntegrityError as err:
                        messages.error(request,
                                       'Could not update information for the player due to the following error: ' +
                                       str(err))
                        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)

                    positions = alt_dict['position = %s']
                    position_list = positions.split(",")

                    for position in position_list:
                        query = "INSERT INTO " + alt_table_name + " VALUES (%s, %s);"
                        params = [new_pk_val, position.strip()]
                        try:
                            if not do_sql(query, params):
                                all_performed = False
                        except IntegrityError as err:
                            messages.error(request,
                                           'Could not update information for the player due to the following error: ' +
                                           str(err))
                            return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)

                else:
                    query = "UPDATE " + alt_table_name
                    query += " SET " + ", ".join(alt_dict.keys()) \
                             + " WHERE " + primary_key + " = %s;"
                    params = list(alt_dict.values())
                    params.append(old_pk_val)
                    try:
                        if not do_sql(query, params):
                            all_performed = False
                    except IntegrityError as err:
                        messages.error(request,
                                       'Could not update information for the player due to the following error: ' +
                                       str(err))
                        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)

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
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/add')
        main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
        placeholders = ["%s"] * len(main_dict)
        query += ", ".join(placeholders) + ");"
        try:
            all_performed = do_sql(query, main_dict.values())
        except IntegrityError as err:
            messages.error(request, 'Could not update information for the player due to the following error: ' +
                           str(err))
            return redirect('/' + table_name + '/add')

        for alt_table_name, table_info in alt_tables.items():
            alt_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_info['table_columns']}
            query = 'INSERT INTO ' + alt_table_name + ' VALUES ('
            placeholders = ["%s"] * len(alt_dict)
            query += ", ".join(placeholders) + ");"
            try:
                if not do_sql(query, alt_dict.values()):
                    all_performed = False
            except IntegrityError as err:
                messages.error(request, 'Could not update information for the player due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/add')

        if all_performed:
            return redirect('/' + table_name + '/view?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add')


def add_favorite_player(request, long_name):
        query = 'INSERT INTO favorite_players VALUES (%s, %s);'
        params = (request.session["user"], long_name)
        try:
            if do_sql(query, params):
                return redirect(reverse('view_players'))
            else:
                return redirect(reverse('add_favorite'))
        except IntegrityError as err:
            return redirect('/favorite_players/view')
