import uuid
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


def upload_photo(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'photos/{uuid.uuid4().hex}.{ext}'


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        u = self.model(email=email.lower(), **extra)
        u.set_password(password)
        u.save(using=self._db)
        return u


class Utilisateur(AbstractBaseUser):
    ROLES = [('ADMIN', 'Administrateur'), ('PROFESSEUR', 'Professeur')]
    STATUTS = [('EN_ATTENTE', 'En attente'), ('VALIDE', 'Validé'), ('REFUSE', 'Refusé'), ('SUSPENDU', 'Suspendu')]
    email = models.EmailField(max_length=150, unique=True)
    role = models.CharField(max_length=12, choices=ROLES)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True)
    sexe = models.CharField(max_length=10)
    adresse = models.CharField(max_length=120)
    telephone = models.CharField(max_length=10, unique=True)
    photo = models.ImageField(upload_to=upload_photo, null=True, blank=True)
    statut = models.CharField(max_length=12, choices=STATUTS, default='EN_ATTENTE')
    theme = models.CharField(max_length=6, choices=[('CLAIR', 'Clair'), ('SOMBRE', 'Sombre')], default='CLAIR')
    doit_changer_mdp = models.BooleanField(default=False)
    tentatives_echec = models.PositiveSmallIntegerField(default=0)
    verrouille_jusqu_a = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    date_creation = models.DateTimeField(default=timezone.now)
    annee_preferee = models.PositiveSmallIntegerField(null=True, blank=True)
    motif_refus = models.CharField(max_length=255, blank=True, default='')

    objects = UtilisateurManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'utilisateur'
        indexes = [models.Index(fields=['role', 'statut'])]

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'.strip()

    @property
    def est_admin(self):
        return self.role == 'ADMIN'


class Discipline(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'discipline'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Professeur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='professeur')
    code = models.CharField(max_length=12, unique=True, null=True, blank=True)
    cin = models.CharField(max_length=14, unique=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.PROTECT, related_name='professeurs')
    observation = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'professeur'


class Etablissement(models.Model):
    nom = models.CharField(max_length=100, default='Lycée Ambohitromby')
    adresse = models.CharField(max_length=120, default='Ambohitromby, Antananarivo, Madagascar')
    telephone = models.CharField(max_length=10, default='0340000000')
    email = models.EmailField(max_length=150, blank=True, default='contact@ambohitromby.mg')
    logo = models.ImageField(upload_to=upload_photo, null=True, blank=True)

    class Meta:
        db_table = 'etablissement'

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(pk=1)[0]


class JournalAudit(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    action = models.CharField(max_length=60)
    entite = models.CharField(max_length=60, blank=True, default='')
    entite_id = models.CharField(max_length=40, blank=True, default='')
    details = models.TextField(blank=True, default='')
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'journal_audit'
        indexes = [models.Index(fields=['date']), models.Index(fields=['utilisateur'])]


class DonneeDemo(models.Model):
    """Repère les lignes créées par charger_demo (effacer_demo)."""
    modele = models.CharField(max_length=40)
    objet_id = models.BigIntegerField()

    class Meta:
        db_table = 'donnee_demo'
        unique_together = [('modele', 'objet_id')]


def audit(user, action, entite='', entite_id='', details=''):
    JournalAudit.objects.create(utilisateur=user if getattr(user, 'pk', None) else None, action=action,
                                entite=entite, entite_id=str(entite_id), details=str(details)[:2000])
