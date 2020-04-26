import copy

from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'teams'
primary_key = 'name'
table_columns = ['name', 'num_champs', 'num_wins', 'num_losses', 'num_ties']

alt_tables = {
    'club_teams': {
        'primary_key': 'name',
        'table_columns': ['name', 'payroll', 'league']
    },
    'national_teams': {
        'primary_key': 'name',
        'table_columns': ['name', 'num_world_cups']
    }
}


def do_sql(query, params=[]):
    print("QUERY =", query)
    print("PARAMS =", params)
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


def view_club_teams(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    query = "SELECT * FROM " + table_name + ' NATURAL JOIN club_teams'

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"
    columns, records = do_sql(query, fields_and_params.values())
    print('COLUMNS = ', columns)

    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, 'club_teams.html', context)


def view_national_teams(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    fields_and_params = get_fields_and_params(request.GET)
    query = "SELECT * FROM " + table_name + ' NATURAL JOIN national_teams'

    if len(fields_and_params) != 0:
        query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"
    columns, records = do_sql(query, fields_and_params.values())

    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, 'national_teams.html', context)
