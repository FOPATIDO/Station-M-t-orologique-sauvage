"""
users/forms.py
Formulaires Django pour l'application DesertMet
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import EmailValidator, MinLengthValidator
from django.core.exceptions import ValidationError

from .models import User, Station


class LoginForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@domaine.com',
            'required': True
        }),
        label='Adresse email'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
            'required': True
        }),
        label='Mot de passe'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)  # On utilise email, pas username


class RegisterForm(UserCreationForm):
    """
    Formulaire d'inscription personnalisé
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@domaine.com',
            'required': True
        }),
        label='Adresse email',
        validators=[EmailValidator(message="Adresse email invalide")]
    )

    fullname = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean Dupont',
            'required': True
        }),
        label='Nom complet',
        validators=[MinLengthValidator(2, message="Le nom doit contenir au moins 2 caractères")]
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 caractères',
            'required': True
        }),
        label='Mot de passe',
        help_text='Minimum 8 caractères'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Répétez le mot de passe',
            'required': True
        }),
        label='Confirmation du mot de passe'
    )

    class Meta:
        model = User
        fields = ('email', 'fullname', 'password1', 'password2')

    def clean_email(self):
        """
        Validation personnalisée de l'email
        """
        email = self.cleaned_data.get('email')

        # Vérifier si l'email existe déjà
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")

        return email

    def clean_password2(self):
        """
        Validation personnalisée des mots de passe
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")

        return password2

    def save(self, commit=True):
        """
        Sauvegarde de l'utilisateur avec le mot de passe haché
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.fullname = self.cleaned_data['fullname']

        if commit:
            user.save()
        return user


class StationForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une station
    """

    class Meta:
        model = Station
        fields = [
            'nom', 'latitude', 'longitude', 'energie', 'communication',
            'status', 'capteur_temperature', 'capteur_pression',
            'capteur_vent', 'capteur_ensoleillement', 'capteur_precipitation'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Station Sahara Nord'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'min': '-90',
                'max': '90'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'min': '-180',
                'max': '180'
            }),
            'energie': forms.Select(attrs={'class': 'form-control'}),
            'communication': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nom de la station',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'energie': 'Source d\'énergie',
            'communication': 'Type de communication',
            'status': 'État de fonctionnement',
            'capteur_temperature': 'Capteur de température',
            'capteur_pression': 'Capteur de pression',
            'capteur_vent': 'Capteur de vent',
            'capteur_ensoleillement': 'Capteur d\'ensoleillement',
            'capteur_precipitation': 'Capteur de précipitation',
        }
        help_texts = {
            'latitude': 'Valeur entre -90 et +90',
            'longitude': 'Valeur entre -180 et +180',
        }

    def clean_latitude(self):
        """
        Validation de la latitude
        """
        latitude = self.cleaned_data.get('latitude')
        if latitude < -90 or latitude > 90:
            raise ValidationError("La latitude doit être entre -90 et +90.")
        return latitude

    def clean_longitude(self):
        """
        Validation de la longitude
        """
        longitude = self.cleaned_data.get('longitude')
        if longitude < -180 or longitude > 180:
            raise ValidationError("La longitude doit être entre -180 et +180.")
        return longitude


class LoginForm(forms.Form):
        """
        Formulaire de connexion simplifié
        """
        email = forms.EmailField(
            label='Adresse email',
            widget=forms.EmailInput(attrs={
                'placeholder': 'exemple@mail.com',
                'class': 'form-control'
            })
        )

        password = forms.CharField(
            label='Mot de passe',
            widget=forms.PasswordInput(attrs={
                'placeholder': '••••••••',
                'class': 'form-control'
            })
        )

        def clean(self):
            """
            Validation personnalisée pour l'authentification
            """
            cleaned_data = super().clean()
            email = cleaned_data.get('email')
            password = cleaned_data.get('password')

            if email and password:
                # Authentifier l'utilisateur
                user = authenticate(email=email, password=password)

                if user is None:
                    # Si l'authentification échoue
                    raise forms.ValidationError(
                        "Email ou mot de passe incorrect. Veuillez réessayer."
                    )

                if not user.is_active:
                    raise forms.ValidationError("Ce compte est désactivé.")

            return cleaned_data