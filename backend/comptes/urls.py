from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views as v

urlpatterns = [
    path('auth/login/', v.Login.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/logout/', v.Logout.as_view()),
    path('auth/register-professeur/', v.RegisterProfesseur.as_view()),
    path('auth/mot-de-passe-oublie/', v.MotDePasseOublie.as_view()),
    path('disciplines/', v.DisciplinesView.as_view()),
    path('professeurs/', v.ProfesseursView.as_view()),
    path('professeurs/en-attente/', v.ProfsEnAttente.as_view()),
    path('professeurs/<int:pk>/', v.ProfesseursView.as_view()),
    path('professeurs/<int:pk>/valider/', v.ProfAction.as_view(action='valider')),
    path('professeurs/<int:pk>/refuser/', v.ProfAction.as_view(action='refuser')),
    path('professeurs/<int:pk>/suspendre/', v.ProfAction.as_view(action='suspendre')),
    path('professeurs/<int:pk>/reactiver/', v.ProfAction.as_view(action='reactiver')),
    path('profil/', v.ProfilView.as_view()),
    path('parametres/', v.ParametresView.as_view()),
]
