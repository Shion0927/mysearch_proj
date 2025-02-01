from django import forms
from .models import Word, Language

class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['word', 'meaning', 'language']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(WordForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['language'].queryset = Language.objects.filter(user=user)

class LanguageForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ['name']