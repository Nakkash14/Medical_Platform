from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'firstname', 'lastname', 'age', 'dob', 'gender', 
            'email', 'address', 'occupation', 'licence', 
            'speciality', 'terms_accepted'
        ]
        labels = {
            'firstname': 'Prénom',
            'lastname': 'Nom',
            'age': 'Âge',
            'dob': 'Date de naissance',
            'gender': 'Genre',
            'email': 'Email',
            'address': 'Adresse',
            'occupation': 'Profession',
            'licence': 'Licence',
            'speciality': 'Spécialité',
            'terms_accepted': 'J’accepte les termes et conditions',
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'formbold-form-input',  # Ajout de la classe CSS principale
                'placeholder': f'Entrez votre {self.fields[field_name].label.lower()}',
            })

        # Champs spécifiques (si vous voulez leur ajouter des classes uniques)
        self.fields['gender'].widget.attrs.update({'class': 'formbold-form-select'})
        self.fields['occupation'].widget.attrs.update({'class': 'formbold-form-select'})
        self.fields['terms_accepted'].widget.attrs.update({
            'class': 'formbold-input-checkbox',
            'style': 'width:auto;',
        })
