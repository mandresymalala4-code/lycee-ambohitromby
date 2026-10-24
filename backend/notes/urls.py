from django.urls import path
from . import views as v

urlpatterns = [
    path('notes/', v.NotesView.as_view()),
    path('resultats/', v.ResultatsView.as_view()),
    path('bulletins/decision/', v.DecisionView.as_view()),
    path('bulletins/decision-classe/', v.DecisionClasse.as_view()),
    path('bulletins/<int:pk>/', v.BulletinView.as_view()),
]
