import copy

from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'leagues'
primary_key = 'league_name'
table_columns = ['league_name', 'country', 'trophy', 'level', 'number_of_teams']


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

    for field in table_columns:
        param = request_dict.get(field)
        if param is not None:
            fields.append(field + " = %s")
            params.append(param)

    return fields, params


def view_leagues(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    query = "SELECT * FROM " + table_name
    fields, params = get_fields_and_params(request.GET)

    if len(fields) != 0:
        query += " WHERE " + " AND ".join(fields)
    query += ";"

    columns, records = do_sql(query, params)
    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, table_name + '.html', context)


def edit_league(request):
    """
        Query parameter will just be the league's name. We will look up original values to populate current view and then
        when user clicks submit send all of the values in the update statement. Name cannot be changed.
    """
    if request.method == 'GET':  # this is when the user clicks on a record's pk from the view template
        league_name = request.GET.get(primary_key, None)
        if league_name is None:
            context = {'record': {primary_key: 'None'}}
            return render(request, 'edit_league.html', context)

        query = "SELECT * FROM " + table_name
        fields, params = get_fields_and_params(request.GET)

        if len(fields) != 0:
            query += " WHERE " + " AND ".join(fields)
        query += ";"

        columns, record = do_sql(query, params)

        context = {'record': record[0], 'columns': columns, 'params': request.GET}
        return render(request, 'edit_league.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE " + table_name
        old_pk_val = unquote(str(request.get_full_path()).split("=")[1])
        new_pk_val = request.POST.get(primary_key)

        fields, params = get_fields_and_params(request.POST)

        if len(fields) != 0:
            query += " SET " + ", ".join(fields) + " WHERE " + primary_key + " = %s;"
            params.append(old_pk_val)
            if do_sql(query, params):
                return redirect('/' + table_name + '/view?' + primary_key + '=' + new_pk_val)

        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)


def add_league(request):
    if request.method == 'GET':
        context = {'record': 'None', 'columns': table_columns}
        return render(request, 'add_league.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO ' + table_name + ' VALUES ('

        fields, params = get_fields_and_params(request.POST)

        placeholders = ["%s"] * len(params)
        query += ", ".join(placeholders) + ");"
        if do_sql(query, params):
            return redirect('/' + table_name + '/view?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add')



