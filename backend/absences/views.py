from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from comptes.errors import ApiError, Conflit, Introuvable, Invalide, Refus
from comptes.models import audit
from scolarite.models import Classe, Cours, Inscription, Matiere
from scolarite.services import trimestre_de_date
from scolarite.views import get_or_404, ser_cours
from . import services as sv
from .models import Absence, Appel

MSG_CLOTURE = 'Trimestre clôturé : contactez l\'administrateur.'
MSG_NOCOURS = 'Aucun cours de votre matière n\'est prévu ce jour pour cette classe.'
STATUTS = [s for s, _ in Absence.STATUTS]


def matiere_ok(user, classe_id, matiere_id):
    classe = get_or_404(Classe.objects.select_related('annee'), classe_id)
    m = Matiere.objects.select_related('discipline', 'professeur__utilisateur').filter(pk=matiere_id, classe=classe).first()
    if not m:
        raise Invalide('Veuillez choisir une matière.', 'matiere')
    if user.role == 'PROFESSEUR' and not (m.professeur and m.professeur.utilisateur_id == user.id):
        raise Refus('Vous n\'avez pas le droit d\'effectuer cette action : cette matière n\'est pas la vôtre.')
    return classe, m


def parse_date(v):
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        raise Invalide('La date ne correspond pas au jour choisi.', 'date')


def controle_date(d, jour=None):
    if d.isoweekday() > 5 or (jour not in (None, '') and int(jour) != d.isoweekday()):
        raise Invalide('La date ne correspond pas au jour choisi.' if d.isoweekday() <= 5 else 'Les cours ont lieu du lundi au vendredi.', 'date')
    if d > date.today():
        raise Invalide('La date ne peut pas être dans le futur.', 'date')


def dec(v, champ, msg):
    try:
        return Decimal(str(v).replace(',', '.'))
    except (InvalidOperation, ValueError):
        raise Invalide(msg, champ)


def trouver_appel(m, d, cours_id):
    return Appel.objects.filter(matiere=m, date=d, cours_id=cours_id or None).first()


def seances_du_jour(m, d):
    return Cours.objects.filter(matiere=m, jour=d.isoweekday()).order_by('heure_debut')


def lignes_payload(classe, appel, d, matiere_id=None, prof_matiere=None):
    ins = list(Inscription.objects.filter(classe=classe, statut='ACTIVE').select_related('eleve').order_by('eleve__nom', 'eleve__prenoms'))
    existantes = {a.inscription_id: a for a in appel.lignes.all()} if appel else {}
    t = trimestre_de_date(classe.annee, d)
    ids = [i.id for i in ins]
    mois = sv.agregats(ids, d.replace(day=1), sv.bornes_mois(d.strftime('%Y-%m'))[1], matiere_id)
    tri = sv.agregats(ids, t.date_debut, t.date_fin, matiere_id) if t else {}
    out = []
    for i in ins:
        a = existantes.get(i.id)
        tr = tri.get(i.id, {})
        inj = tr.get('ABSENT', 0)
        out.append({'inscription_id': i.id, 'matricule': i.eleve.matricule, 'nom': i.eleve.nom, 'prenoms': i.eleve.prenoms,
                    'statut': a.statut if a else 'PRESENT', 'heures_absence': float(a.heures_absence) if a else 0,
                    'motif': a.motif if a else '', 'observation': a.observation if a else '',
                    'total_mensuel': sv.total_abs(mois.get(i.id, {})), 'total_trimestriel': sv.total_abs(tr),
                    'injustifiees': inj, 'alerte': sv.depasse_seuil(inj)})
    return out


def ser_appel_payload(user, classe, m, d, appel, cours):
    t = trimestre_de_date(classe.annee, d)
    cloture = bool(t and t.cloture)
    editable = user.role == 'ADMIN' or (not cloture and (appel is None or appel.saisi_par_id == user.id))
    duree = float(appel.duree_heures) if appel else (cours.duree if cours else None)
    return {'appel': {'id': appel.id, 'cours': appel.cours_id, 'duree_heures': float(appel.duree_heures), 'date': appel.date,
                      'saisi_par': appel.saisi_par.nom_complet if appel.saisi_par else ''} if appel else None,
            'duree': duree, 'cloture': cloture, 'editable': editable, 'trimestre': t.numero if t else None,
            'lignes': lignes_payload(classe, appel, d, m.id)}


class SeancesView(APIView):
    def get(self, request):
        qp = request.query_params
        classe, m = matiere_ok(request.user, qp.get('classe'), qp.get('matiere'))
        d = parse_date(qp.get('date'))
        return Response([ser_cours(c) for c in seances_du_jour(m, d).select_related('matiere__discipline', 'matiere__classe', 'matiere__professeur__utilisateur')])


class AppelView(APIView):
    def get(self, request):
        qp = request.query_params
        classe, m = matiere_ok(request.user, qp.get('classe'), qp.get('matiere'))
        d = parse_date(qp.get('date'))
        controle_date(d, qp.get('jour'))
        cours_id = qp.get('cours') if qp.get('cours') not in (None, '', '0', 'null') else None
        cours = None
        if cours_id:
            cours = Cours.objects.filter(pk=cours_id, matiere=m, jour=d.isoweekday()).first()
            if not cours:
                raise Invalide(MSG_NOCOURS, 'cours')
        elif not trouver_appel(m, d, None):
            seances = list(seances_du_jour(m, d))
            if len(seances) == 1:
                cours = seances[0]
                cours_id = cours.id
        appel = trouver_appel(m, d, cours_id)
        if request.user.role == 'PROFESSEUR' and not appel and not cours and not seances_du_jour(m, d).exists():
            raise Invalide(MSG_NOCOURS, 'cours')
        return Response({**ser_appel_payload(request.user, classe, m, d, appel, cours),
                         'cours': ser_cours(cours) if cours else None})

    def _verifier(self, request, appel=None):
        data = request.data
        user = request.user
        classe, m = matiere_ok(user, data.get('classe'), data.get('matiere'))
        d = parse_date(data.get('date'))
        controle_date(d, data.get('jour'))
        t = trimestre_de_date(classe.annee, d)
        if not t:
            raise Invalide('La date doit être comprise dans un trimestre de l\'année.', 'date')
        if t.cloture and user.role != 'ADMIN':
            raise ApiError(MSG_CLOTURE, {}, 'TRIMESTRE_CLOTURE', 403)
        cours = None
        cid = data.get('cours') if data.get('cours') not in (None, '', 0, '0') else None
        if cid:
            cours = Cours.objects.filter(pk=cid, matiere=m, jour=d.isoweekday()).first()
            if not cours:
                raise Invalide(MSG_NOCOURS, 'cours')
        elif user.role == 'PROFESSEUR':
            raise Invalide(MSG_NOCOURS, 'cours')
        if cours:
            duree = Decimal(str(cours.duree)).quantize(Decimal('0.01'))
        else:
            duree = dec(data.get('duree_heures'), 'duree_heures', 'Saisissez la durée de la séance.')
            if duree <= 0 or duree > 11 or (duree * 4) % 1 != 0:
                raise Invalide('Saisissez la durée de la séance (pas de 0,25 h).', 'duree_heures')
        lignes = data.get('lignes')
        if not isinstance(lignes, list) or not lignes:
            raise Invalide('Aucun élève à enregistrer.')
        valides = {i.id for i in Inscription.objects.filter(classe=classe, statut='ACTIVE')}
        out, champs = [], {}
        for l in lignes:
            iid = l.get('inscription_id')
            if iid not in valides:
                raise Invalide('Élève introuvable dans cette classe.')
            st = l.get('statut')
            if st not in STATUTS:
                champs[f'statut_{iid}'] = 'Veuillez choisir un statut.'
                continue
            motif, obs = (l.get('motif') or '').strip(), (l.get('observation') or '').strip()
            if len(motif) > 255 or len(obs) > 255:
                champs[f'motif_{iid}'] = '255 caractères maximum.'
                continue
            if st == 'PRESENT':
                h = Decimal(0)
            else:
                brut = l.get('heures_absence')
                if brut in (None, ''):
                    h = duree if st in ('ABSENT', 'JUSTIFIEE') else Decimal('0.25')
                else:
                    try:
                        h = Decimal(str(brut).replace(',', '.'))
                    except InvalidOperation:
                        champs[f'heures_{iid}'] = 'Les heures d\'absence dépassent la durée de la séance.'
                        continue
                if h < 0 or h > duree or (h * 4) % 1 != 0:
                    champs[f'heures_{iid}'] = 'Les heures d\'absence dépassent la durée de la séance.'
                    continue
            if st == 'JUSTIFIEE' and not motif:
                champs[f'motif_{iid}'] = 'Le motif est obligatoire pour une absence justifiée.'
                continue
            out.append((iid, st, h, motif, obs))
        if champs:
            raise ApiError(next(iter(champs.values())), champs, 'DONNEES_INVALIDES', 400)
        return classe, m, d, t, cours, duree, out

    @transaction.atomic
    def post(self, request):
        classe, m, d, t, cours, duree, lignes = self._verifier(request)
        if trouver_appel(m, d, cours.id if cours else None):
            raise Conflit('Un appel existe déjà pour cette classe, cette matière et cette séance.', code='APPEL_EXISTE')
        appel = Appel.objects.create(classe=classe, matiere=m, cours=cours, date=d, duree_heures=duree, saisi_par=request.user)
        Absence.objects.bulk_create([Absence(appel=appel, inscription_id=i, statut=s, heures_absence=h, motif=mo, observation=o) for i, s, h, mo, o in lignes])
        return Response(ser_appel_payload(request.user, classe, m, d, appel, cours), status=201)

    @transaction.atomic
    def put(self, request, pk):
        appel = get_or_404(Appel.objects.select_related('saisi_par'), pk)
        if request.user.role == 'PROFESSEUR' and appel.saisi_par_id != request.user.id:
            raise Refus('Vous ne pouvez modifier que les appels que vous avez saisis.')
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data.update({'classe': appel.classe_id, 'matiere': appel.matiere_id, 'date': appel.date.isoformat(), 'cours': appel.cours_id})
        request._full_data = data
        classe, m, d, t, cours, duree, lignes = self._verifier(request, appel)
        appel.duree_heures = duree
        appel.save(update_fields=['duree_heures'])
        appel.lignes.all().delete()
        Absence.objects.bulk_create([Absence(appel=appel, inscription_id=i, statut=s, heures_absence=h, motif=mo, observation=o) for i, s, h, mo, o in lignes])
        if t.cloture:
            audit(request.user, 'CORRECTION_APPEL_APRES_CLOTURE', 'appel', appel.id)
        return Response(ser_appel_payload(request.user, classe, m, d, appel, cours))


def recap_rows(user, classe, qp):
    """Récapitulatif mensuel / trimestriel d'une classe (§8.5, §9.6)."""
    matiere_id = qp.get('matiere') or None
    if user.role == 'PROFESSEUR':
        mine = Matiere.objects.filter(classe=classe, professeur__utilisateur=user).first()
        if not mine or (matiere_id and int(matiere_id) != mine.id):
            raise Refus()
        matiere_id = mine.id
    if qp.get('periode') == 'mois':
        ym = qp.get('mois') or date.today().strftime('%Y-%m')
        d1, d2 = sv.bornes_mois(ym)
        t = trimestre_de_date(classe.annee, d2) or trimestre_de_date(classe.annee, d1)
        titre = f'Mois de {ym[5:7]}/{ym[:4]}'
    else:
        t = classe.annee.trimestres.filter(numero=qp.get('trimestre') or 1).first()
        if not t:
            raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
        d1, d2, titre = t.date_debut, t.date_fin, f'{t.numero}{"er" if t.numero == 1 else "ème"} trimestre'
    ins = list(Inscription.objects.filter(classe=classe, statut='ACTIVE').select_related('eleve').order_by('eleve__nom', 'eleve__prenoms'))
    ids = [i.id for i in ins]
    ag = sv.agregats(ids, d1, d2, matiere_id)
    tri = sv.agregats(ids, t.date_debut, t.date_fin, matiere_id) if t else {}
    rows = []
    for i in ins:
        a = ag.get(i.id, {})
        inj_tri = tri.get(i.id, {}).get('ABSENT', 0)
        rows.append({'inscription_id': i.id, 'matricule': i.eleve.matricule, 'nom': i.eleve.nom, 'prenoms': i.eleve.prenoms,
                     'justifiees': a.get('JUSTIFIEE', 0), 'injustifiees': a.get('ABSENT', 0), 'retards': a.get('retards', 0),
                     'retard_heures': a.get('RETARD', 0), 'total': sv.total_abs(a), 'injustifiees_trimestre': inj_tri,
                     'alerte': sv.depasse_seuil(inj_tri)})
    return titre, rows


class RecapView(APIView):
    def get(self, request):
        classe = get_or_404(Classe.objects.select_related('annee'), request.query_params.get('classe'))
        titre, rows = recap_rows(request.user, classe, request.query_params)
        return Response({'titre': titre, 'classe': classe.nom, 'lignes': rows})


class AlertesView(APIView):
    def get(self, request):
        from scolarite.services import annee_courante
        from scolarite.models import AnneeScolaire
        a = AnneeScolaire.objects.filter(pk=request.query_params.get('annee')).first() or annee_courante()
        ids = None
        if request.user.role == 'PROFESSEUR':
            ids = list(Matiere.objects.filter(professeur__utilisateur=request.user, classe__annee=a).values_list('id', flat=True))
        return Response(sv.alertes(a, ids))
