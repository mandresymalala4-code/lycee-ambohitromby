from calendar import monthrange
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.db.models import Count, Sum
from .models import Absence


def agregats(ins_ids, d1, d2, matiere_id=None):
    """{inscription_id: {'JUSTIFIEE': h, 'ABSENT': h, 'RETARD': h, 'retards': n}} sur [d1, d2]."""
    qs = Absence.objects.filter(inscription_id__in=ins_ids, appel__date__gte=d1, appel__date__lte=d2)
    if matiere_id:
        qs = qs.filter(appel__matiere_id=matiere_id)
    out = {}
    for r in qs.exclude(statut='PRESENT').values('inscription_id', 'statut').annotate(h=Sum('heures_absence'), n=Count('id')):
        d = out.setdefault(r['inscription_id'], {})
        d[r['statut']] = float(r['h'] or 0)
        if r['statut'] == 'RETARD':
            d['retards'] = r['n']
    return out


def depasse_seuil(h):
    return h > settings.SEUIL_ALERTE_ABSENCES


def bornes_mois(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return date(y, m, 1), date(y, m, monthrange(y, m)[1])


def total_abs(d):
    """Heures d'absence = Absent + Absence justifiée (§8.5)."""
    return round(d.get('ABSENT', 0) + d.get('JUSTIFIEE', 0), 2)


def alertes(annee, matiere_ids=None, today=None):
    today = today or date.today()
    out = []
    for t in annee.trimestres.order_by('numero'):
        if t.date_debut > today:
            continue
        qs = Absence.objects.filter(statut='ABSENT', appel__date__gte=t.date_debut, appel__date__lte=t.date_fin,
                                    inscription__annee=annee)
        if matiere_ids is not None:
            qs = qs.filter(appel__matiere_id__in=matiere_ids)
        for r in qs.values('inscription_id', 'inscription__eleve__matricule', 'inscription__eleve__nom',
                           'inscription__eleve__prenoms', 'inscription__classe__nom', 'inscription__classe_id').annotate(h=Sum('heures_absence')):
            if depasse_seuil(r['h'] or Decimal(0)):
                out.append({'inscription_id': r['inscription_id'], 'matricule': r['inscription__eleve__matricule'],
                            'nom': r['inscription__eleve__nom'], 'prenoms': r['inscription__eleve__prenoms'],
                            'classe': r['inscription__classe__nom'], 'classe_id': r['inscription__classe_id'],
                            'trimestre': t.numero, 'heures': float(r['h'])})
    out.sort(key=lambda x: -x['heures'])
    return out
