from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Reservation

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False, max_length=20)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = Profile.objects.get(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('phone', 'wallet_inr')

class ReservationForm(forms.ModelForm):
    VEHICLE_TYPE_CHOICES = [
        ('bike', 'Bike'),
        ('car', 'Car'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('ev', 'EV'),
    ]
    
    vehicle_type = forms.ChoiceField(
        choices=VEHICLE_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label="Vehicle Type"
    )
    
    class Meta:
        model = Reservation
        fields = ('vehicle_number', 'vehicle_type')
        widgets = {
            'vehicle_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vehicle number (e.g., MH01AB1234)',
                'required': True
            }),
        }
