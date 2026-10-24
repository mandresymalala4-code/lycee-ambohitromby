from django.db import models
from django.db.models import Q


class Note(models.Model):
    inscription = models.ForeignKey('scolarite.Inscription', on_delete=models.PROTECT, related_name='notes')
    matiere = models.ForeignKey('scolarite.Matiere', on_delete=models.PROTECT, related_name='notes')
    trimestre = models.ForeignKey('scolarite.Trimestre', on_delete=models.PROTECT, related_name='notes')
    ds = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    examen = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    saisi_par = models.ForeignKey('comptes.Utilisateur', null=True, on_delete=models.SET_NULL, related_name='+')
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'note'
        constraints = [models.UniqueConstraint(fields=['inscription', 'matiere', 'trimestre'], name='uq_note'),
                       models.CheckConstraint(condition=(Q(ds__isnull=True) | Q(ds__gte=0, ds__lte=20)), name='chk_ds'),
                       models.CheckConstraint(condition=(Q(examen__isnull=True) | Q(examen__gte=0, examen__lte=20)), name='chk_examen')]


class ResultatTrimestre(models.Model):
    inscription = models.ForeignKey('scolarite.Inscription', on_delete=models.CASCADE, related_name='resultats')
    trimestre = models.ForeignKey('scolarite.Trimestre', on_delete=models.CASCADE, related_name='resultats')
    total_coefficients = models.PositiveIntegerField(default=0)
    total_points = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    moyenne = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rang = models.PositiveIntegerField(null=True, blank=True)
    effectif_classe = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'resultat_trimestre'
        constraints = [models.UniqueConstraint(fields=['inscription', 'trimestre'], name='uq_resultat')]


class DecisionConseil(models.Model):
    inscription = models.ForeignKey('scolarite.Inscription', on_delete=models.CASCADE, related_name='decisions')
    trimestre = models.ForeignKey('scolarite.Trimestre', on_delete=models.CASCADE, related_name='decisions')
    texte = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'decision_conseil'
        constraints = [models.UniqueConstraint(fields=['inscription', 'trimestre'], name='uq_decision')]
