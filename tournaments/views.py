import copy

from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'tournaments'
primary_key = 'tournament_name'
table_columns = ['tournament_name', 'year', 'prize', 'team_name']


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


def view_tournaments(request):
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


def edit_tournament(request):
    """
        Query parameter will just be the tournament's name. We will look up original values to populate current view and then
        when user clicks submit send all of the values in the update statement. Name cannot be changed.
    """
    if request.method == 'GET':  # this is when the user clicks on a record's pk from the view template
        league_name = request.GET.get(primary_key, None)
        if league_name is None:
            context = {'record': {primary_key: 'None'}}
            return render(request, 'edit_tournament.html', context)

        query = "SELECT * FROM " + table_name
        fields, params = get_fields_and_params(request.GET)

        if len(fields) != 0:
            query += " WHERE " + " AND ".join(fields)
        query += ";"

        columns, record = do_sql(query, params)

        context = {'record': record[0], 'columns': columns, 'params': request.GET}
        return render(request, 'edit_tournament.html', context)

    if request.method == 'POST':  # this is when they click submit on an edit
        query = "UPDATE " + table_name
        old_name = unquote(str(request.get_full_path()).split("=")[1].split("&")[0])
        old_year = unquote(str(request.get_full_path()).split("=")[2])
        new_name = request.POST.get(primary_key)
        new_year = request.POST.get('year')

        fields, params = get_fields_and_params(request.POST)

        if len(fields) != 0:
            query += " SET " + ", ".join(fields) + " WHERE " + primary_key + " = %s AND year = %s;"
            params.append(old_name)
            params.append(old_year)
            if do_sql(query, params):
                return redirect('/' + table_name + '/view?' + primary_key + '=' + new_name + '&' + 'year=' + str(new_year))

        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_name + '&' + 'year=' + str(old_year))


def add_tournament(request):
    if request.method == 'GET':
        context = {'record': 'None', 'columns': table_columns}
        return render(request, 'add_tournament.html', context)

    if request.method == 'POST':
        query = 'INSERT INTO ' + table_name + ' VALUES ('

        fields, params = get_fields_and_params(request.POST)

        placeholders = ["%s"] * len(params)
        query += ", ".join(placeholders) + ");"
        if do_sql(query, params):
            return redirect('/' + table_name + '/view?' + primary_key + '=' + request.POST.get(primary_key))
        else:
            return redirect('/' + table_name + '/add')