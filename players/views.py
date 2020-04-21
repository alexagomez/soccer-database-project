from django.db import connection

from rest_framework import status
from rest_framework.response import Response

def my_custom_sql():
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM registered_users;")
        entries = cursor.fetchall()
        for entry in entries:
            print(entry)

    return None

def return_404(self):
    my_custom_sql()
    return Response(status=status.HTTP_404_NOT_FOUND, data={})
