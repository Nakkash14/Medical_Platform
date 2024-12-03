from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_TYPES = [
        ('patient', 'Patient'),
        ('docteur', 'Docteur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    firstname = models.CharField(max_length=100, blank=True, null=True)
    lastname = models.CharField(max_length=100, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    occupation = models.CharField(max_length=10, choices=USER_TYPES, blank=True, null=True)
    licence = models.FileField(upload_to='licences/', blank=True, null=True)
    speciality = models.CharField(max_length=100, blank=True, null=True)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile"
