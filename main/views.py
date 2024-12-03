from django.shortcuts import get_object_or_404, render, redirect
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.http import HttpResponse
import random
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserProfileForm


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Vérifiez si un UserProfile existe pour cet utilisateur
            try:
                profile = user.userprofile
                if profile.occupation == 'patient':
                    return redirect('patient_dashboard')
                elif profile.occupation == 'docteur':
                    return redirect('docteur_dashboard')
                else:
                    messages.warning(request, "Occupation non spécifiée.")
                    return redirect('profile_setup')  # Redirection pour compléter le profil si nécessaire
            except UserProfile.DoesNotExist:
                messages.error(request, "Profil utilisateur introuvable. Veuillez contacter l'administrateur.")
                return redirect('login_page')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            return redirect('login_page')
    
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            
            # Créer un profil vide lié à l'utilisateur
            UserProfile.objects.create(user=user)
            
            request.session['username'] = username
            request.session['verification_code'] = str(random.randint(1000, 9999))
            
            send_mail(
                'Votre code de vérification',
                f'Votre code de vérification est {request.session["verification_code"]}.',
                'medi.plateforme@gmail.com',
                [email],
            )
            return redirect('verify_code')
        else:
            return render(request, 'signup.html', {'error': 'Les mots de passe ne correspondent pas'})
    return render(request, 'signup.html')

@login_required
def my_profile(request):
    user_profile = get_object_or_404(UserProfile, user_id=request.user.id)
    return render(request, 'profile.html', {'user_profile': user_profile})

def verify_code_view(request):
    
    if request.method == 'POST':
        entered_code = request.POST['verification_code']
        if entered_code == request.session.get('verification_code'):
            user = User.objects.get(username=request.session.get('username'))
            login(request, user)  # Connexion automatique
            return redirect('create_profile')  # Rediriger vers création de profil
        else:
            return render(request, 'verify_code.html', {'error': 'Code de vérification invalide'})
    return render(request, 'verify_code.html')

@login_required
def create_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.firstname = request.POST.get('firstname', '').strip()
        profile.lastname = request.POST.get('lastname', '').strip()
        profile.age = request.POST.get('age', None)
        profile.dob = request.POST.get('dob', None)
        profile.gender = request.POST.get('gender', None)
        profile.email = request.POST.get('email', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.occupation = request.POST.get('occupation', None)

        if request.FILES.get('licence'):
            profile.licence = request.FILES.get('licence')

        profile.speciality = request.POST.get('speciality', '').strip()
        profile.terms_accepted = request.POST.get('terms_accepted') == 'on'

        try:
            profile.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('succes_page')
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour du profil : {e}")

    context = {
        'profile': profile,  # Passer les données existantes pour pré-remplir le formulaire
    }

    return render(request, 'create_profile.html', context)

@login_required
def edit_profile(request):
    user_profile = get_object_or_404(UserProfile, user_id=request.user.id)

    if request.method == 'POST':
        # Update fields manually from POST data
        user_profile.firstname = request.POST.get('firstname', user_profile.firstname)
        user_profile.lastname = request.POST.get('lastname', user_profile.lastname)
        user_profile.email = request.POST.get('email', user_profile.email)
        user_profile.age = request.POST.get('age', user_profile.age)
        user_profile.dob = request.POST.get('dob', user_profile.dob)
        user_profile.address = request.POST.get('address', user_profile.address)

        # Save the updated profile
        user_profile.save()
        return render(request, 'my_profile')  # Redirect back to the profile page

    # Render the edit form with current user profile data
    return render(request, 'edit_profile.html', {'user_profile': user_profile})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        password = request.POST.get('password')

        # Authenticate the user's password
        user = authenticate(username=request.user.username, password=password)
        if user is not None:
            # Delete the user profile and the user object
            try:
                request.user.userprofile.delete()  # Delete the UserProfile
            except UserProfile.DoesNotExist:
                pass  # Profile might not exist, handle gracefully
            
            request.user.delete()  # Delete the User object
            messages.success(request, "Your profile has been deleted successfully.")
            return redirect('home')  # Redirect to home or login page
        else:
            messages.error(request, "Incorrect password. Please try again.")

    return render(request, 'delete_profile.html')

def user_logout(request):
    logout(request)
    request.session.flush()  # Vider la session lors de la déconnexion
    return render(request, 'login.html')  # Redirection vers la page de connexion après déconnexion

def success_view(request):
    logout(request)
    return render(request, 'succes.html')

@login_required
def patient_dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'patient_dashboard.html', {'user_profile': user_profile})

@login_required
def docteur_dashboard(request):
    return render(request, 'docteur_dashboard.html')  # Template pour docteur


def dashboard(request):
    return render(request, "index.html")

def dashboard_D(request):
    return render(request, "index_doctor.html")