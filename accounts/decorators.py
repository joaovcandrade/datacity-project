from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin():
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_manager()):
            messages.error(request, 'Você não tem permissão para acessar esta página.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta página.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view 