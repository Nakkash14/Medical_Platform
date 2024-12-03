from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login_page')),  # Redirige l'utilisateur vers la page de login
    path('', include('main.urls')),
]
