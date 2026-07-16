from django import forms
from .models import *


class UserMasterDetailsForm(forms.ModelForm):
    class Meta:
        model = MenusDetailsModel
        fields = ['uid', 'table_name', 'menu_type', 'authentication_key_value', 'doc_url']

    def __init__(self, *args, **kwargs):
        super(UserMasterDetailsForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


