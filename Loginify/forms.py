from django import forms


class SignupForm(forms.Form):
    # The form's name value is saved as UserDetails.username.
    name = forms.CharField(max_length=50, label="Name")
    email = forms.EmailField()
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput,
        help_text="Use at least 8 characters and avoid common passwords.",
    )


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(strip=False, widget=forms.PasswordInput)
