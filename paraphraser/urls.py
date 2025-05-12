from django.urls import path
from . import views

urlpatterns = [
    path('api/paraphrase/', views.paraphrase_mcq, name='paraphrase_mcq'),
] 