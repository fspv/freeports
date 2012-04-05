from django import forms
class UpdateSwitch(forms.Form):
    name = forms.CharField(max_length=100,required=False)
    middle_name = forms.CharField(required=False)
    
