from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from accounts.forms import RegisterForm, LoginForm
from accounts.models import User, Municipality
from .models import FutureIndicatorCSC, FutureIndicatorValueCSC, CategoriaCSC, EvidencePDFCSC
import json
import os
from django.conf import settings
from django.utils import timezone
import mimetypes
from pathlib import Path
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from accounts.decorators import admin_required, manager_required
