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
    path('edit_word/<int:word_id>/', views.edit_word, name='edit_word'),
    path('delete_word/<int:word_id>/', views.delete_word, name='delete_word'),
    path('add_language/', views.add_language, name='add_language'),
    path('edit_language/<int:language_id>/', views.edit_language, name='edit_language'),
    path('delete_language/<int:language_id>/', views.delete_language, name='delete_language'),
    path('languages/', views.language_list, name='language_list'),
    path('quiz/', views.quiz_start, name='quiz_start'),
    path('quiz/question/', views.quiz_question, name='quiz_question'),
    path('quiz/result/', views.quiz_result, name='quiz_result'),
    path('quiz/clear-session/', views.clear_quiz_session, name='clear_quiz_session'),
    path('mistake_words/', views.mistake_words, name='mistake_words'),
    path('mark_as_learned/<int:mistake_id>/', views.mark_as_learned, name='mark_as_learned'),
]

