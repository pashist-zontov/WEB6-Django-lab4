"""ВАЛИДАЦИЯ ДАННЫХ СО СТОРОНЫ КЛИЕНТА <views.py>"""

from django import forms
from .models import Request, Comment

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request

        # Используются только поля, которые пользователь может заполнить самостоятельно
        # owner заполняет система вьюх
        fields = ['title', 'description', 'file', 'status']

        # HTML-классы
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Краткая тема заявки"
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': "Подробное описание к заявке"
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    # Кастомная функция с валидацией поля
    def clean_file(self):
        file = self.cleaned_data.get('file')

        if file:
            # Проверка на превышение максимально возможного объёма (2 МБ)
            if file.size > 2 * (2**20):
                raise forms.ValidationError("СЛИШКОМ БОЛЬШОЙ РАЗМЕР ФАЙЛА")
            
            if not file.name.endswith(('.pdf', '.docx', '.doc', '.odt', '.jpg', '.png')):
                raise forms.ValidationError("НЕДОПУСТИМЫЙ ФОРМАТ ФАЙЛА")
        return file
    

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Напишите комментарий к вашей проблеме..."
            })
        }