from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Avg, Q
from django.db.utils import OperationalError
from django.utils import timezone
from .models import Course, Exam, Question, Choice, Result
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import CourseForm, ExamForm, QuestionForm, ChoiceFormSet
from django.shortcuts import get_object_or_404


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'login.html')

        users = User.objects.filter(email__iexact=email)
        if not users.exists():
            messages.error(request, 'Invalid credentials.')
            return render(request, 'login.html')

        user = None
        for user_obj in users:
            candidate = authenticate(request, username=user_obj.username, password=password)
            if candidate is not None:
                user = candidate
                break

        if user is not None:
            login(request, user)
            # Route to appropriate dashboard
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
            return render(request, 'login.html')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not (first_name and last_name and email and password1 and password2):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'register.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'register.html')

        # Use email as username when possible to make authentication simple
        base_username = email
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username.split('@')[0]}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()
        messages.success(request, 'Account created successfully. You can now sign in.')
        return redirect('login')

    return render(request, 'register.html')


def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('student_dashboard')
    
    schema_error = False
    error_message = ''

    try:
        courses = Course.objects.all().order_by('title')
        exams = Exam.objects.select_related('course').order_by('-created_at')
        results = Result.objects.select_related('user', 'exam', 'exam__course')
        students = User.objects.filter(is_staff=False)

        total_courses = courses.count()
        total_exams = exams.count()
        total_students = students.count()
        avg_score = int(results.aggregate(avg_score=Avg('score'))['avg_score'] or 0)

        upcoming_exams = [
            {
                'id': exam.id,
                'day': exam.created_at.day,
                'month': exam.created_at.strftime('%b'),
                'title': exam.title,
                'course': exam.course.title if exam.course else '-',
                'duration': f'{exam.duration_minutes} min',
            }
            for exam in exams[:5]
        ]

        course_data = [
            {
                'title': course.title,
                'instructor': course.instructor,
                'lessons': course.lessons,
                'students': course.students,
                'status': course.status.capitalize(),
                'status_class': course.status_class,
                'progress': course.progress,
            }
            for course in courses[:5]
        ]

        recent_activities = [
            {
                'icon_type': 'emerald',
                'icon_svg': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
                'text': '<strong>New course</strong> added to the catalog',
                'time': '10 minutes ago',
            },
            {
                'icon_type': 'sky',
                'icon_svg': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>',
                'text': '<strong>Exam results</strong> published for new batch',
                'time': '35 minutes ago',
            },
            {
                'icon_type': 'amber',
                'icon_svg': '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
                'text': '<strong>12 students</strong> registered this week',
                'time': '1 hour ago',
            },
        ]

        top_performers = [
            {'name': 'Arjun Patel', 'course': 'Python Programming', 'score': 98},
            {'name': 'Riya Sharma', 'course': 'Data Structures', 'score': 95},
            {'name': 'Kabir Nair', 'course': 'ML Basics', 'score': 93},
        ]

    except OperationalError as exc:
        schema_error = True
        error_message = 'Database schema is not ready. Please run migrations with `python manage.py migrate`.'
        courses = []
        exams = []
        results = []
        students = []
        total_courses = 0
        total_exams = 0
        total_students = 0
        avg_score = 0
        upcoming_exams = []
        course_data = []
        recent_activities = []
        top_performers = []

    return render(request, 'admin_dashboard.html', {
        'active_page': 'dashboard',
        'page_title': 'Admin Dashboard',
        'page_subtitle': "Here's what's happening in your LMS today.",
        'total_students': total_students,
        'total_courses': total_courses,
        'total_exams': total_exams,
        'avg_score': avg_score,
        'courses': course_data,
        'upcoming_exams': upcoming_exams,
        'recent_activities': recent_activities,
        'top_performers': top_performers,
        'schema_error': schema_error,
        'error_message': error_message,
    })


def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_staff:
        return redirect('admin_dashboard')
    
    try:
        now = timezone.now()
        # Show all published exams to students; template will indicate status (upcoming/open/ended)
        exams = Exam.objects.select_related('course').filter(
            published=True,
        ).order_by('-created_at')
        student_results = Result.objects.filter(user=request.user).select_related('exam', 'exam__course')
        
        total_exams = exams.count()
        attempted_exams = student_results.count()
        avg_score = int(student_results.aggregate(avg_score=Avg('score'))['avg_score'] or 0)
        
    except OperationalError:
        exams = []
        student_results = []
        total_exams = 0
        attempted_exams = 0
        avg_score = 0
        now = timezone.now()

    return render(request, 'student_dashboard.html', {
        'page_title': 'My Dashboard',
        'page_subtitle': 'Track your progress and take exams.',
        'total_exams': total_exams,
        'attempted_exams': attempted_exams,
        'avg_score': avg_score,
        'exams': exams,
        'results': student_results,
        'now': now,
    })


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class CourseCreateView(StaffRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'course_form.html'
    success_url = reverse_lazy('courses')


class ExamCreateView(StaffRequiredMixin, CreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exam_form.html'
    success_url = reverse_lazy('exams')


class CourseUpdateView(StaffRequiredMixin, UpdateView):
    model = Course
    fields = ['title', 'instructor', 'lessons', 'status', 'content', 'pdf']
    template_name = 'course_content_form.html'
    success_url = reverse_lazy('courses')

    def form_valid(self, form):
        return super().form_valid(form)


def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('admin_dashboard')

    questions = exam.questions.prefetch_related('choices').all()
    return render(request, 'exam_detail.html', {
        'exam': exam,
        'questions': questions,
    })


def add_question(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        qform = QuestionForm(request.POST)
        if qform.is_valid():
            question = qform.save(commit=False)
            question.exam = exam
            question.save()
            formset = ChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Question saved successfully.')
                return redirect('exam_detail', exam_id=exam.id)
        else:
            formset = ChoiceFormSet(request.POST)
    else:
        qform = QuestionForm()
        formset = ChoiceFormSet()

    return render(request, 'question_form.html', {'exam': exam, 'qform': qform, 'formset': formset})


def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        qform = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if qform.is_valid() and formset.is_valid():
            qform.save()
            formset.save()
            messages.success(request, 'Question updated successfully.')
            return redirect('exam_detail', exam_id=exam.id)
    else:
        qform = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)

    return render(request, 'question_form.html', {
        'exam': exam,
        'qform': qform,
        'formset': formset,
        'editing': True,
    })


def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    exam = question.exam
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Admin access required.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('exam_detail', exam_id=exam.id)

    return render(request, 'question_delete.html', {'question': question, 'exam': exam})


def take_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, published=True)
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('login')

    questions = exam.questions.prefetch_related('choices').all()
    now = timezone.now()

    if exam.start_time and now < exam.start_time:
        messages.error(request, 'This exam has not started yet. It will open at %s.' % exam.start_time.strftime('%Y-%m-%d %H:%M'))
        return redirect('student_dashboard')
    if exam.end_time and now > exam.end_time:
        messages.error(request, 'This exam has already ended.')
        return redirect('student_dashboard')

    if request.method == 'POST':
        correct = 0
        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                try:
                    choice = Choice.objects.get(pk=selected_choice_id, question=question)
                    if choice.is_correct:
                        correct += 1
                except Choice.DoesNotExist:
                    pass

        score = 0.0
        total = questions.count()
        if total > 0:
            score = round((correct / total) * 100, 2)

        Result.objects.create(user=request.user, exam=exam, score=score)
        messages.success(request, f'Exam submitted. Your score is {score}%.')
        return redirect('student_dashboard')

    return render(request, 'take_exam.html', {
        'exam': exam,
        'questions': questions,
    })



def dashboard_view(request):
    """Redirect to appropriate dashboard based on user role"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('student_dashboard')


def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, 'course_detail.html', {
        'course': course,
    })


def courses_view(request):
    courses = Course.objects.all().order_by('title')
    return render(request, 'courses.html', {
        'active_page': 'courses',
        'page_title': 'All Courses',
        'page_subtitle': 'Browse active, pending, and closed courses.',
        'courses': courses,
        'total_courses': courses.count(),
    })


def exams_view(request):
    exams = Exam.objects.select_related('course').order_by('-created_at')
    return render(request, 'exams.html', {
        'active_page': 'exams',
        'page_title': 'Exams',
        'page_subtitle': 'View active and upcoming exams.',
        'exams': exams,
        'total_exams': exams.count(),
    })


def results_view(request):
    results = Result.objects.select_related('user', 'exam', 'exam__course').order_by('-completed_at')
    return render(request, 'results.html', {
        'active_page': 'results',
        'page_title': 'Results',
        'page_subtitle': 'Check student exam performance.',
        'results': results,
    })


def students_view(request):
    students = User.objects.filter(is_staff=False).order_by('username')
    return render(request, 'students.html', {
        'active_page': 'students',
        'page_title': 'Students',
        'page_subtitle': 'Manage enrolled learners.',
        'students': students,
        'total_students': students.count(),
    })


def schedule_view(request):
    return render(request, 'schedule.html', {
        'active_page': 'schedule',
        'page_title': 'Schedule',
        'page_subtitle': 'Review upcoming sessions and exams.',
    })


def reports_view(request):
    return render(request, 'reports.html', {
        'active_page': 'reports',
        'page_title': 'Reports',
        'page_subtitle': 'View LMS analytics and performance summaries.',
    })


def settings_view(request):
    return render(request, 'settings.html', {
        'active_page': 'settings',
        'page_title': 'Settings',
        'page_subtitle': 'Configure your LMS preferences.',
    })


def logout_view(request):
    logout(request)
    return redirect('login')
 