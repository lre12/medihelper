from django import forms
class SearchForm(forms):
	word = forms.Charfield(label='증상입력')