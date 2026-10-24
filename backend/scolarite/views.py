from datetime import date
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from comptes import validators as V
from comptes.errors import ApiError, Conflit, Introuvable, Invalide, Refus
from comptes.models import Discipline, Etablissement, Professeur, audit
from comptes.services import discipline_pour
from comptes.permissions import AdminOuLecture, EstAdmin
from . import services as sv
from .models import (AnneeScolaire, Classe, Cours, Eleve, Famille, Inscription, Matiere, Paiement, Trimestre)
from .serializers import ClasseIn, CoursIn, EleveIn, FamilleIn, InscriptionIn, MatiereIn, photo_url


def get_or_404(model, pk, **kw):
    qs = model if hasattr(model, 'filter') and not isinstance(model, type) else model.objects.all()
    try:
        return qs.get(pk=pk, **kw)
    except (qs.model.DoesNotExist, ValueError, TypeError):
        raise Introuvable()


def ser_trimestre(t):
    return {'id': t.id, 'numero': t.numero, 'date_debut': t.date_debut, 'date_fin': t.date_fin, 'cloture': t.cloture}


def ser_annee(a):
    return {'id': a.id, 'annee_debut': a.annee_debut, 'libelle': a.libelle, 'courante': a.courante}


class AnneesView(APIView):
    def get(self, request):
        sv.ensure_toutes_annees()
        return Response([ser_annee(a) for a in AnneeScolaire.objects.all()])


class TrimestresView(APIView):
    permission_classes = [AdminOuLecture]

    def get(self, request, pk):
        a = get_or_404(AnneeScolaire, pk)
        return Response([ser_trimestre(t) for t in a.trimestres.order_by('numero')])

    def put(self, request, pk):
        a = get_or_404(AnneeScolaire, pk)
        data = request.data if isinstance(request.data, list) else request.data.get('trimestres', [])
        ts = {t.numero: t for t in a.trimestres.all()}
        prev, new = None, {}
        mini, maxi = date(a.annee_debut, 9, 1), date(a.annee_fin, 8, 31)
        for n in (1, 2, 3):
            item = next((x for x in data if int(x.get('numero', 0)) == n), None)
            try:
                d1, d2 = date.fromisoformat(str(item['date_debut'])), date.fromisoformat(str(item['date_fin']))
            except Exception:
                raise Invalide('Les dates des trimestres sont incohérentes.', 'trimestres')
            if d1 >= d2 or d1 < mini or d2 > maxi or (prev and d1 <= prev):
                raise Invalide('Les dates des trimestres sont incohérentes.', 'trimestres')
            prev = d2
            new[n] = (d1, d2)
        for n, (d1, d2) in new.items():
            ts[n].date_debut, ts[n].date_fin = d1, d2
            ts[n].save()
        return Response([ser_trimestre(t) for t in a.trimestres.order_by('numero')])


class Cloture(APIView):
    permission_classes = [EstAdmin]

    def post(self, request, pk):
        t = get_or_404(Trimestre, pk)
        t.cloture = bool(request.data.get('cloture', True))
        t.save(update_fields=['cloture'])
        audit(request.user, 'CLOTURE_TRIMESTRE' if t.cloture else 'REOUVERTURE_TRIMESTRE', 'trimestre', t.id, f'{t.annee.libelle} T{t.numero}')
        return Response(ser_trimestre(t))


# ---------- Classes ----------
def ser_classe(c, admin, eff=0):
    d = {'id': c.id, 'annee': c.annee_id, 'nom': c.nom, 'effectif': eff}
    if admin:
        d.update(droit_inscription=c.droit_inscription, caisse_soutien=c.caisse_soutien, total=c.total)
    return d


class ClassesView(APIView):
    permission_classes = [AdminOuLecture]

    def get(self, request, pk=None):
        admin = request.user.role == 'ADMIN'
        if pk:
            c = get_or_404(Classe, pk)
            return Response(ser_classe(c, admin, sv.classe_effectif(c)))
        annee = get_or_404(AnneeScolaire, request.query_params.get('annee')) if request.query_params.get('annee') else sv.annee_courante()
        sv.ensure_classes(annee)
        eff = sv.effectifs(annee.id)
        order = {n: i for i, (n, _) in enumerate(sv.CLASSES_DEFAUT)}
        cl = sorted(Classe.objects.filter(annee=annee), key=lambda c: (order.get(c.nom, 99), c.nom))
        return Response([ser_classe(c, admin, eff.get(c.id, 0)) for c in cl])

    def post(self, request):
        s = ClasseIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        annee = get_or_404(AnneeScolaire, d.get('annee') or request.data.get('annee'))
        if Classe.objects.filter(annee=annee, nom__iexact=d['nom']).exists():
            raise Conflit('Ce nom de classe existe déjà pour cette année.', 'nom')
        c = Classe.objects.create(annee=annee, nom=d['nom'], droit_inscription=d['droit_inscription'], caisse_soutien=d['caisse_soutien'])
        return Response(ser_classe(c, True), status=201)

    def put(self, request, pk):
        c = get_or_404(Classe, pk)
        s = ClasseIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if Classe.objects.filter(annee=c.annee, nom__iexact=d['nom']).exclude(pk=c.pk).exists():
            raise Conflit('Ce nom de classe existe déjà pour cette année.', 'nom')
        c.nom, c.droit_inscription, c.caisse_soutien = d['nom'], d['droit_inscription'], d['caisse_soutien']
        c.save()
        return Response(ser_classe(c, True, sv.classe_effectif(c)))

    def delete(self, request, pk):
        c = get_or_404(Classe, pk)
        if c.inscriptions.exists() or c.matieres.exists():
            raise Conflit('Cette classe contient des élèves ou des matières. Elle ne peut pas être supprimée.', code='CLASSE_NON_VIDE')
        c.delete()
        return Response(status=204)


# ---------- Élèves ----------
def ser_row_eleve(i):
    e = i.eleve
    return {'id': i.id, 'eleve_id': e.id, 'matricule': e.matricule, 'nom': e.nom, 'prenoms': e.prenoms,
            'date_naissance': e.date_naissance, 'sexe': e.sexe, 'adresse': e.adresse, 'observation': e.observation,
            'photo': photo_url(e.photo), 'classe': i.classe_id, 'classe_nom': i.classe.nom, 'annee': i.annee_id,
            'date_inscription': i.date_inscription}


def ser_famille(f):
    return {k: getattr(f, k) for k in ('pere_nom', 'pere_prenoms', 'mere_nom', 'mere_prenoms', 'contact_parent',
                                        'adresse_parents', 'tuteur_nom', 'tuteur_prenoms', 'tuteur_contact')}


def ser_paiement(p):
    return {'id': p.id, 'numero_recu': p.numero_recu, 'droit_inscription': p.droit_inscription, 'caisse_soutien': p.caisse_soutien,
            'total': p.total, 'mode_paiement': p.mode_paiement, 'date_paiement': p.date_paiement, 'statut': p.statut,
            'matricule': p.eleve_matricule, 'nom': p.eleve_nom, 'prenoms': p.eleve_prenoms, 'classe_nom': p.classe_nom,
            'annee_libelle': p.annee.libelle}


def ser_fiche(i, admin):
    d = ser_row_eleve(i)
    d['annee_libelle'] = i.annee.libelle
    d['famille'] = ser_famille(i.eleve.famille)
    if admin:
        p = getattr(i, 'paiement', None)
        d['paiement'] = ser_paiement(p) if p else None
    return d


class ElevesView(APIView):
    permission_classes = [AdminOuLecture]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, pk=None):
        admin = request.user.role == 'ADMIN'
        if pk:
            i = get_or_404(Inscription.objects.select_related('eleve', 'eleve__famille', 'classe', 'annee'), pk)
            return Response(ser_fiche(i, admin))
        qp = request.query_params
        ordre = 'alpha' if qp.get('tri') == 'alpha' else ('matricule' if qp.get('classe') else 'recent')
        qs = sv.inscriptions_filtrees(qp, ordre)
        return Response([ser_row_eleve(i) for i in qs])

    def put(self, request, pk):
        if request.user.role != 'ADMIN':
            raise Refus()
        i = get_or_404(Inscription.objects.select_related('eleve', 'eleve__famille', 'classe', 'annee'), pk)
        se, sf = EleveIn(data=request.data.get('eleve', request.data)), FamilleIn(data=request.data.get('famille', request.data))
        se.is_valid(raise_exception=True)
        sf.is_valid(raise_exception=True)
        e, f = i.eleve, i.eleve.famille
        with transaction.atomic():
            for k, v in se.validated_data.items():
                setattr(e, k, v)
            fd = sf.validated_data
            autre = Famille.objects.filter(contact_parent=fd['contact_parent']).exclude(pk=f.pk).first()
            if autre:
                if not request.data.get('rattacher_famille'):
                    raise Conflit(f'Cette famille existe déjà (parents de {autre.pere_nom or autre.mere_nom or autre.tuteur_nom}). Rattacher cet élève à cette famille ?', 'contact_parent', 'FAMILLE_EXISTE')
                old = f
                f = autre
                e.famille = f
                e.save()
                if not old.eleves.exists():
                    old.delete()
            else:
                for k, v in fd.items():
                    setattr(f, k, v)
                f.save()
            e.save()
        audit(request.user, 'MODIF_ELEVE', 'eleve', e.id, e.matricule)
        i.refresh_from_db()
        return Response(ser_fiche(Inscription.objects.select_related('eleve', 'eleve__famille', 'classe', 'annee').get(pk=i.pk), True))

    def delete(self, request, pk):
        if request.user.role != 'ADMIN':
            raise Refus()
        i = get_or_404(Inscription.objects.select_related('eleve', 'eleve__famille'), pk)
        if i.notes.exists() or i.absences.exists():
            raise Conflit('Cet élève a des notes ou des absences enregistrées. Suppression impossible.', code='ELEVE_AVEC_DONNEES')
        with transaction.atomic():
            e, f = i.eleve, i.eleve.famille
            Paiement.objects.filter(inscription=i).update(statut='ANNULE')
            mat = e.matricule
            i.delete()
            if not e.inscriptions.exists():
                e.delete()
                if not f.eleves.exists():
                    f.delete()
        audit(request.user, 'SUPPRESSION_INSCRIPTION', 'eleve', pk, mat)
        return Response(status=204)


class PhotoEleve(APIView):
    permission_classes = [EstAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        i = get_or_404(Inscription.objects.select_related('eleve'), pk)
        try:
            f = V.v_photo(request.FILES.get('photo'))
        except Exception as ex:
            raise Invalide('Format de photo non accepté (JPG ou PNG, 2 Mo maximum).', 'photo')
        if f is None:
            raise Invalide('Format de photo non accepté (JPG ou PNG, 2 Mo maximum).', 'photo')
        i.eleve.photo = f
        i.eleve.save(update_fields=['photo'])
        return Response({'photo': photo_url(i.eleve.photo)})


class RechercheEleve(APIView):
    """Recherche d'un élève déjà enregistré (toutes années) pour réinscription."""
    permission_classes = [EstAdmin]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        if len(q) < 2:
            return Response([])
        qs = Eleve.objects.filter(Q(nom__icontains=q) | Q(prenoms__icontains=q) | Q(matricule__icontains=q)).select_related('famille').order_by('nom', 'prenoms')[:15]
        return Response([{'id': e.id, 'matricule': e.matricule, 'nom': e.nom, 'prenoms': e.prenoms, 'date_naissance': e.date_naissance,
                          'sexe': e.sexe, 'adresse': e.adresse, 'observation': e.observation, 'photo': photo_url(e.photo),
                          'famille': ser_famille(e.famille)} for e in qs])


class FamilleParContact(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        c = V.re.sub(r'\s', '', request.query_params.get('contact') or '')
        f = Famille.objects.filter(contact_parent=c).first()
        return Response({'famille': ser_famille(f) if f else None})


# ---------- Inscriptions ----------
class InscriptionsView(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        qp = request.query_params
        return Response([ser_row_eleve(i) for i in sv.inscriptions_filtrees(qp, 'recent')])

    @transaction.atomic
    def post(self, request):
        s = InscriptionIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        annee = AnneeScolaire.objects.filter(pk=d['annee']).first()
        if not annee:
            raise Invalide('Veuillez choisir l\'année scolaire.', 'annee')
        classe = Classe.objects.filter(pk=d['classe'], annee=annee).first()
        if not classe:
            raise Invalide('Classe inexistante.', 'classe')
        ed, fd = d['eleve'], d['famille']
        eleve = None
        if d.get('eleve_id'):
            eleve = Eleve.objects.select_related('famille').filter(pk=d['eleve_id']).first()
            if not eleve:
                raise Introuvable()
        else:
            eleve = Eleve.objects.select_related('famille').filter(nom=ed['nom'], prenoms=ed['prenoms'], date_naissance=ed['date_naissance']).first()
        if eleve and Inscription.objects.filter(eleve=eleve, annee=annee).exists():
            raise Conflit('Cet élève est déjà inscrit pour cette année scolaire.', 'nom', 'DEJA_INSCRIT')
        # Famille
        existante = Famille.objects.filter(contact_parent=fd['contact_parent']).first()
        if eleve and existante and existante.pk == eleve.famille_id:
            famille = existante
            for k, v in fd.items():
                setattr(famille, k, v)
            famille.save()
        elif existante:
            if not d['rattacher_famille']:
                nom = existante.pere_nom or existante.mere_nom or existante.tuteur_nom
                raise Conflit(f'Cette famille existe déjà (parents de {nom}). Rattacher cet élève à cette famille ?', 'contact_parent', 'FAMILLE_EXISTE')
            famille = existante
        elif eleve:
            famille = eleve.famille
            for k, v in fd.items():
                setattr(famille, k, v)
            famille.save()
        else:
            famille = Famille.objects.create(**fd)
        if eleve:
            for k, v in ed.items():
                setattr(eleve, k, v)
            eleve.famille = famille
            eleve.save()
        else:
            eleve = Eleve.objects.create(matricule=sv.prochain_matricule(annee.annee_debut), famille=famille, **ed)
        ins = Inscription.objects.create(eleve=eleve, classe=classe, annee=annee)
        p = Paiement.objects.create(inscription=ins, annee=annee, numero_recu=sv.prochain_recu(annee), droit_inscription=classe.droit_inscription,
                                    caisse_soutien=classe.caisse_soutien, total=classe.total, mode_paiement=d['mode_paiement'],
                                    enregistre_par=request.user, eleve_matricule=eleve.matricule, eleve_nom=eleve.nom,
                                    eleve_prenoms=eleve.prenoms, classe_nom=classe.nom)
        audit(request.user, 'INSCRIPTION', 'inscription', ins.id, f'{eleve.matricule} {classe.nom} {annee.libelle} {p.numero_recu}')
        ins = Inscription.objects.select_related('eleve', 'eleve__famille', 'classe', 'annee', 'paiement').get(pk=ins.pk)
        return Response(ser_fiche(ins, True), status=201)

    def delete(self, request, pk):
        return ElevesView().delete(request, pk)


class Paiements(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk=None):
        if pk:
            return Response(ser_paiement(get_or_404(Paiement.objects.select_related('annee'), pk)))
        qs = Paiement.objects.select_related('annee').order_by('-id')
        if request.query_params.get('annee'):
            qs = qs.filter(annee_id=request.query_params['annee'])
        return Response([ser_paiement(p) for p in qs])


# ---------- Matières ----------
def ser_matiere(m):
    p = m.professeur
    return {'id': m.id, 'classe': m.classe_id, 'classe_nom': m.classe.nom, 'discipline': m.discipline_id, 'nom': m.discipline.nom,
            'coefficient': m.coefficient, 'professeur': p.id if p else None,
            'professeur_nom': f'{p.utilisateur.nom} {p.utilisateur.prenom}' if p else None}


def verifier_prof(prof_id, discipline):
    if not prof_id:
        return None
    p = Professeur.objects.select_related('utilisateur').filter(pk=prof_id, utilisateur__statut='VALIDE').first()
    if not p:
        raise Introuvable()
    if p.discipline_id != discipline.id:
        raise Invalide('Ce professeur n\'enseigne pas cette matière.', 'professeur')
    return p


class MatieresView(APIView):
    permission_classes = [AdminOuLecture]

    def get(self, request):
        qs = Matiere.objects.select_related('classe', 'discipline', 'professeur__utilisateur')
        qp = request.query_params
        if qp.get('classe'):
            qs = qs.filter(classe_id=qp['classe'])
        if qp.get('annee'):
            qs = qs.filter(classe__annee_id=qp['annee'])
        if request.user.role == 'PROFESSEUR' and qp.get('mienne'):
            qs = qs.filter(professeur__utilisateur=request.user)
        return Response([ser_matiere(m) for m in qs.order_by('discipline__nom')])

    @transaction.atomic
    def post(self, request):
        s = MatiereIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if 'nom' not in d:
            raise Invalide('La matière doit contenir entre 2 et 100 caractères.', 'nom')
        classe = get_or_404(Classe, d.get('classe') or request.data.get('classe'))
        disc = discipline_pour(d['nom'])
        if Matiere.objects.filter(classe=classe, discipline=disc).exists():
            raise Conflit('Matière déjà existante dans cette classe.', 'nom')
        prof = verifier_prof(d.get('professeur'), disc)
        m = Matiere.objects.create(classe=classe, discipline=disc, coefficient=d['coefficient'], professeur=prof)
        return Response(ser_matiere(m), status=201)

    @transaction.atomic
    def put(self, request, pk):
        m = get_or_404(Matiere.objects.select_related('classe', 'discipline'), pk)
        s = MatiereIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        disc = discipline_pour(d['nom']) if d.get('nom') else m.discipline
        if Matiere.objects.filter(classe=m.classe, discipline=disc).exclude(pk=m.pk).exists():
            raise Conflit('Matière déjà existante dans cette classe.', 'nom')
        if disc.id != m.discipline_id and m.notes.exists():
            raise Conflit('Des notes existent pour cette matière. Elle ne peut pas être renommée.', 'nom')
        prof = verifier_prof(d.get('professeur'), disc)
        m.discipline, m.coefficient, m.professeur = disc, d['coefficient'], prof
        m.save()
        return Response(ser_matiere(m))

    def delete(self, request, pk):
        m = get_or_404(Matiere, pk)
        if m.notes.exists():
            raise Conflit('Des notes existent pour cette matière. Suppression impossible.', code='MATIERE_AVEC_NOTES')
        if m.appels.exists():
            raise Conflit('Des appels existent pour cette matière. Suppression impossible.', code='MATIERE_AVEC_APPELS')
        m.delete()
        return Response(status=204)


class CopierMatieres(APIView):
    permission_classes = [EstAdmin]

    @transaction.atomic
    def post(self, request):
        classe = get_or_404(Classe, request.data.get('classe'))
        prec = AnneeScolaire.objects.filter(annee_debut=classe.annee.annee_debut - 1).first()
        src = Classe.objects.filter(annee=prec, nom=classe.nom).first() if prec else None
        if not src:
            raise Invalide('Aucune matière à copier pour l\'année précédente.')
        n = 0
        for m in src.matieres.select_related('professeur__utilisateur'):
            if Matiere.objects.filter(classe=classe, discipline=m.discipline).exists():
                continue
            prof = m.professeur if m.professeur and m.professeur.utilisateur.statut == 'VALIDE' else None
            Matiere.objects.create(classe=classe, discipline=m.discipline, coefficient=m.coefficient, professeur=prof)
            n += 1
        return Response({'copiees': n})


# ---------- Emploi du temps ----------
JOURS = ['', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']


def ser_cours(c):
    m, p = c.matiere, c.matiere.professeur
    return {'id': c.id, 'matiere': m.id, 'matiere_nom': m.discipline.nom, 'discipline': m.discipline_id, 'classe': m.classe_id,
            'classe_nom': m.classe.nom, 'professeur': p.id if p else None,
            'professeur_nom': f'{p.utilisateur.nom} {p.utilisateur.prenom}' if p else '', 'jour': c.jour, 'jour_nom': JOURS[c.jour],
            'heure_debut': c.heure_debut.strftime('%H:%M'), 'heure_fin': c.heure_fin.strftime('%H:%M'), 'salle': c.salle}


def cours_qs():
    return Cours.objects.select_related('matiere__discipline', 'matiere__classe', 'matiere__professeur__utilisateur')


def verifier_conflits(m, jour, debut, fin, exclude=None):
    base = cours_qs().filter(jour=jour, heure_debut__lt=fin, heure_fin__gt=debut)
    if exclude:
        base = base.exclude(pk=exclude)
    if base.filter(matiere__classe=m.classe).exists():
        raise Conflit('Un cours est déjà prévu à ce créneau pour cette classe.', 'heure_debut', 'CONFLIT_CLASSE')
    other = base.filter(matiere__professeur=m.professeur).exclude(matiere__classe=m.classe).first() if m.professeur else None
    if other:
        raise Conflit(f'Ce professeur a déjà un cours à ce créneau dans la classe {other.matiere.classe.nom}.', 'heure_debut', 'CONFLIT_PROFESSEUR')


class CoursView(APIView):
    permission_classes = [AdminOuLecture]

    def get(self, request):
        qs = cours_qs()
        if request.query_params.get('classe'):
            qs = qs.filter(matiere__classe_id=request.query_params['classe'])
        elif request.query_params.get('annee'):
            qs = qs.filter(matiere__classe__annee_id=request.query_params['annee'])
        return Response([ser_cours(c) for c in qs.order_by('jour', 'heure_debut')])

    def _save(self, request, c=None):
        s = CoursIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        m = Matiere.objects.select_related('classe', 'discipline', 'professeur__utilisateur').filter(pk=d['matiere']).first()
        if not m:
            raise Invalide('Veuillez choisir une matière.', 'matiere')
        if not m.professeur:
            raise Invalide('Affectez d\'abord un professeur à cette matière.', 'matiere')
        verifier_conflits(m, d['jour'], d['heure_debut'], d['heure_fin'], c.pk if c else None)
        c = c or Cours()
        c.matiere, c.jour, c.heure_debut, c.heure_fin, c.salle = m, d['jour'], d['heure_debut'], d['heure_fin'], d['salle']
        c.save()
        return c

    @transaction.atomic
    def post(self, request):
        return Response(ser_cours(cours_qs().get(pk=self._save(request).pk)), status=201)

    @transaction.atomic
    def put(self, request, pk):
        c = get_or_404(Cours, pk)
        return Response(ser_cours(cours_qs().get(pk=self._save(request, c).pk)))

    def delete(self, request, pk):
        get_or_404(Cours, pk).delete()
        return Response(status=204)


class MonEmploiDuTemps(APIView):
    def get(self, request):
        if request.user.role != 'PROFESSEUR':
            raise Refus()
        qs = cours_qs().filter(matiere__professeur__utilisateur=request.user)
        if request.query_params.get('annee'):
            qs = qs.filter(matiere__classe__annee_id=request.query_params['annee'])
        out = []
        for c in qs.order_by('jour', 'heure_debut'):
            d = ser_cours(c)
            d['effectif'] = sv.classe_effectif(c.matiere.classe)
            out.append(d)
        return Response(out)
