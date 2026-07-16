from django.urls import path
from . import views

urlpatterns = [
    path('ai_assistant/', views.gemini_chat, name='gemini_chat'),
]