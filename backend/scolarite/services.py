from datetime import date
from django.db.models import Count, Q
from .models import AnneeScolaire, Classe, Eleve, Inscription, Paiement, Trimestre

CLASSES_DEFAUT = [('Seconde', 50000), ('1ère L', 60000), ('1ère S', 60000), ('1ère OSE', 60000),
                  ('Terminale L', 70000), ('Terminale S', 70000), ('Terminale OSE', 70000)]


def debut_annee_pour(d=None):
    d = d or date.today()
    return d.year if d.month >= 9 else d.year - 1


def libelle(debut):
    return f'{debut} - {debut + 1}'


def trimestres_defaut(debut):
    return [(1, date(debut, 10, 1), date(debut, 12, 31)), (2, date(debut + 1, 1, 1), date(debut + 1, 3, 31)),
            (3, date(debut + 1, 4, 1), date(debut + 1, 6, 30))]


def ensure_annee(debut):
    a, created = AnneeScolaire.objects.get_or_create(annee_debut=debut, defaults={'annee_fin': debut + 1, 'libelle': libelle(debut)})
    if not a.trimestres.exists():
        for n, d1, d2 in trimestres_defaut(debut):
            Trimestre.objects.get_or_create(annee=a, numero=n, defaults={'date_debut': d1, 'date_fin': d2})
    return a


def ensure_toutes_annees():
    existantes = set(AnneeScolaire.objects.values_list('annee_debut', flat=True))
    for y in range(2020, 2046):
        if y not in existantes:
            ensure_annee(y)
    if not AnneeScolaire.objects.filter(courante=True).exists():
        AnneeScolaire.objects.filter(annee_debut=debut_annee_pour()).update(courante=True)


def annee_courante():
    ensure_toutes_annees()
    return AnneeScolaire.objects.filter(courante=True).first() or ensure_annee(debut_annee_pour())


def ensure_classes(annee):
    if not annee.classes_initialisees:
        for nom, droit in CLASSES_DEFAUT:
            Classe.objects.get_or_create(annee=annee, nom=nom, defaults={'droit_inscription': droit, 'caisse_soutien': 0})
        annee.classes_initialisees = True
        annee.save(update_fields=['classes_initialisees'])


def prochain_matricule(debut):
    last = Eleve.objects.filter(matricule__startswith=f'{debut}-').order_by('-matricule').first()
    n = int(last.matricule[-4:]) + 1 if last else 1
    return f'{debut}-{n:04d}'


def prochain_recu(annee):
    last = Paiement.objects.filter(annee=annee).order_by('-numero_recu').first()
    n = int(last.numero_recu.split('-')[-1]) + 1 if last else 1
    return f'REC-{annee.annee_debut}-{n:05d}'


def inscriptions_filtrees(params, ordre='recent'):
    qs = Inscription.objects.filter(statut='ACTIVE').select_related('eleve', 'classe', 'annee', 'eleve__famille')
    if params.get('annee'):
        qs = qs.filter(annee_id=params['annee'])
    if params.get('classe'):
        qs = qs.filter(classe_id=params['classe'])
    if params.get('sexe'):
        qs = qs.filter(eleve__sexe=params['sexe'])
    q = (params.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(eleve__nom__icontains=q) | Q(eleve__prenoms__icontains=q) | Q(eleve__matricule__icontains=q))
    if ordre == 'alpha':
        return qs.order_by('eleve__nom', 'eleve__prenoms')
    if params.get('classe') and ordre == 'matricule':
        return qs.order_by('eleve__matricule')
    return qs.order_by('-id')


def effectifs(annee_id):
    return dict(Inscription.objects.filter(annee_id=annee_id, statut='ACTIVE').values_list('classe_id').annotate(n=Count('id')))


def classe_effectif(classe):
    return Inscription.objects.filter(classe=classe, statut='ACTIVE').count()


def trimestre_courant(annee, today=None):
    today = today or date.today()
    ts = list(annee.trimestres.order_by('numero'))
    for t in ts:
        if t.date_debut <= today <= t.date_fin:
            return t
    passes = [t for t in ts if t.date_fin < today]
    return passes[-1] if passes else ts[0]


def trimestre_de_date(annee, d):
    return annee.trimestres.filter(date_debut__lte=d, date_fin__gte=d).first()
