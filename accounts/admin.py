from django.contrib import admin
from .models import Course, Exam, Question, Choice, Result

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4  # Default number of empty choice slots

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'exam')
    list_filter = ('exam',)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'course', 'duration_minutes')

admin.site.register(Course)
admin.site.register(Result)
