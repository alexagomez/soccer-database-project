from django.db import connection
from django.db.utils import OperationalError
from urllib.parse import unquote

from django.shortcuts import get_object_or_404, render, redirect

table_name = 'coaches'
primary_key = 'long_name'
table_columns = ['long_name','nationality','years_experience','num_championships','num_wins','num_losses','num_ties']

alt_tables = {
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


def view_coaches(request):
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

    context = {'records': records, 'columns': columns, 'params': request.GET}
    return render(request, table_name + '.html', context)


def edit_coach(request):
    """
        Query parameter will just be the coach's name. We will look up original values to populate current view and then
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
        coach_name = request.GET.get(primary_key, None)
        if coach_name is None:
            context = {'record': {primary_key: 'None'}}
            return render(request, 'edit_coach.html', context)

        query = "SELECT * FROM " + table_name + ' NATURAL JOIN ' + ' NATURAL JOIN '.join(alt_tables.keys())
        fields_and_params = get_fields_and_params(request.GET)

        if len(fields_and_params) != 0:
            query += " WHERE " + " AND ".join(fields_and_params.keys())
        query += ";"

        columns, record = do_sql(query, fields_and_params.values())
        
        context = {'record': record[0], 'columns': columns, 'params': request.GET}
        return render(request, 'edit_coach.html', context)

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
                return redirect('/' + table_name + '/view?' + primary_key + '=' + new_pk_val)

        return redirect('/' + table_name + '/edit?' + primary_key + '=' + old_pk_val)


def add_coach(request):
    if request.method == 'GET':
        full_columns = copy.deepcopy(table_columns)
        for table_info in alt_tables.values():
            full_columns += table_info['table_columns'][1:]
        context = {'record': 'None', 'columns': full_columns}
        return render(request, 'add_coach.html', context)

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
