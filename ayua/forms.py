from django import forms
from django.core.exceptions import ValidationError
from .models import Orden, Plato
from datetime import date, time
import re
from django.contrib.auth.models import User

class ClienteRegistroForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña"
    )
    password_confirmation = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar contraseña"
    )
    telefono = forms.CharField(
        max_length=12,
        label="Número de Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'})
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'telefono']

    def clean_password_confirmation(self):
        password = self.cleaned_data.get('password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if password != password_confirmation:
            raise ValidationError("Las contraseñas no coinciden.")
        return password_confirmation

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not re.match(r'^\+569\d{8}$', telefono):
            raise ValidationError("El número de teléfono debe estar en el formato +569XXXXXXXX.")
        return telefono

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class PlatoForm(forms.ModelForm):
    class Meta:
        model = Plato
        fields = ['nombre', 'precio', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

class OrdenForm(forms.ModelForm):
    fecha_retiro = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    hora_retiro = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Orden
        fields = ['cantidad', 'fecha_retiro', 'hora_retiro']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'fecha_retiro': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_retiro': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def clean_fecha_retiro(self):
        """
        Validar que la fecha de retiro no sea en el pasado.
        """
        fecha_retiro = self.cleaned_data.get('fecha_retiro')
        if fecha_retiro < date.today():
            raise forms.ValidationError("La fecha de retiro no puede ser en el pasado.")
        return fecha_retiro

    def clean_hora_retiro(self):
        """
        Validar que la hora de retiro esté entre las 10:00 AM y las 10:00 PM.
        """
        hora_retiro = self.cleaned_data.get('hora_retiro')
        if hora_retiro < time(10, 0) or hora_retiro > time(22, 0):
            raise forms.ValidationError("La hora de retiro debe estar entre las 10:00 y las 22:00.")
        return hora_retiro