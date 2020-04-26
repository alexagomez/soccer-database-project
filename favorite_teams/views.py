from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

table_name = 'favorite_teams'
primary_keys = ['username', 'team_name']
table_columns = ['username', 'team_name']


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


def view_favorite_teams(request):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """

    query = "SELECT * FROM "+table_name+" WHERE username='"+request.session["user"]+"'"
    fields, params = get_fields_and_params(request.GET)

    if len(fields) != 0:
        query += " AND " + " AND ".join(fields)
    query += ";"
    try:
        columns, records = do_sql(query, params)
        if len(records) != 0:
            context = {'records': records, 'columns': columns, 'params': request.GET}
            return render(request, table_name + '.html', context)
        else:
            messages.error(request, 'Could not find any players with that name, please try again')
            context = {'records': records, 'columns': columns, 'params': request.GET}
            return render(request, table_name + '.html', context)
    except:
        messages.error(request,' failed to retrieve team')
        redirect('view_favorite_teams')

def delete_favorite_team(request, team_name):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    query = "DELETE FROM " + table_name + " WHERE username='"+request.session["user"]+"' AND team_name='"+team_name+"';"

    if do_sql(query):
        messages.success(request,' successfully deleted favorite team')
    else:
        messages.error(request,' failed to delete favorite team')

    return redirect('view_favorite_teams')


