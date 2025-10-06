from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Reserva, Habitacion, TipoHabitacion

class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre'
        }),
        label='Nombre'
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu apellido'
        }),
        label='Apellido'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico'
    )

    telefono = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56 9 1234 5678'
        }),
        label='Teléfono'
    )

    direccion = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu dirección'
        }),
        label='Dirección'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases de Bootstrap a los campos heredados
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Elige un nombre de usuario'
        })
        self.fields['username'].label = 'Nombre de Usuario'

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••'
        })
        self.fields['password1'].label = 'Contraseña'

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••'
        })
        self.fields['password2'].label = 'Confirmar Contraseña'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        return user


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['fecha_entrada', 'fecha_salida', 'numero_huespedes', 'comentarios']
        widgets = {
            'fecha_entrada': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'fecha_salida': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'numero_huespedes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'comentarios': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Comentarios adicionales (opcional)'
            }),
        }
        labels = {
            'fecha_entrada': 'Fecha de Entrada',
            'fecha_salida': 'Fecha de Salida',
            'numero_huespedes': 'Número de Huéspedes',
            'comentarios': 'Comentarios',
        }


class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'tipo', 'piso', 'descripcion']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'piso': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la habitación'
            }),
        }
        labels = {
            'numero': 'Número de Habitación',
            'tipo': 'Tipo de Habitación',
            'piso': 'Piso',
            'descripcion': 'Descripción',
        }


class TipoHabitacionForm(forms.ModelForm):
    class Meta:
        model = TipoHabitacion
        fields = ['nombre', 'descripcion', 'precio_por_noche', 'capacidad_maxima']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),  # Cambié Select por TextInput
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'precio_por_noche': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'capacidad_maxima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }
        labels = {
            'nombre': 'Tipo de Habitación',
            'descripcion': 'Descripción',
            'precio_por_noche': 'Precio por Noche',
            'capacidad_maxima': 'Capacidad Máxima',
        }