from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from django.db.models import Count, Sum
from comptes.errors import ApiError
from .models import DecisionConseil, Note, ResultatTrimestre

Q2 = Decimal('0.01')
BAREME = [(5, 'Très insuffisant'), (8, 'Insuffisant'), (10, 'Médiocre'), (12, 'Passable'), (14, 'Assez bien'), (16, 'Bien'), (18, 'Très bien')]


def r2(x):
    return Decimal(x).quantize(Q2, rounding=ROUND_HALF_UP)


def fl(x):
    return None if x is None else float(x)


def note_trimestrielle(ds, ex):
    if ds is None or ex is None:
        return None
    return r2((Decimal(ds) + Decimal(ex)) / 2)


def appreciation(n):
    if n is None:
        return ''
    for seuil, lib in BAREME:
        if n < seuil:
            return lib
    return 'Excellent'


def parse_note(v):
    """None si vide ; Decimal 0..20 (2 décimales max) sinon ValueError."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        d = Decimal(str(v).strip().replace(',', '.'))
    except InvalidOperation:
        raise ValueError('La note doit être comprise entre 0 et 20.')
    if not d.is_finite() or d < 0 or d > 20 or d.as_tuple().exponent < -2:
        raise ValueError('La note doit être comprise entre 0 et 20.')
    return d.quantize(Q2)


def recalculer(classe, trimestre):
    """Recalcule moyennes et rangs (ex æquo : 1,2,2,4) de la classe pour le trimestre."""
    from scolarite.models import Inscription, Matiere
    ins_ids = list(Inscription.objects.filter(classe=classe, statut='ACTIVE').values_list('id', flat=True))
    coefs = dict(Matiere.objects.filter(classe=classe).values_list('id', 'coefficient'))
    agg = {}
    for n in Note.objects.filter(inscription_id__in=ins_ids, trimestre=trimestre, ds__isnull=False, examen__isnull=False):
        nt = note_trimestrielle(n.ds, n.examen)
        c = coefs.get(n.matiere_id)
        if c is None:
            continue
        a = agg.setdefault(n.inscription_id, [0, Decimal(0)])
        a[0] += c
        a[1] += nt * c
    classes = []
    for iid, (tc, tp) in agg.items():
        classes.append((iid, tc, r2(tp), r2(tp / tc)))
    classes.sort(key=lambda x: -x[3])
    effectif = len(classes)
    rang_prec, moy_prec = 0, None
    ResultatTrimestre.objects.filter(inscription_id__in=ins_ids, trimestre=trimestre).exclude(inscription_id__in=agg.keys()).delete()
    for pos, (iid, tc, tp, moy) in enumerate(classes, start=1):
        rang = rang_prec if moy == moy_prec else pos
        rang_prec, moy_prec = rang, moy
        ResultatTrimestre.objects.update_or_create(inscription_id=iid, trimestre=trimestre, defaults={
            'total_coefficients': tc, 'total_points': tp, 'moyenne': moy, 'rang': rang, 'effectif_classe': effectif})


def bulletin_data(ins, trimestre):
    """Données complètes d'un bulletin (§9.2)."""
    from absences.services import agregats
    from scolarite.models import Matiere
    classe = ins.classe
    matieres = list(Matiere.objects.filter(classe=classe).select_related('discipline').order_by('discipline__nom'))
    notes = {n.matiere_id: n for n in Note.objects.filter(inscription=ins, trimestre=trimestre)}
    lignes, manquantes = [], 0
    for m in matieres:
        n = notes.get(m.id)
        nt = note_trimestrielle(n.ds, n.examen) if n else None
        if nt is None:
            manquantes += 1
        lignes.append({'matiere': m.discipline.nom, 'coefficient': m.coefficient, 'ds': fl(n.ds) if n else None,
                       'examen': fl(n.examen) if n else None, 'note': fl(nt),
                       'points': fl(r2(nt * m.coefficient)) if nt is not None else None, 'appreciation': appreciation(nt)})
    res = ResultatTrimestre.objects.filter(inscription=ins, trimestre=trimestre).first()
    ag = agregats([ins.id], trimestre.date_debut, trimestre.date_fin).get(ins.id, {})
    dec = DecisionConseil.objects.filter(inscription=ins, trimestre=trimestre).first()
    from scolarite.services import classe_effectif
    return {
        'inscription': ins.id, 'matricule': ins.eleve.matricule, 'nom': ins.eleve.nom, 'prenoms': ins.eleve.prenoms,
        'classe': classe.nom, 'effectif_classe': classe_effectif(classe), 'annee': ins.annee.libelle,
        'trimestre': trimestre.numero, 'lignes': lignes,
        'total_coefficients': res.total_coefficients if res else 0, 'total_points': fl(res.total_points) if res else None,
        'moyenne': fl(res.moyenne) if res else None, 'appreciation': appreciation(res.moyenne) if res else '',
        'rang': res.rang if res else None, 'effectif_classe_classe': res.effectif_classe if res else 0,
        'absences_justifiees': ag.get('JUSTIFIEE', 0), 'absences_injustifiees': ag.get('ABSENT', 0),
        'retards': ag.get('retards', 0), 'decision': dec.texte if dec else '',
        'provisoire': manquantes > 0, 'matieres_sans_note': manquantes,
    }


def rang_str(rang, eff):
    if not rang:
        return '—'
    return f'{rang}{"er" if rang == 1 else "e"} / {eff}'
