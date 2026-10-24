from django.db import models
from django.db.models import Q


class Appel(models.Model):
    classe = models.ForeignKey('scolarite.Classe', on_delete=models.PROTECT, related_name='appels')
    matiere = models.ForeignKey('scolarite.Matiere', on_delete=models.PROTECT, related_name='appels')
    cours = models.ForeignKey('scolarite.Cours', null=True, blank=True, on_delete=models.SET_NULL, related_name='appels')
    date = models.DateField()
    duree_heures = models.DecimalField(max_digits=4, decimal_places=2)
    saisi_par = models.ForeignKey('comptes.Utilisateur', null=True, on_delete=models.SET_NULL, related_name='+')
    date_saisie = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appel'
        constraints = [models.UniqueConstraint(fields=['matiere', 'date', 'cours'], name='uq_appel')]
        indexes = [models.Index(fields=['classe', 'date'])]


class Absence(models.Model):
    STATUTS = [('PRESENT', 'Présent'), ('ABSENT', 'Absent'), ('RETARD', 'Retard'), ('JUSTIFIEE', 'Absence justifiée')]
    appel = models.ForeignKey(Appel, on_delete=models.CASCADE, related_name='lignes')
    inscription = models.ForeignKey('scolarite.Inscription', on_delete=models.PROTECT, related_name='absences')
    statut = models.CharField(max_length=10, choices=STATUTS, default='PRESENT')
    heures_absence = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    motif = models.CharField(max_length=255, blank=True, default='')
    observation = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'absence'
        constraints = [models.UniqueConstraint(fields=['appel', 'inscription'], name='uq_absence'),
                       models.CheckConstraint(condition=Q(heures_absence__gte=0), name='chk_heures')]
