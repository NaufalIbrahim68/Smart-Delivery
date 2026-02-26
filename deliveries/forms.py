from django import forms
from .models import Delivery


class ExcelUploadForm(forms.Form):
    """Form for uploading an Excel file to bulk-import deliveries."""
    excel_file = forms.FileField(
        label='Excel File (.xlsx)',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
    )

    def clean_excel_file(self):
        f = self.cleaned_data['excel_file']
        if not f.name.endswith('.xlsx'):
            raise forms.ValidationError('Only .xlsx files are accepted.')
        return f


class DeliveryForm(forms.ModelForm):
    """
    ModelForm for creating and editing Delivery records.
    """
    class Meta:
        model = Delivery
        fields = [
            'tracking_number', 'vendor', 'status',
            'origin_city', 'destination_city',
            'order_date', 'scheduled_date', 'actual_delivery_date',
            'weight_kg', 'quantity', 'recipient_name', 'notes',
        ]
        widgets = {
            'tracking_number':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. JNE-20240101-001'}),
            'vendor':               forms.Select(attrs={'class': 'form-select'}),
            'status':               forms.Select(attrs={'class': 'form-select'}),
            'origin_city':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Jakarta'}),
            'destination_city':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Surabaya'}),
            'order_date':           forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_date':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weight_kg':            forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'quantity':             forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'recipient_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full recipient name'}),
            'notes':                forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
