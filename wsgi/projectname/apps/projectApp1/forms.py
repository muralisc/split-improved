from django import forms


class LoginCreateForm(forms.Form):
    email = forms.EmailField(label='', widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'input-block-level'}))
    password = forms.CharField(max_length=50, label='', widget=forms.PasswordInput(attrs={'class': 'input-block-level', 'placeholder': 'Password'}))
