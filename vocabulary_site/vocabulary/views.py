import random
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from .models import Word, Quiz, MistakeWord, Language
from django.core.paginator import Paginator

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .forms import WordForm, LanguageForm

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
    return render(request, 'registration/register.html', {'form': form})

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
        words = words.filter(Q(word__icontains=query) | Q(meaning__icontains(query)))
    if language:
        words = words.filter(language__name=language)

    # 総検索結果数を計算
    total_words_count = words.count()

    # ページネーション
    paginator = Paginator(words, 10)
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
def quiz_start(request):
    languages = Language.objects.filter(word__user=request.user).distinct()
    language_word_counts = {
        lang.id: Word.objects.filter(user=request.user, language=lang).count()
        for lang in languages
    }

    if request.method == 'POST':
        language_id = request.POST.get('language')
        num_questions = int(request.POST.get('num_questions', 10))
        
        words = list(Word.objects.filter(user=request.user, language_id=language_id))
        if len(words) < num_questions:
            messages.error(request, f"選択した言語の単語数が{num_questions}個未満です。全ての単語を使用してクイズを作成します。")
            num_questions = len(words)
        
        if num_questions == 0:
            messages.error(request, "選択した言語に単語がありません。")
            return redirect('quiz_start')

        quiz_words = random.sample(words, num_questions)
        quiz_types = [random.choice(['word', 'meaning']) for _ in range(num_questions)]
        
        quiz = Quiz.objects.create(
            user=request.user,
            language_id=language_id,
            total_questions=num_questions
        )
        
        request.session['quiz_words'] = [word.id for word in quiz_words]
        request.session['quiz_types'] = quiz_types
        request.session['current_question'] = 0
        request.session['correct_answers'] = 0
        request.session['quiz_id'] = quiz.id

        return redirect('quiz_question')

    context = {
        'languages': languages,
        'language_word_counts': language_word_counts,
    }
    return render(request, 'vocabulary/quiz_start.html', context)

@login_required
def quiz_question(request):
    quiz_words = request.session.get('quiz_words', [])
    quiz_types = request.session.get('quiz_types', [])
    current_question = request.session.get('current_question', 0)
    quiz_id = request.session.get('quiz_id')
    
    if current_question >= len(quiz_words):
        return redirect('quiz_result')
    
    word = Word.objects.get(id=quiz_words[current_question])
    question_type = quiz_types[current_question]
    
    if request.method == 'POST':
        user_answer = next((value for key, value in request.POST.items() if key.startswith('answer')), '').strip().lower()
        correct_answer = word.word.lower() if question_type == 'meaning' else word.meaning.lower()
        
        if user_answer == correct_answer:
            request.session['correct_answers'] = request.session.get('correct_answers', 0) + 1
            messages.success(request, "正解です！")
        else:
            messages.error(request, f"不正解です。正解は '{correct_answer}' でした。")
            quiz = Quiz.objects.get(id=quiz_id)
            MistakeWord.objects.get_or_create(user=request.user, word=word, quiz=quiz)
        
        request.session['current_question'] = current_question + 1
        return redirect('quiz_question')
    
    return render(request, 'vocabulary/quiz_question.html', {
        'word': word,
        'question_type': question_type,
        'question_number': current_question + 1,
        'total_questions': len(quiz_words)
    })

@login_required
def quiz_result(request):
    quiz_id = request.session.get('quiz_id')
    
    if not quiz_id:
        messages.error(request, "クイズセッションが見つかりません。新しいクイズを開始してください。")
        return redirect('quiz_start')
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
    except Quiz.DoesNotExist:
        messages.error(request, "クイズが見つかりません。新しいクイズを開始してください。")
        return redirect('quiz_start')
    
    correct_answers = request.session.get('correct_answers', 0)
    total_questions = quiz.total_questions
    
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # クイズ結果を表示した後にセッションデータをクリア
    request.session['quiz_completed'] = True
    
    context = {
        'correct_answers': correct_answers,
        'total_questions': total_questions,
        'quiz_id': quiz_id,
        'score_percentage': round(score_percentage, 2)
    }
    
    return render(request, 'vocabulary/quiz_result.html', context)

@login_required
def clear_quiz_session(request):
    keys_to_remove = ['quiz_words', 'quiz_types', 'current_question', 'correct_answers', 'quiz_id', 'quiz_completed']
    for key in keys_to_remove:
        request.session.pop(key, None)
    return redirect('quiz_start')

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


@login_required
def edit_language(request, language_id):
    language = get_object_or_404(Language, id=language_id)
    if request.method == 'POST':
        form = LanguageForm(request.POST, instance=language)
        if form.is_valid():
            form.save()
            messages.success(request, '言語が更新されました。')
            return redirect('word_list')
    else:
        form = LanguageForm(instance=language)
    return render(request, 'vocabulary/edit_language.html', {'form': form, 'language': language})

@login_required
def delete_language(request, language_id):
    language = get_object_or_404(Language, id=language_id)
    if request.method == 'POST':
        language.delete()
        messages.success(request, '言語が削除されました。')
        return redirect('word_list')
    return render(request, 'vocabulary/delete_language.html', {'language': language})

@login_required
def language_list(request):
    languages = Language.objects.annotate(word_count=Count('word'))
    return render(request, 'vocabulary/language_list.html', {'languages': languages})

@login_required
def edit_word(request, word_id):
    word = get_object_or_404(Word, id=word_id, user=request.user)
    if request.method == 'POST':
        form = WordForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            messages.success(request, '単語が更新されました。')
            return redirect('word_list')
    else:
        form = WordForm(instance=word)
    return render(request, 'vocabulary/edit_word.html', {'form': form, 'word': word})

@login_required
def delete_word(request, word_id):
    word = get_object_or_404(Word, id=word_id, user=request.user)
    if request.method == 'POST':
        word.delete()
        messages.success(request, '単語が削除されました。')
        return redirect('word_list')
    return render(request, 'vocabulary/delete_word.html', {'word': word})
