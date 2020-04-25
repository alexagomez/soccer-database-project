from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.views.generic import FormView
from django.db.utils import OperationalError
from users.forms import RegisterForm, LogInForm, RemoveForm
from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
from django.views.generic import ListView
from django.http import HttpResponse, HttpResponseRedirect

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

def do_sql_return(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        return columns, [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

def login(request):
    try:
        if(request.session["user"]):
            return HttpResponseRedirect(reverse('show_players'))
    except:
        return HttpResponseRedirect(reverse('loginform'))

def logout(request):
    try:
        del request.session['user']
        return HttpResponseRedirect(reverse("loginform"))
    except KeyError:
        return HttpResponseRedirect(reverse('signupform'))

class SignUp(FormView):
    form_class = RegisterForm
    success_url = '/players/view'
    template_name = 'signup.html'

    def form_valid(self, form):
        username = self.request.POST['username']
        first = self.request.POST['first_name']
        last = self.request.POST['last_name']
        email = self.request.POST['email']
        password = self.request.POST['password1']
        hashed_passwd = make_password(password, None, 'pbkdf2_sha256')
        vals = (username, first, last, email, hashed_passwd)
        try:
            do_sql("INSERT into registered_users (username, first_name, last_name, email, password) VALUES(%s, %s, %s, %s, %s);", vals)
            self.request.session['user'] = username
            return super(SignUp, self).form_valid(form)
        except:
            form.add_error(field='username', error='Invalid password for this username')
            return HttpResponseRedirect(reverse('signup')) 

class LogIn(FormView):
    form_class = LogInForm
    success_url = '/players/view'
    template_name = 'login.html'

    def form_valid(self, form):
        username = self.request.POST['username']
        password = self.request.POST['password1']
        columns, hashed = do_sql_return(f"Select password From registered_users Where username='{username}';")
        if(check_password(password, hashed[0]["password"]), None, 'pbkdf2_sha256'):
            print('success')
            self.request.session['user'] = username
            return super(LogIn, self).form_valid(form)
        else:
            form.add_error(field='password1', error='Invalid password for this username')
            return HttpResponseRedirect(reverse('login')) 

class RemoveAccount(FormView):
    form_class = RemoveForm
    success_url = 'signup'
    template_name = 'remove.html'

    def form_valid(self, form):
        username = self.request.POST['username']
        password = self.request.POST['password1']
        columns, hashed = do_sql_return(f"Select password From registered_users Where username='{username}';")
        if(check_password(password, hashed[0]["password"]), None, 'pbkdf2_sha256'):
            if do_sql("DELETE FROM favorite_players WHERE username='"+username+"';"):
                print('deleted favorite_players')
                if do_sql("DELETE FROM favorite_teams WHERE username='"+username+"';"):
                    print('deleted favorite_teams')
                    if do_sql("DELETE FROM registered_users WHERE username='"+username+"';"):
                        print('deleted registered_users')
                        try:
                            if self.request.session["user"]:
                                del request.session["user"]
                        except:
                            pass
                        return super(RemoveAccount, self).form_valid(form)
                    else:
                        print('failed at remove user')
                        return HttpResponseRedirect(reverse('remove')) 
                else:
                    print('failed at remove teams')
                    return HttpResponseRedirect(reverse('remove'))
            else:
                print('failed at remove players')
                return HttpResponseRedirect(reverse('remove'))
        else:
            return HttpResponseRedirect(reverse('remove')) 
