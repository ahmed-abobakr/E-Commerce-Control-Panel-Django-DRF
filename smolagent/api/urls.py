from django.urls import path, include
from .views import run_function_view, run_chat_view

urlpatterns = [
    path('internal/run_function/', run_function_view, name='internal-ai-agent-run-function'),
    path('chat/', run_chat_view, name='run-chat'),
]