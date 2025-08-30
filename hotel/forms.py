from django import forms
from .models import Reserva, Habitacion, TipoHabitacion

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
            'nombre': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'precio_por_noche': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
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