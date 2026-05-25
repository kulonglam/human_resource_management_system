from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Survey, SurveyQuestion, SurveyResponse
from .forms import SurveyForm, SurveyQuestionForm, SurveyResponseForm
from django.utils import timezone

@login_required
def survey_list(request):
    surveys = Survey.objects.filter(status='active', end_date__gte=timezone.now().date())
    return render(request, 'surveys/list.html', {'surveys': surveys})

@login_required
def survey_detail(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.all().order_by('order')
    return render(request, 'surveys/detail.html', {'survey': survey, 'questions': questions})

@login_required
def survey_take(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    if request.method == 'POST':
        questions = survey.questions.all()
        for question in questions:
            response_data = request.POST.get(f'question_{question.id}')
            if response_data or not question.is_required:
                SurveyResponse.objects.create(
                    survey=survey,
                    respondent=request.user.employee if not survey.is_anonymous else None,
                    question=question,
                    response_text=response_data if question.question_type == 'text' else '',
                    response_rating=int(response_data) if question.question_type == 'rating' else None,
                    response_selected=response_data if question.question_type in ['multiple_choice', 'checkbox'] else ''
                )
        messages.success(request, 'Survey submitted successfully')
        return redirect('survey_list')
    questions = survey.questions.all().order_by('order')
    return render(request, 'surveys/take.html', {'survey': survey, 'questions': questions})

@login_required
def survey_create(request):
    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.created_by = request.user.employee
            survey.save()
            messages.success(request, 'Survey created successfully')
            return redirect('survey_detail', pk=survey.pk)
    else:
        form = SurveyForm()
    return render(request, 'surveys/form.html', {'form': form, 'title': 'Create Survey'})

@login_required
def survey_results(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.all().order_by('order')
    responses = survey.responses.all()
    return render(request, 'surveys/results.html', {'survey': survey, 'questions': questions, 'responses': responses})
