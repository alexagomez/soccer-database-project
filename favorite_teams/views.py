from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect

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
    username = request.session["user"]
    query = "SELECT * FROM "+table_name+" WHERE username='"+request.session["user"]+"';"

    columns, records = do_sql(query)
    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, table_name + '.html', context)

def delete_favorite_team(request, team_name):
    """
        Searches for all records based on query params. returns all records if no query params are present.
    """
    query = "DELETE FROM " + table_name + " WHERE username='"+request.session["user"]+"' AND team_name='"+team_name+"';"

    do_sql(query)

    return HttpResponseRedirect(reverse('view_favorite_teams'))


