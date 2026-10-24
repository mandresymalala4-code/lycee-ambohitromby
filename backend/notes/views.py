from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from comptes.errors import ApiError, Introuvable, Invalide, Refus
from comptes.models import audit
from comptes.permissions import EstAdmin
from scolarite.models import Classe, Inscription, Matiere, Trimestre
from scolarite.views import get_or_404
from .models import DecisionConseil, Note, ResultatTrimestre
from . import services as sv

MSG_CLOTURE = 'Trimestre clôturé : contactez l\'administrateur.'


def resoudre(classe_id, numero):
    classe = get_or_404(Classe.objects.select_related('annee'), classe_id)
    t = Trimestre.objects.filter(annee=classe.annee, numero=numero).first()
    if not t:
        raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
    return classe, t


def controle_matiere(user, matiere_id, classe):
    m = Matiere.objects.select_related('discipline', 'professeur__utilisateur').filter(pk=matiere_id, classe=classe).first()
    if not m:
        raise Invalide('Veuillez choisir une matière.', 'matiere')
    if user.role == 'PROFESSEUR' and not (m.professeur and m.professeur.utilisateur_id == user.id):
        raise Refus('Vous n\'avez pas le droit d\'effectuer cette action : cette matière n\'est pas la vôtre.')
    return m


def payload(classe, t, m, user):
    ins = list(Inscription.objects.filter(classe=classe, statut='ACTIVE').select_related('eleve').order_by('eleve__nom', 'eleve__prenoms'))
    notes = {n.inscription_id: n for n in Note.objects.filter(inscription__in=ins, matiere=m, trimestre=t)}
    lignes, vals = [], []
    for i in ins:
        n = notes.get(i.id)
        nt = sv.note_trimestrielle(n.ds, n.examen) if n else None
        if nt is not None:
            vals.append(nt)
        lignes.append({'inscription_id': i.id, 'matricule': i.eleve.matricule, 'nom': i.eleve.nom, 'prenoms': i.eleve.prenoms,
                       'ds': sv.fl(n.ds) if n else None, 'examen': sv.fl(n.examen) if n else None,
                       'note': sv.fl(nt), 'appreciation': sv.appreciation(nt)})
    saisies = sum((1 for n in notes.values() for x in (n.ds, n.examen) if x is not None))
    stats = {'moyenne': float(sv.r2(sum(vals) / len(vals))) if vals else None, 'max': float(max(vals)) if vals else None,
             'min': float(min(vals)) if vals else None, 'nb_notes': saisies, 'nb_attendues': 2 * len(ins)}
    return {'classe': classe.id, 'trimestre': t.numero, 'trimestre_id': t.id, 'matiere': m.id, 'matiere_nom': m.discipline.nom,
            'coefficient': m.coefficient, 'cloture': t.cloture, 'editable': (not t.cloture) or user.role == 'ADMIN',
            'lignes': lignes, 'stats': stats}


class NotesView(APIView):
    def get(self, request):
        qp = request.query_params
        classe, t = resoudre(qp.get('classe'), qp.get('trimestre'))
        m = controle_matiere(request.user, qp.get('matiere'), classe)
        return Response(payload(classe, t, m, request.user))

    @transaction.atomic
    def post(self, request):
        d = request.data
        classe, t = resoudre(d.get('classe'), d.get('trimestre'))
        m = controle_matiere(request.user, d.get('matiere'), classe)
        if t.cloture and request.user.role != 'ADMIN':
            raise ApiError(MSG_CLOTURE, {}, 'TRIMESTRE_CLOTURE', 403)
        items = d.get('notes')
        if not isinstance(items, list):
            raise Invalide('Aucune note à enregistrer.')
        valides = {i.id for i in Inscription.objects.filter(classe=classe, statut='ACTIVE')}
        champs, parsed = {}, []
        for it in items:
            iid = it.get('inscription_id')
            if iid not in valides:
                raise Invalide('Élève introuvable dans cette classe.')
            row = {}
            for k in ('ds', 'examen'):
                try:
                    row[k] = sv.parse_note(it.get(k))
                except ValueError as e:
                    champs[f'{k}_{iid}'] = str(e)
            parsed.append((iid, row.get('ds'), row.get('examen')))
        if champs:
            raise ApiError(next(iter(champs.values())), champs, 'DONNEES_INVALIDES', 400)
        for iid, ds, ex in parsed:
            if ds is None and ex is None:
                Note.objects.filter(inscription_id=iid, matiere=m, trimestre=t).delete()
            else:
                Note.objects.update_or_create(inscription_id=iid, matiere=m, trimestre=t, defaults={'ds': ds, 'examen': ex, 'saisi_par': request.user})
        sv.recalculer(classe, t)
        if t.cloture:
            audit(request.user, 'CORRECTION_NOTE_APRES_CLOTURE', 'note', m.id, f'{classe.nom} T{t.numero} {m.discipline.nom}')
        return Response(payload(classe, t, m, request.user))

    put = post


class ResultatsView(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        qp = request.query_params
        classe, t = resoudre(qp.get('classe'), qp.get('trimestre'))
        matieres = list(Matiere.objects.filter(classe=classe).select_related('discipline').order_by('discipline__nom'))
        ins = list(Inscription.objects.filter(classe=classe, statut='ACTIVE').select_related('eleve'))
        res = {r.inscription_id: r for r in ResultatTrimestre.objects.filter(inscription__in=ins, trimestre=t)}
        notes = {}
        for n in Note.objects.filter(inscription__in=ins, trimestre=t):
            notes.setdefault(n.inscription_id, {})[n.matiere_id] = sv.fl(sv.note_trimestrielle(n.ds, n.examen))
        rows = []
        for i in ins:
            r = res.get(i.id)
            rows.append({'inscription_id': i.id, 'matricule': i.eleve.matricule, 'nom': i.eleve.nom, 'prenoms': i.eleve.prenoms,
                         'notes': notes.get(i.id, {}), 'total_points': sv.fl(r.total_points) if r else None,
                         'total_coefficients': r.total_coefficients if r else 0, 'moyenne': sv.fl(r.moyenne) if r else None,
                         'appreciation': sv.appreciation(r.moyenne) if r else '', 'rang': r.rang if r else None,
                         'effectif_classe': r.effectif_classe if r else 0})
        rows.sort(key=lambda x: (x['rang'] is None, x['rang'] or 0, x['nom'], x['prenoms']))
        return Response({'matieres': [{'id': m.id, 'nom': m.discipline.nom, 'coefficient': m.coefficient} for m in matieres],
                         'lignes': rows, 'cloture': t.cloture})


class BulletinView(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk):
        ins = get_or_404(Inscription.objects.select_related('eleve', 'classe', 'annee'), pk)
        t = Trimestre.objects.filter(annee=ins.annee, numero=request.query_params.get('trimestre')).first()
        if not t:
            raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
        return Response(sv.bulletin_data(ins, t))


class DecisionView(APIView):
    permission_classes = [EstAdmin]

    def post(self, request):
        d = request.data
        ins = get_or_404(Inscription.objects.select_related('annee'), d.get('inscription'))
        t = Trimestre.objects.filter(annee=ins.annee, numero=d.get('trimestre')).first()
        if not t:
            raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
        texte = (d.get('texte') or '').strip()
        if len(texte) > 255:
            raise Invalide('255 caractères maximum.', 'texte')
        DecisionConseil.objects.update_or_create(inscription=ins, trimestre=t, defaults={'texte': texte})
        return Response({'texte': texte})


class DecisionClasse(APIView):
    """Applique la même décision à toute une classe (champ « Décision du conseil »)."""
    permission_classes = [EstAdmin]

    @transaction.atomic
    def post(self, request):
        classe, t = resoudre(request.data.get('classe'), request.data.get('trimestre'))
        texte = (request.data.get('texte') or '').strip()[:255]
        for i in Inscription.objects.filter(classe=classe, statut='ACTIVE'):
            DecisionConseil.objects.update_or_create(inscription=i, trimestre=t, defaults={'texte': texte})
        return Response({'texte': texte})
