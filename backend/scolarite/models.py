from datetime import time
from django.db import models
from django.db.models import Q


class AnneeScolaire(models.Model):
    annee_debut = models.PositiveSmallIntegerField(unique=True)
    annee_fin = models.PositiveSmallIntegerField()
    libelle = models.CharField(max_length=15)
    courante = models.BooleanField(default=False)
    classes_initialisees = models.BooleanField(default=False)

    class Meta:
        db_table = 'annee_scolaire'
        ordering = ['annee_debut']
        constraints = [models.CheckConstraint(condition=Q(annee_debut__gte=2020, annee_debut__lte=2045), name='chk_annee_bornes')]

    def __str__(self):
        return self.libelle


class Trimestre(models.Model):
    annee = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='trimestres')
    numero = models.PositiveSmallIntegerField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    cloture = models.BooleanField(default=False)

    class Meta:
        db_table = 'trimestre'
        ordering = ['annee', 'numero']
        constraints = [models.UniqueConstraint(fields=['annee', 'numero'], name='uq_trimestre'),
                       models.CheckConstraint(condition=Q(numero__gte=1, numero__lte=3), name='chk_trim_num')]


class Classe(models.Model):
    annee = models.ForeignKey(AnneeScolaire, on_delete=models.PROTECT, related_name='classes')
    nom = models.CharField(max_length=50)
    droit_inscription = models.PositiveIntegerField(default=0)
    caisse_soutien = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'classe'
        constraints = [models.UniqueConstraint(fields=['annee', 'nom'], name='uq_classe_annee_nom'),
                       models.CheckConstraint(condition=Q(droit_inscription__lte=10000000, caisse_soutien__lte=10000000), name='chk_classe_montants')]

    @property
    def total(self):
        return self.droit_inscription + self.caisse_soutien


class Famille(models.Model):
    pere_nom = models.CharField(max_length=100, blank=True, default='')
    pere_prenoms = models.CharField(max_length=100, blank=True, default='')
    mere_nom = models.CharField(max_length=100, blank=True, default='')
    mere_prenoms = models.CharField(max_length=100, blank=True, default='')
    contact_parent = models.CharField(max_length=10, unique=True)
    adresse_parents = models.CharField(max_length=120)
    tuteur_nom = models.CharField(max_length=100, blank=True, default='')
    tuteur_prenoms = models.CharField(max_length=100, blank=True, default='')
    tuteur_contact = models.CharField(max_length=10, blank=True, default='')

    class Meta:
        db_table = 'famille'


def _photo_path(instance, filename):
    from comptes.models import upload_photo
    return upload_photo(instance, filename)


class Eleve(models.Model):
    matricule = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10)
    adresse = models.CharField(max_length=120)
    photo = models.ImageField(upload_to=_photo_path, null=True, blank=True)
    observation = models.CharField(max_length=255, blank=True, default='')
    famille = models.ForeignKey(Famille, on_delete=models.PROTECT, related_name='eleves')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eleve'
        indexes = [models.Index(fields=['nom', 'prenoms'])]


class Inscription(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.PROTECT, related_name='inscriptions')
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name='inscriptions')
    annee = models.ForeignKey(AnneeScolaire, on_delete=models.PROTECT, related_name='inscriptions')
    statut = models.CharField(max_length=8, default='ACTIVE', choices=[('ACTIVE', 'Active'), ('ANNULEE', 'Annulée')])
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inscription'
        constraints = [models.UniqueConstraint(fields=['eleve', 'annee'], name='uq_inscription_eleve_annee')]


MODES_PAIEMENT = ['Espèces', 'MVola', 'Orange Money', 'Airtel Money', 'Chèque/Virement']


class Paiement(models.Model):
    inscription = models.OneToOneField(Inscription, null=True, blank=True, on_delete=models.SET_NULL, related_name='paiement')
    annee = models.ForeignKey(AnneeScolaire, on_delete=models.PROTECT, related_name='paiements')
    numero_recu = models.CharField(max_length=20, unique=True)
    droit_inscription = models.PositiveIntegerField()
    caisse_soutien = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    mode_paiement = models.CharField(max_length=30)
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=6, default='VALIDE', choices=[('VALIDE', 'Valide'), ('ANNULE', 'Annulé')])
    enregistre_par = models.ForeignKey('comptes.Utilisateur', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    eleve_matricule = models.CharField(max_length=10)
    eleve_nom = models.CharField(max_length=100)
    eleve_prenoms = models.CharField(max_length=100)
    classe_nom = models.CharField(max_length=50)

    class Meta:
        db_table = 'paiement'


class Matiere(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name='matieres')
    discipline = models.ForeignKey('comptes.Discipline', on_delete=models.PROTECT, related_name='matieres')
    coefficient = models.PositiveSmallIntegerField()
    professeur = models.ForeignKey('comptes.Professeur', null=True, blank=True, on_delete=models.PROTECT, related_name='matieres')

    class Meta:
        db_table = 'matiere'
        constraints = [models.UniqueConstraint(fields=['classe', 'discipline'], name='uq_matiere_classe_disc'),
                       models.CheckConstraint(condition=Q(coefficient__gte=1, coefficient__lte=6), name='chk_coef')]

    @property
    def nom(self):
        return self.discipline.nom


class Cours(models.Model):
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cours')
    jour = models.PositiveSmallIntegerField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    salle = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        db_table = 'cours'
        indexes = [models.Index(fields=['matiere', 'jour'])]
        constraints = [models.CheckConstraint(condition=Q(jour__gte=1, jour__lte=5, heure_debut__gte=time(7, 0),
                                                         heure_fin__lte=time(18, 0), heure_debut__lt=models.F('heure_fin')),
                                              name='chk_cours_horaire')]

    @property
    def duree(self):
        return (self.heure_fin.hour * 60 + self.heure_fin.minute - self.heure_debut.hour * 60 - self.heure_debut.minute) / 60
