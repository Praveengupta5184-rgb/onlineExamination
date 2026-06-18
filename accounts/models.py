from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Course(models.Model):
    title      = models.CharField(max_length=200)
    instructor = models.CharField(max_length=100)
    students   = models.IntegerField(default=0)
    lessons    = models.IntegerField(default=0)
    completed  = models.IntegerField(default=0)  # completed lessons
    status     = models.CharField(max_length=20, default='active')
    content    = models.TextField(blank=True, null=True)
    pdf        = models.FileField(upload_to='course_pdfs/', blank=True, null=True)

    @property
    def progress(self):
        if self.lessons == 0:
            return 0
        return int((self.completed / self.lessons) * 100)

    @property
    def status_class(self):
        return self.status.lower()  # 'active', 'pending', 'closed'


class Exam(models.Model):
    course           = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title            = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=60)
    start_time       = models.DateTimeField(null=True, blank=True)
    end_time         = models.DateTimeField(null=True, blank=True)
    published        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return self.text[:50]


class Choice(models.Model):
    question   = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text       = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Wrong'})"


class Result(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    exam         = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score        = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.score}%"