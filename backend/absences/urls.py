from django.urls import path
from . import views as v

urlpatterns = [
    path('appels/', v.AppelView.as_view()),
    path('appels/seances/', v.SeancesView.as_view()),
    path('appels/<int:pk>/', v.AppelView.as_view()),
    path('absences/recapitulatif/', v.RecapView.as_view()),
    path('absences/alertes/', v.AlertesView.as_view()),
]
