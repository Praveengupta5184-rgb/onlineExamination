from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Course, Exam, Question, Choice, Result
from django.db.models import Avg


def home(request):
    return render(request, "home.html")


def register_view(request):
    if request.method == "POST":
        # Template uses 'email' as the main identifier
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password1')
        password_confirm = request.POST.get('password2')

        if not email or not password:
            messages.error(request, "Email and Password are required")
            return render(request, "register.html")

        if password != password_confirm:
            messages.error(request, "Passwords do not match")
            return render(request, "register.html")

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists")
            return render(request, "register.html")

        # Default User model uses username, so we use email as username
        User.objects.create_user(
            username=email, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        messages.success(request, "Account created successfully! You can now log in.")
        return redirect('login')

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        # HTML input name is 'email'
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard_view')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "login.html")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    courses_list = Course.objects.all()
    results_qs = Result.objects.all()
    
    total_students = User.objects.filter(is_staff=False).count()
    total_courses = courses_list.count()
    total_exams = Exam.objects.count()
    
    avg_score_val = results_qs.aggregate(Avg('score'))['score__avg'] or 0
    avg_score = f"{int(avg_score_val)}%"

    upcoming_exams_qs = Exam.objects.select_related('course').order_by('-created_at')[:3]
    upcoming_exams = []
    for e in upcoming_exams_qs:
        upcoming_exams.append({
            'id': e.id,
            'day': e.created_at.strftime('%d'),
            'month': e.created_at.strftime('%b'),
            'title': e.title,
            'course': e.course.title,
            'duration': f"{e.duration_minutes} min"
        })

    top_performers_data = Result.objects.select_related('user', 'exam').order_by('-score')[:5]
    top_performers = []
    for r in top_performers_data:
        top_performers.append({
            'name': r.user.get_full_name() or r.user.username,
            'course': r.exam.course.title,
            'score': int(r.score)
        })

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_exams': total_exams,
        'avg_score': avg_score,
        'courses': courses_list[:5],
        'upcoming_exams': upcoming_exams,
        'top_performers': top_performers,
        'recent_activities': []
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def take_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.prefetch_related('choices').all()

    if request.method == "POST":
        score = 0
        total_q = questions.count()
        for q in questions:
            val = request.POST.get(f'question_{q.id}')
            if val and val.isdigit():
                try:
                    choice = Choice.objects.get(id=int(val), question=q)
                    if choice.is_correct:
                        score += 1
                except Choice.DoesNotExist:
                    pass

        # Optimization: Calculate the score in a single query instead of looping (Fixes N+1)
        selected_choice_ids = [
            int(v) for k, v in request.POST.items() 
            if k.startswith('question_') and v.isdigit()
        ]
        
        score = Choice.objects.filter(
            id__in=selected_choice_ids,
            is_correct=True,
            question__exam=exam
        ).count()
        
        final_score = (score / total_q * 100) if total_q > 0 else 0
        Result.objects.create(user=request.user, exam=exam, score=final_score)
        messages.success(request, f"Exam '{exam.title}' submitted! Score: {final_score:.1f}%")
        return redirect('dashboard_view')

    return render(request, 'take_exam.html', {'exam': exam, 'questions': questions})