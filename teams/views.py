import copy

from django.db import connection, IntegrityError
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'teams'
primary_key = 'name'
table_columns = ['name', 'num_champs', 'num_wins', 'num_losses', 'num_ties']

club_team_alt = {
    'primary_key': 'name',
    'table_columns': ['name', 'payroll', 'league']
}
national_team_alt = {
    'primary_key': 'name',
    'table_columns': ['name', 'num_world_cups']
}

field_restrictions = {
    'ints': {
        'num_champs': 11,
        'num_wins': 11,
        'num_losses': 11,
        'num_ties': 11,
        'payroll': 11,
        'num_world_cups': 11
    },
    'str': {
        'name': 100,
        'league': 100
    }
}

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

    for field in club_team_alt['table_columns']:
        if field != primary_key:
            param = request_dict.get(field)
            if param is not None:
                field_to_param[field + " = %s"] = param

    for field in national_team_alt['table_columns']:
        if field != primary_key:
            param = request_dict.get(field)
            if param is not None:
                field_to_param[field + " = %s"] = param

    return field_to_param


def check_valid_vals(fields_and_params):
    """
        Takes a dictionary of fields mapped to the values that are trying to be set, then check before trying to execute
        if they match restrictions of database. Returns True if all ok, false otherwise.
    """
    global failed_columns
    failed_columns = []
    for column_name, val in fields_and_params.items():
        if column_name.split(" ")[0] in field_restrictions['ints'].keys():
            if val.strip() == "":
                failed_columns.append(column_name.split(" ")[0])
            else:
                try:
                    int(val.strip())
                except ValueError:
                    failed_columns.append(column_name.split(" ")[0])

        elif column_name.split(" ")[0] in field_restrictions['str'].keys():
            if val.strip() == "":
                failed_columns.append(column_name.split(" ")[0])
            else:
                if len(val.strip()) > field_restrictions['str'][column_name.split(' ')[0]]:
                    failed_columns.append(column_name.split(' ')[0])

    if len(failed_columns) > 0:
        failed_columns = list(set(failed_columns))
        return False

    return True


def view_club_teams(request):
    """
        Searches for all club team records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    query = "SELECT * FROM " + table_name + ' NATURAL JOIN club_teams'

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
    query += ";"
    columns, records = do_sql(query, fields_and_params.values())

    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, 'club_teams.html', context)


def view_national_teams(request):
    """
        Searches for all national team records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    query = "SELECT * FROM " + table_name + ' NATURAL JOIN national_teams'

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
    query += ";"
    columns, records = do_sql(query, fields_and_params.values())

    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, 'national_teams.html', context)


def add_club_team(request):
    if request.method == 'GET':
        full_columns = copy.deepcopy(table_columns)
        full_columns += club_team_alt['table_columns'][1:]
        context = {'record': 'None', 'columns': full_columns}
        return render(request, 'add_club_team.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO ' + table_name + ' VALUES ('

        fields_and_params = get_fields_and_params(request.POST)
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/add_club_team')
        main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
        placeholders = ["%s"] * len(main_dict)
        query += ", ".join(placeholders) + ");"
        try:
            all_performed = do_sql(query, main_dict.values())
        except IntegrityError as err:
            messages.error(request, 'Could not update information for the club team due to the following error: ' +
                           str(err))
            return redirect('/' + table_name + '/add_club_team')
        alt_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in club_team_alt['table_columns']}
        query = 'INSERT INTO club_teams VALUES ('
        placeholders = ["%s"] * len(alt_dict)
        query += ", ".join(placeholders) + ");"
        try:
            if not do_sql(query, alt_dict.values()):
                all_performed = False
        except IntegrityError as err:
            messages.error(request, 'Could not update information for the club team due to the following error: ' +
                           str(err))
            return redirect('/' + table_name + '/add_club_team')

        if all_performed:
            return redirect('/' + table_name + '/view_club_teams?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add_club_team')


def add_national_team(request):
    if request.method == 'GET':
        full_columns = copy.deepcopy(table_columns)
        full_columns += national_team_alt['table_columns'][1:]
        context = {'record': 'None', 'columns': full_columns}
        return render(request, 'add_national_team.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO ' + table_name + ' VALUES ('

        fields_and_params = get_fields_and_params(request.POST)
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/add_national_team')
        main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
        placeholders = ["%s"] * len(main_dict)
        query += ", ".join(placeholders) + ");"
        try:
            all_performed = do_sql(query, main_dict.values())
        except IntegrityError as err:
            messages.error(request, 'Could not update information for the national team due to the following error: ' +
                           str(err))
            return redirect('/' + table_name + '/add_national_team')
        alt_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in national_team_alt['table_columns']}
        query = 'INSERT INTO national_teams VALUES ('
        placeholders = ["%s"] * len(alt_dict)
        query += ", ".join(placeholders) + ");"
        try:
            if not do_sql(query, alt_dict.values()):
                all_performed = False
        except IntegrityError as err:
            messages.error(request, 'Could not update information for the national team due to the following error: ' +
                           str(err))
            return redirect('/' + table_name + '/add_national_team')

        if all_performed:
            return redirect('/' + table_name + '/view_national_teams?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add_national_team')


def edit_club_team(request):
    """
        Query parameter will just be the team's name. We will look up original values to populate current view and then
        when user clicks submit send all of the values in the update statement. Name cannot be changed.
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT " + primary_key + " FROM teams NATURAL JOIN club_teams"

    if len(fields_and_params) != 0:
        pk_val_query += " WHERE " + " AND ".join(fields_and_params.keys())
    pk_val_query += ";"
    pk, pk_vals = do_sql(pk_val_query, fields_and_params.values())

    if request.method == 'GET':  # this is when the user clicks on a record's pk from the view template
        team_name = request.GET.get(primary_key, None)
        if team_name is None:
            context = {'record': {primary_key: 'None'}, 'type': 'club'}
            return render(request, 'edit_team.html', context)

        query = "SELECT * FROM teams NATURAL JOIN club_teams"
        fields_and_params = get_fields_and_params(request.GET)

        if len(fields_and_params) != 0:
            query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"

        columns, record = do_sql(query, fields_and_params.values())

        context = {'record': record[0], 'columns': columns, 'params': request.GET, 'type': 'club'}
        return render(request, 'edit_team.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE " + table_name
        old_pk_val = unquote(str(request.get_full_path()).split("=")[1])
        new_pk_val = request.POST.get(primary_key)

        fields_and_params = get_fields_and_params(request.POST)
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/edit_club_team?' + primary_key + '=' + old_pk_val)

        if len(fields_and_params) != 0:
            main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
            query += " SET " + ", ".join(main_dict.keys()) + " WHERE " + \
                     primary_key + " = %s;"
            params = list(main_dict.values())
            params.append(old_pk_val)
            try:
                all_performed = do_sql(query, params)
            except IntegrityError as err:
                messages.error(request,
                               'Could not update information for the club team due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/edit_club_team?' + primary_key + '=' + old_pk_val)

            alt_dict = {k: v for k, v in fields_and_params.items() if
                            k.split(" ")[0] in club_team_alt['table_columns']}
            query = "UPDATE club_teams"
            query += " SET " + ", ".join(alt_dict.keys()) \
                     + " WHERE " + primary_key + " = %s;"
            params = list(alt_dict.values())
            params.append(old_pk_val)
            try:
                if not do_sql(query, params):
                    all_performed = False
            except IntegrityError as err:
                messages.error(request,
                               'Could not update information for the club team due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/edit_club_team?' + primary_key + '=' + old_pk_val)

            if all_performed:
                return redirect('/' + table_name + '/view_club_teams?' + primary_key + '=' + new_pk_val)

        return redirect('/' + table_name + '/edit_club_team?' + primary_key + '=' + old_pk_val)


def edit_national_team(request):
    """
        Query parameter will just be the team's name. We will look up original values to populate current view and then
        when user clicks submit send all of the values in the update statement. Name cannot be changed.
    """
    fields_and_params = get_fields_and_params(request.GET)
    pk_val_query = "SELECT " + primary_key + " FROM teams NATURAL JOIN national_teams"

    if len(fields_and_params) != 0:
        pk_val_query += " WHERE " + " AND ".join(fields_and_params.keys())
    pk_val_query += ";"
    pk, pk_vals = do_sql(pk_val_query, fields_and_params.values())

    if request.method == 'GET':  # this is when the user clicks on a record's pk from the view template
        team_name = request.GET.get(primary_key, None)
        if team_name is None:
            context = {'record': {primary_key: 'None'}, 'type': 'national'}
            return render(request, 'edit_team.html', context)

        query = "SELECT * FROM teams NATURAL JOIN national_teams"
        fields_and_params = get_fields_and_params(request.GET)

        if len(fields_and_params) != 0:
            query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"

        columns, record = do_sql(query, fields_and_params.values())

        context = {'record': record[0], 'columns': columns, 'params': request.GET, 'type': 'national'}
        return render(request, 'edit_team.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE " + table_name
        old_pk_val = unquote(str(request.get_full_path()).split("=")[1])
        new_pk_val = request.POST.get(primary_key)

        fields_and_params = get_fields_and_params(request.POST)
        if not check_valid_vals(fields_and_params):
            messages.error(request, 'Values of the following columns were invalid, please try again! Columns: '
                           + ", ".join(failed_columns))
            return redirect('/' + table_name + '/edit_national_team?' + primary_key + '=' + old_pk_val)

        if len(fields_and_params) != 0:
            main_dict = {k: v for k, v in fields_and_params.items() if k.split(" ")[0] in table_columns}
            query += " SET " + ", ".join(main_dict.keys()) + " WHERE " + \
                     primary_key + " = %s;"
            params = list(main_dict.values())
            params.append(old_pk_val)
            try:
                all_performed = do_sql(query, params)
            except IntegrityError as err:
                messages.error(request,
                               'Could not update information for the national team due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/edit_national_team?' + primary_key + '=' + old_pk_val)

            alt_dict = {k: v for k, v in fields_and_params.items() if
                            k.split(" ")[0] in national_team_alt['table_columns']}
            query = "UPDATE national_teams"
            query += " SET " + ", ".join(alt_dict.keys()) \
                     + " WHERE " + primary_key + " = %s;"
            params = list(alt_dict.values())
            params.append(old_pk_val)
            try:
                if not do_sql(query, params):
                    all_performed = False
            except IntegrityError as err:
                messages.error(request,
                               'Could not update information for the national team due to the following error: ' +
                               str(err))
                return redirect('/' + table_name + '/edit_national_team?' + primary_key + '=' + old_pk_val)

            if all_performed:
                return redirect('/' + table_name + '/view_national_teams?' + primary_key + '=' + new_pk_val)

        return redirect('/' + table_name + '/edit_national_team?' + primary_key + '=' + old_pk_val)


def add_favorite_team(request, long_name):
    query = 'INSERT INTO favorite_teams VALUES (%s, %s);'
    params = (request.session["user"], long_name)
    try:
        if do_sql(query, params):
            return redirect(reverse('view_club_teams'))
        else:
            return redirect(reverse('add_favorite'))
    except IntegrityError as err:
        return redirect('/favorite_teams/view')
