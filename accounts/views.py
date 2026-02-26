from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


def login_view(request):
    """Login page — redirects to dashboard if already logged in."""
    if request.user.is_authenticated:
        return redirect('deliveries:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url else 'deliveries:dashboard')
        else:
            messages.error(request, '❌ Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """Log the user out and redirect to login."""
    logout(request)
    messages.success(request, '✅ You have been logged out.')
    return redirect('accounts:login')
