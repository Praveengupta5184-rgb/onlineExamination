from django import forms
from .models import Course, Exam
from .models import Question, Choice
from django.forms import inlineformset_factory


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'instructor', 'lessons', 'status', 'content', 'pdf']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'lessons': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'status': forms.Select(choices=[('active', 'Active'), ('pending', 'Pending'), ('closed', 'Closed')], attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['course', 'title', 'duration_minutes', 'start_time', 'end_time', 'published']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


ChoiceFormSet = inlineformset_factory(Question, Choice, form=ChoiceForm, extra=4, can_delete=True)
