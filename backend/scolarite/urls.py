from django.urls import path
from . import views as v

urlpatterns = [
    path('annees/', v.AnneesView.as_view()),
    path('annees/<int:pk>/trimestres/', v.TrimestresView.as_view()),
    path('trimestres/<int:pk>/cloture/', v.Cloture.as_view()),
    path('classes/', v.ClassesView.as_view()),
    path('classes/<int:pk>/', v.ClassesView.as_view()),
    path('eleves/', v.ElevesView.as_view()),
    path('eleves/recherche/', v.RechercheEleve.as_view()),
    path('eleves/<int:pk>/', v.ElevesView.as_view()),
    path('eleves/<int:pk>/photo/', v.PhotoEleve.as_view()),
    path('familles/par-contact/', v.FamilleParContact.as_view()),
    path('inscriptions/', v.InscriptionsView.as_view()),
    path('inscriptions/<int:pk>/', v.InscriptionsView.as_view()),
    path('paiements/', v.Paiements.as_view()),
    path('paiements/<int:pk>/', v.Paiements.as_view()),
    path('matieres/', v.MatieresView.as_view()),
    path('matieres/copier-annee-precedente/', v.CopierMatieres.as_view()),
    path('matieres/<int:pk>/', v.MatieresView.as_view()),
    path('emplois-du-temps/', v.CoursView.as_view()),
    path('emplois-du-temps/<int:pk>/', v.CoursView.as_view()),
    path('mon-emploi-du-temps/', v.MonEmploiDuTemps.as_view()),
]
