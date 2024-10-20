from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail

from hackerthin import settings
from .models import Profile, PersonalProfile, InternProfile, Major, Subscription, Community, SupportEmail, Room


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('user', 'username', 'email', 'avatar', 'alternate', 'about_me', 'keywords', 'opt_in')


class PersonalProfileForm(forms.ModelForm):
    class Meta:
        model = PersonalProfile
        fields = ('full_name', 'date_of_birth', 'state', 'city')


class InternProfileForm(forms.ModelForm):
    class Meta:
        model = InternProfile
        fields = ('username', 'major', 'resume')


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class EmailForm(forms.ModelForm):
    email = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Email'}))

    class Meta:
        model = Subscription
        fields = ('email', 'opt_in')

    def clean_confirmation(self):
        confirmation = self.cleaned_data.get('confirmation')
        if not confirmation:
            raise forms.ValidationError("You must agree to the terms to continue.")
        return confirmation
        # name = forms.CharField(widget = forms.TextInput(attrs={'placeholder':'Enter your first name'}))

        # description = forms.CharField(widget = forms.EmailInput
        # (attrs={'placeholder':'Enter your email'}))


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'logo']  # Add any other fields you want users to fill in
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Enter a brief description...'}),
        }


class SupportEmailForm(forms.ModelForm):
    class Meta:
        model = SupportEmail
        fields = {"user", "subject", "email", "message"}

        widgets = {
            "user": forms.TextInput(attrs={"class": "form-control", 'placeholder': 'e.g. Marinara Sauce'}),
            "subject": forms.TextInput(attrs={"class": "form-control", 'placeholder': 'Subject of your message.'}),
            "email": forms.TextInput(attrs={"class": "form-control", 'placeholder': 'e.g. Intellex@gmail.com'}),
            "message": forms.TextInput(attrs={"class": "form-control", 'placeholder': 'Your message.'})
        }

    def get_info(self):
        """
        Method that returns formatted information
        :return: subject, msg
        """
        # Cleaned data
        cl_data = super().clean()

        name = cl_data.get('name').strip()
        from_email = cl_data.get('email')
        subject = cl_data.get('inquiry')

        msg = f'{name} with email {from_email} said:'
        msg += f'\n"{subject}"\n\n'
        msg += cl_data.get('message')

        return subject, msg, from_email

    def send(self):
        subject, msg, from_email = self.get_info()

        send_mail(
            subject=subject,
            message=msg,
            from_email=from_email,
            recipient_list=[settings.EMAIL_HOST_USER]
        )


class RSVPForm(forms.Form):
    confirm = forms.BooleanField(required=True, label="RSVP to this event")


class FriendRequestForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Enter Username",
        widget=forms.TextInput(attrs={
            'placeholder': 'Warning: case sensitive!'  # Add placeholder text here
        })
    )


class RoomCreationForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'public', 'logo']