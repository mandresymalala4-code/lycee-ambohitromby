from django.urls import path
from . import views as v

urlpatterns = [
    path('paiements/<int:pk>/recu/', v.RecuPDF.as_view()),
    path('inscriptions/<int:pk>/recu/', v.RecuInscriptionPDF.as_view()),
    path('eleves/pdf/', v.ElevesPDF.as_view()),
    path('professeurs/pdf/', v.ProfesseursPDF.as_view()),
    path('emplois-du-temps/pdf/', v.EdtPDF.as_view()),
    path('mon-emploi-du-temps/pdf/', v.MonEdtPDF.as_view()),
    path('appels/pdf/', v.FeuilleAppelPDF.as_view()),
    path('absences/rapport/pdf/', v.RapportAbsencesPDF.as_view()),
    path('bulletins/<int:pk>/pdf/', v.BulletinPDF.as_view()),
    path('bulletins/classe/<int:pk>/pdf/', v.BulletinClassePDF.as_view()),
    path('statistiques/admin/', v.StatsAdmin.as_view()),
    path('statistiques/professeur/', v.StatsProfesseur.as_view()),
    path('notifications/', v.Notifications.as_view()),
]
