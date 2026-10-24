from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('api/', include('comptes.urls')),
    path('api/', include('scolarite.urls')),
    path('api/', include('absences.urls')),
    path('api/', include('notes.urls')),
    path('api/', include('documents.urls')),
    # Photos et logo (noms aléatoires) : servis aussi en production, sans configuration supplémentaire de l'hébergeur
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

handler400 = 'comptes.errors.json_400'
handler403 = 'comptes.errors.json_403'
handler404 = 'comptes.errors.json_404'
handler500 = 'comptes.errors.json_500'
