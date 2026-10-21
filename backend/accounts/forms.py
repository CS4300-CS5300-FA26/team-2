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
