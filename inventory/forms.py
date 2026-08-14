from django import forms
from .models import Cylinder


class CylinderScanInForm(forms.ModelForm):

    SOURCE_CHOICES = [
        ('WAREHOUSE', 'Received from Warehouse'),
        ('FIELD', 'Returned from Field'),
    ]

    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )

    class Meta:
        model = Cylinder

        fields = [
            'serial_number',
            'barcode',
            'weight',
            'brand',
            'source',
        ]

        widgets = {
            'serial_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Scan GLP cylinder number',
                    'autofocus': True,
                }
            ),

            'barcode': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Scan barcode',
                }
            ),

            'weight': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter weight in kg',
                    'step': '0.01',
                }
            ),

            'brand': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter cylinder brand',
                }
            ),
        }

    def clean_serial_number(self):
        serial_number = self.cleaned_data['serial_number'].strip().upper()

        if not serial_number.startswith('GLP'):
            raise forms.ValidationError(
                'Invalid cylinder. The serial number must begin with GLP.'
            )

        if Cylinder.objects.filter(
            serial_number=serial_number
        ).exists():
            raise forms.ValidationError(
                'This cylinder already exists in the inventory.'
            )

        return serial_number

    def clean_barcode(self):
        barcode = self.cleaned_data['barcode'].strip()

        if Cylinder.objects.filter(
            barcode=barcode
        ).exists():
            raise forms.ValidationError(
                'This barcode already exists in the inventory.'
            )

        return barcode

    def save(self, commit=True):
        cylinder = super().save(commit=False)

        source = self.cleaned_data['source']

        if source == 'WAREHOUSE':
            cylinder.status = 'FULL'

        elif source == 'FIELD':
            cylinder.status = 'EMPTY'

        if commit:
            cylinder.save()

        return cylinder