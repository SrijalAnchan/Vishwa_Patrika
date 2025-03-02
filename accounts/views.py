from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm, UserUpdateForm
from .models import Profile

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile_edit.html', context)


def password_reset_request(request):

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                from_email=None,
                email_template_name='accounts/password_reset_email.html',
                subject_template_name='accounts/password_reset_subject.txt',
            )
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')  # Redirect to the login page
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})
