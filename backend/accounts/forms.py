from django import forms
from django.contrib.auth import get_user_model


# Step 2 of sign-up (US1.2): the profile details we need before the
# user starts using the site. These fields already exist on Django's User.
class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # User allows these to be blank, but the profile step needs all of them
        for field in self.fields.values():
            field.required = True

    # one account per email (case-insensitive)
    def clean_email(self):
        email = self.cleaned_data["email"]
        taken = get_user_model().objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
