from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import SignupForm, LoginForm
from plagiarism.models import UserProfile, Submission

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            profession = form.cleaned_data['profession']
            UserProfile.objects.create(user=user, profession=profession)

            messages.success(request, "Signup successful! You can now log in.")
            return redirect('login')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            user = None
            if '@' in username_or_email:
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    pass
            else:
                try:
                    user = User.objects.get(username=username_or_email)
                except User.DoesNotExist:
                    pass

            if user and user.check_password(password):
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def userprofile(request):
    user_profile = request.user.userprofile
    submissions = request.user.submissions.all()
    tab = request.GET.get('tab', 'profile')
    return render(request, 'accounts/userprofile.html', {
        'user_profile': user_profile,
        'submissions': submissions,
        'tab': tab,
    })

@login_required(login_url='login')
def delete_account(request):
    user = request.user
    user.delete()
    return redirect('login')
