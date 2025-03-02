from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser, Profile

class UserUpdateForm(UserChangeForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'bio']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['location', 'profile_picture', 'website']

class UserUpdateForm(UserChangeForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        
from django import forms
from django.contrib.auth.models import User

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser  # Use your custom user model

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


