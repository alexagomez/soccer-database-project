from django import forms



class RegisterForm(forms.Form):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'class' : 'form-control'}), max_length=20)
    first_name = forms.CharField(label="First Name", widget=forms.TextInput(attrs={'class' : 'form-control'}), max_length=15)
    last_name = forms.CharField(label="Last Name", widget=forms.TextInput(attrs={'class' : 'form-control'}), max_length=15)
    email = forms.CharField(label="Email Address", widget=forms.TextInput(attrs={'class' : 'form-control'}), max_length=30)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class' : 'form-control'}))
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'class' : 'form-control'}))

class LogInForm(forms.Form):
    username = forms.CharField(label="Username*", widget=forms.TextInput(attrs={'class' : 'form-control'}), max_length=20)
    password1 = forms.CharField(label="Password*", widget=forms.PasswordInput(attrs={'class' : 'form-control'}))