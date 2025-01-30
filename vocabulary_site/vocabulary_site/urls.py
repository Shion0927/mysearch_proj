from django.contrib import admin
from django.urls import path
from vocabulary import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.word_list, name='word_list'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('add_word/', views.add_word, name='add_word'),
    path('add_language/', views.add_language, name='add_language'),
    path('quiz/', views.quiz_start, name='quiz_start'),
    path('quiz/question/', views.quiz_question, name='quiz_question'),
    path('quiz/result/', views.quiz_result, name='quiz_result'),
    path('quiz/clear-session/', views.clear_quiz_session, name='clear_quiz_session'),
    path('mistake_words/', views.mistake_words, name='mistake_words'),
    path('mark_as_learned/<int:mistake_id>/', views.mark_as_learned, name='mark_as_learned'),
]

