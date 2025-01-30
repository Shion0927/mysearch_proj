from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import Word, Language, Quiz, MistakeWord
from .forms import WordForm, LanguageForm
from django.contrib import messages 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import random

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # ユーザーを自動的にログイン
            messages.success(request, 'アカウントが正常に作成されました。ようこそ！') # Added success message
            return redirect('word_list')
    else:
        form = UserCreationForm()
    return render(request, 'vocabulary/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('word_list')
    return render(request, 'vocabulary/login.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def word_list(request):
    query = request.GET.get('query')
    language = request.GET.get('language')
    words = Word.objects.filter(user=request.user)

    if query:
        words = words.filter(Q(word__icontains=query) | Q(meaning__icontains=query))
    if language:
        words = words.filter(language__name=language)

    # 総検索結果数を計算
    total_words_count = words.count()

    # ページネーション
    paginator = Paginator(words, 10)  # 1ページあたり10件表示
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    languages = Language.objects.filter(word__user=request.user).distinct()
    language_word_counts = {lang.id: Word.objects.filter(user=request.user, language=lang).count() for lang in languages}
    
    context = {
        'words': page_obj,
        'query': query,
        'languages': languages,
        'current_language': language,
        'total_words_count': total_words_count,  # 総検索結果数をコンテキストに追加
        'language_word_counts': language_word_counts
    }
    
    return render(request, 'vocabulary/word_list.html', context)

@login_required
def add_word(request):
    if request.method == 'POST':
        form = WordForm(request.POST)
        if form.is_valid():
            word = form.save(commit=False)
            word.user = request.user
            word.save()
            return redirect('word_list')
    else:
        form = WordForm()
    return render(request, 'vocabulary/add_word.html', {'form': form})

@login_required
def add_language(request):
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('word_list')
    else:
        form = LanguageForm()
    return render(request, 'vocabulary/add_language.html', {'form': form})

@login_required
def quiz(request):
    if request.method == 'POST':
        language_id = request.POST.get('language')
        num_questions = int(request.POST.get('num_questions', 10))
        language = Language.objects.get(id=language_id)
        words = list(Word.objects.filter(user=request.user, language=language).order_by('-created_at'))
        
        if len(words) < num_questions:
            messages.error(request, f"選択した言語の単語数が{num_questions}個未満です。全ての単語を使用してクイズを作成します。")
            num_questions = len(words)
        
        quiz_words = random.sample(words, num_questions)
        request.session['quiz_words'] = [word.id for word in quiz_words]
        request.session['current_question'] = 0
        request.session['correct_answers'] = 0
        
        # クイズオブジェクトを作成し、セッションにIDを保存
        quiz = Quiz.objects.create(user=request.user, language=language, total_questions=num_questions)
        request.session['quiz_id'] = quiz.id
        
        return redirect('quiz_question')
    
    languages = Language.objects.filter(word__user=request.user).distinct()
    language_word_counts = {lang.id: Word.objects.filter(user=request.user, language=lang).count() for lang in languages}
    return render(request, 'vocabulary/quiz_start.html', {
        'languages': languages,
        'language_word_counts': language_word_counts
    })

@login_required
def quiz_question(request):
    quiz_words = request.session.get('quiz_words', [])
    current_question = request.session.get('current_question', 0)
    quiz_id = request.session.get('quiz_id')
    
    if current_question >= len(quiz_words):
        return redirect('quiz_result')
    
    word = Word.objects.get(id=quiz_words[current_question])
    
    if request.method == 'POST':
        user_answer = request.POST.get('answer', '').strip().lower()
        correct_answer = word.word.lower()
        
        if user_answer == correct_answer:
            request.session['correct_answers'] = request.session.get('correct_answers', 0) + 1
            messages.success(request, "正解です！")
        else:
            messages.error(request, f"不正解です。正解は '{word.word}' でした。")
            # 間違えた単語を保存
            quiz = Quiz.objects.get(id=quiz_id)
            MistakeWord.objects.get_or_create(user=request.user, word=word, quiz=quiz)
        
        request.session['current_question'] = current_question + 1
        return redirect('quiz_question')
    
    return render(request, 'vocabulary/quiz_question.html', {'word': word, 'question_number': current_question + 1, 'total_questions': len(quiz_words)})

@login_required
def quiz_result(request):
    correct_answers = request.session.get('correct_answers', 0)
    total_questions = len(request.session.get('quiz_words', []))
    score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
    
    quiz = Quiz.objects.create(
        user=request.user,
        language=Word.objects.get(id=request.session['quiz_words'][0]).language,
        score=score,
        total_questions=total_questions
    )
    
    # セッションのクリーンアップ
    for key in ['quiz_words', 'current_question', 'correct_answers', 'quiz_id']:
        if key in request.session:
            del request.session[key]
    
    return render(request, 'vocabulary/quiz_result.html', {
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': total_questions
    })

@login_required
def mistake_words(request):
    mistakes = MistakeWord.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'vocabulary/mistake_words.html', {'mistakes': mistakes})

@login_required
def mark_as_learned(request, mistake_id):
    mistake = get_object_or_404(MistakeWord, id=mistake_id, user=request.user)
    mistake.delete()
    messages.success(request, f"'{mistake.word.word}'を覚えた単語としてマークしました。")
    return redirect('mistake_words')

