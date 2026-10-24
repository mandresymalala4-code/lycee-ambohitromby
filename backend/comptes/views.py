from datetime import date, timedelta
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from . import validators as V
from .errors import ApiError, Conflit, Introuvable, Invalide, Refus
from .models import Discipline, Etablissement, Professeur, Utilisateur, audit
from .permissions import AdminOuLecture, EstAdmin
from .serializers import ProfesseurIn, ser_prof_fields, ser_user, photo_url
from .services import discipline_pour, prochain_code_prof

MSG_ATTENTE = 'Votre compte est en attente de validation par l\'administrateur.'
MSG_INACTIF = 'Votre compte n\'est pas actif. Contactez l\'administration du lycée.'
MSG_VERROU = 'Trop de tentatives. Réessayez dans 15 minutes.'
MULTI = [JSONParser, MultiPartParser, FormParser]


class Login(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        pw = request.data.get('password') or ''
        champs = {}
        if not email:
            champs['email'] = 'Ce champ est obligatoire.'
        else:
            try:
                V.v_email(email)
            except Exception:
                champs['email'] = 'Adresse email invalide.'
        if not pw:
            champs['password'] = 'Ce champ est obligatoire.'
        if champs:
            raise ApiError(next(iter(champs.values())), champs, 'DONNEES_INVALIDES', 400)
        u = Utilisateur.objects.filter(email__iexact=email).first()
        now = timezone.now()
        if u and u.verrouille_jusqu_a and u.verrouille_jusqu_a > now:
            raise ApiError(MSG_VERROU, {}, 'COMPTE_VERROUILLE', 429)
        if not u or not check_password(pw, u.password):
            if u:
                u.tentatives_echec += 1
                if u.tentatives_echec >= 5:
                    u.tentatives_echec = 0
                    u.verrouille_jusqu_a = now + timedelta(minutes=15)
                u.save(update_fields=['tentatives_echec', 'verrouille_jusqu_a'])
                audit(u, 'CONNEXION_ECHEC', 'utilisateur', u.id, email)
                if u.verrouille_jusqu_a and u.verrouille_jusqu_a > now:
                    raise ApiError(MSG_VERROU, {}, 'COMPTE_VERROUILLE', 429)
            raise ApiError('Email ou mot de passe incorrect.', {}, 'IDENTIFIANTS_INCORRECTS', 401)
        if u.statut == 'EN_ATTENTE':
            raise ApiError(MSG_ATTENTE, {}, 'COMPTE_EN_ATTENTE', 403)
        if u.statut != 'VALIDE':
            raise ApiError(MSG_INACTIF, {}, 'COMPTE_INACTIF', 403)
        u.tentatives_echec, u.verrouille_jusqu_a = 0, None
        u.save(update_fields=['tentatives_echec', 'verrouille_jusqu_a'])
        r = RefreshToken.for_user(u)
        audit(u, 'CONNEXION', 'utilisateur', u.id)
        return Response({'access': str(r.access_token), 'refresh': str(r), 'role': u.role, 'statut': u.statut, 'user': ser_user(u)})


class Logout(APIView):
    """Déconnexion : le jeton de rafraîchissement est mis sur liste noire (inutilisable après coup)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken as RT
        refresh = request.data.get('refresh')
        if refresh:
            try:
                t = RT(refresh)
                uid = t.get('user_id')
                t.blacklist()
                u = Utilisateur.objects.filter(pk=uid).first()
                if u:
                    audit(u, 'DECONNEXION', 'utilisateur', u.id)
            except Exception:
                pass
        return Response(status=204)


def verifier_unicite(d, exclude_user=None, exclude_prof=None):
    err = {}
    u = Utilisateur.objects.exclude(pk=exclude_user) if exclude_user else Utilisateur.objects.all()
    if u.filter(email__iexact=d['email']).exists():
        err['email'] = 'Email déjà utilisé.'
    if u.filter(telephone=d['telephone']).exists():
        err['telephone'] = 'Téléphone déjà utilisé.'
    p = Professeur.objects.exclude(pk=exclude_prof) if exclude_prof else Professeur.objects.all()
    if p.filter(cin=d['cin']).exists():
        err['cin'] = 'CIN déjà utilisé.'
    if err:
        raise ApiError(next(iter(err.values())), err, 'DOUBLON', 409)


def valider_profs(request, mode):
    s = ProfesseurIn(data=request.data, context={'mode': mode})
    s.is_valid(raise_exception=True)
    return s.validated_data


class RegisterProfesseur(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        d = valider_profs(request, 'register')
        verifier_unicite(d)
        disc = discipline_pour(d['matiere'])
        u = Utilisateur(email=d['email'], role='PROFESSEUR', nom=d['nom'], prenom=d['prenom'], date_naissance=d['date_naissance'],
                        sexe=d['sexe'], adresse=d['adresse'], telephone=d['telephone'], statut='EN_ATTENTE', photo=d.get('photo'))
        u.set_password(d['mot_de_passe'])
        u.save()
        Professeur.objects.create(utilisateur=u, cin=d['cin'], discipline=disc)
        audit(u, 'CREATION_COMPTE_PROF', 'utilisateur', u.id, u.email)
        return Response({'message': 'Votre compte a été créé. Il sera actif après validation par l\'administrateur.'}, status=201)


class MotDePasseOublie(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        tel = V.re.sub(r'\s', '', request.data.get('telephone') or '')
        ip = request.META.get('REMOTE_ADDR', '')
        key = f'mdp_oublie:{ip}:{email}'
        n = cache.get(key, 0)
        if n >= 5:
            raise ApiError(MSG_VERROU, {}, 'TROP_DE_TENTATIVES', 429)
        cache.set(key, n + 1, 15 * 60)
        champs = {}
        if not email:
            champs['email'] = 'Ce champ est obligatoire.'
        if not tel:
            champs['telephone'] = 'Ce champ est obligatoire.'
        pw, conf = request.data.get('mot_de_passe') or '', request.data.get('confirmation') or ''
        try:
            V.v_mdp(pw)
        except Exception as e:
            champs['mot_de_passe'] = 'Le mot de passe doit contenir au moins 8 caractères avec des lettres et des chiffres.'
        if pw != conf:
            champs['confirmation'] = 'Les mots de passe ne correspondent pas.'
        if champs:
            raise ApiError(next(iter(champs.values())), champs, 'DONNEES_INVALIDES', 400)
        u = Utilisateur.objects.filter(email__iexact=email, telephone=tel).first()
        if not u:
            raise ApiError('Les informations saisies ne correspondent à aucun compte.', {}, 'COMPTE_INTROUVABLE', 400)
        if check_password(pw, u.password):
            raise Invalide('Le nouveau mot de passe ne peut pas être identique à l\'ancien.', 'mot_de_passe')
        u.set_password(pw)
        u.tentatives_echec, u.verrouille_jusqu_a = 0, None
        u.save()
        cache.delete(key)
        audit(u, 'CHANGEMENT_MDP', 'utilisateur', u.id, 'récupération')
        return Response({'message': 'Mot de passe modifié. Vous pouvez vous reconnecter.'})


class DisciplinesView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response([{'id': d.id, 'nom': d.nom} for d in Discipline.objects.all()])


# ---------- Professeurs ----------
def row_prof(p, admin=True):
    u = p.utilisateur
    d = {'id': p.id, 'code': p.code, 'nom': u.nom, 'prenoms': u.prenom, 'sexe': u.sexe, 'matiere': p.discipline_id,
         'matiere_nom': p.discipline.nom, 'telephone': u.telephone, 'email': u.email, 'photo': photo_url(u.photo), 'statut': u.statut}
    if admin:
        d.update(utilisateur=u.id, cin=p.cin, adresse=u.adresse, date_naissance=u.date_naissance, observation=p.observation,
                 date_creation=u.date_creation, motif_refus=u.motif_refus)
    return d


def profs_qs():
    return Professeur.objects.select_related('utilisateur', 'discipline')


class ProfesseursView(APIView):
    permission_classes = [AdminOuLecture]
    parser_classes = MULTI

    def get(self, request, pk=None):
        admin = request.user.role == 'ADMIN'
        if pk:
            p = profs_qs().filter(pk=pk).first()
            if not p or (not admin and p.utilisateur.statut != 'VALIDE'):
                raise Introuvable()
            return Response(row_prof(p, admin))
        qs = profs_qs().filter(utilisateur__statut__in=['VALIDE', 'SUSPENDU'] if admin else ['VALIDE'])
        qp = request.query_params
        if qp.get('sexe'):
            qs = qs.filter(utilisateur__sexe=qp['sexe'])
        if qp.get('matiere'):
            qs = qs.filter(discipline_id=qp['matiere']) if str(qp['matiere']).isdigit() else qs.filter(discipline__nom__iexact=qp['matiere'])
        q = (qp.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(utilisateur__nom__icontains=q) | Q(utilisateur__prenom__icontains=q) | Q(code__icontains=q))
        return Response([row_prof(p, admin) for p in qs.order_by('utilisateur__nom', 'utilisateur__prenom')])

    @transaction.atomic
    def post(self, request):
        if request.user.role != 'ADMIN':
            raise Refus()
        d = valider_profs(request, 'create')
        verifier_unicite(d)
        disc = discipline_pour(d['matiere'])
        u = Utilisateur(email=d['email'], role='PROFESSEUR', nom=d['nom'], prenom=d['prenom'], date_naissance=d['date_naissance'],
                        sexe=d['sexe'], adresse=d['adresse'], telephone=d['telephone'], statut='VALIDE', photo=d.get('photo'),
                        doit_changer_mdp=True, valide_par=request.user)
        u.set_password(d['mot_de_passe'])
        u.save()
        p = Professeur.objects.create(utilisateur=u, cin=d['cin'], discipline=disc, code=prochain_code_prof(), observation=d['observation'])
        audit(request.user, 'CREATION_PROF', 'professeur', p.id, p.code)
        return Response(row_prof(profs_qs().get(pk=p.pk)), status=201)

    @transaction.atomic
    def put(self, request, pk):
        p = profs_qs().filter(pk=pk).first()
        if not p:
            raise Introuvable()
        d = valider_profs(request, 'update')
        u = p.utilisateur
        verifier_unicite(d, u.pk, p.pk)
        disc = discipline_pour(d['matiere'])
        if disc.id != p.discipline_id and p.matieres.exists():
            raise Conflit('Ce professeur est affecté à des matières. Retirez d\'abord ces affectations.', 'matiere', 'PROF_AFFECTE')
        for k in ('nom', 'prenom', 'date_naissance', 'sexe', 'adresse', 'telephone', 'email'):
            setattr(u, k, d[k])
        if d.get('photo'):
            u.photo = d['photo']
        if d.get('mot_de_passe'):
            u.set_password(d['mot_de_passe'])
        u.save()
        p.cin, p.discipline, p.observation = d['cin'], disc, d['observation']
        p.save()
        audit(request.user, 'MODIF_PROF', 'professeur', p.id, p.code or '')
        return Response(row_prof(profs_qs().get(pk=p.pk)))

    @transaction.atomic
    def delete(self, request, pk):
        if request.user.role != 'ADMIN':
            raise Refus()
        p = profs_qs().filter(pk=pk).first()
        if not p:
            raise Introuvable()
        u = p.utilisateur
        from absences.models import Appel
        from notes.models import Note
        if Note.objects.filter(saisi_par=u).exists() or Appel.objects.filter(saisi_par=u).exists():
            raise Conflit('Ce professeur a saisi des notes ou des appels. Suppression impossible. Vous pouvez le suspendre.', code='PROF_AVEC_DONNEES')
        for m in p.matieres.all():
            m.cours.all().delete()
            m.professeur = None
            m.save(update_fields=['professeur'])
        audit(request.user, 'SUPPRESSION_PROF', 'professeur', p.id, p.code or u.email)
        u.delete()
        return Response(status=204)


class ProfsEnAttente(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        qs = profs_qs().filter(utilisateur__statut__in=['EN_ATTENTE', 'REFUSE']).order_by('-utilisateur__date_creation')
        return Response([row_prof(p) for p in qs])


class ProfAction(APIView):
    permission_classes = [EstAdmin]
    action = ''

    @transaction.atomic
    def post(self, request, pk):
        p = profs_qs().filter(pk=pk).first()
        if not p:
            raise Introuvable()
        u = p.utilisateur
        a = self.action
        if a == 'valider':
            u.statut, u.valide_par, u.motif_refus = 'VALIDE', request.user, ''
            if not p.code:
                p.code = prochain_code_prof()
                p.save(update_fields=['code'])
        elif a == 'refuser':
            u.statut, u.motif_refus = 'REFUSE', (request.data.get('motif') or '')[:255]
        elif a == 'suspendre':
            if u.statut != 'VALIDE':
                raise Invalide('Seul un compte validé peut être suspendu.')
            u.statut = 'SUSPENDU'
        elif a == 'reactiver':
            if u.statut != 'SUSPENDU':
                raise Invalide('Ce compte n\'est pas suspendu.')
            u.statut = 'VALIDE'
        u.save()
        audit(request.user, f'PROF_{a.upper()}', 'professeur', p.id, u.email)
        return Response(row_prof(profs_qs().get(pk=p.pk)))


# ---------- Profil ----------
class ProfilView(APIView):
    parser_classes = MULTI

    def get(self, request):
        return Response(ser_user(request.user))

    @transaction.atomic
    def put(self, request):
        u, data = request.user, request.data
        admin = u.role == 'ADMIN'
        editables = ['adresse', 'telephone'] + (['nom', 'prenom', 'date_naissance', 'sexe', 'email'] if admin else [])
        err = {}

        def champ(k, fn):
            if k in data:
                try:
                    return fn(data[k])
                except Exception as e:
                    err[k] = str(getattr(e, 'detail', [e])[0]) if hasattr(e, 'detail') else str(e)
            return None

        vals = {}
        fns = {'adresse': V.v_adresse, 'telephone': V.v_tel, 'nom': V.v_nom, 'prenom': V.v_prenom, 'email': V.v_email,
               'sexe': lambda v: v if v in ('Homme', 'Femme') else (_ for _ in ()).throw(Exception('Veuillez sélectionner le sexe.')),
               'date_naissance': lambda v: V.v_naissance(date.fromisoformat(str(v)), 'ADMIN')}
        for k in editables:
            if k in data:
                vals[k] = champ(k, fns[k])
        if 'theme' in data and data['theme'] in ('CLAIR', 'SOMBRE'):
            u.theme = data['theme']
        if 'annee_preferee' in data and str(data['annee_preferee']).isdigit():
            u.annee_preferee = int(data['annee_preferee'])
        if request.FILES.get('photo'):
            try:
                u.photo = V.v_photo(request.FILES['photo'])
            except Exception:
                err['photo'] = 'Format de photo non accepté (JPG ou PNG, 2 Mo maximum).'
        nouveau = data.get('nouveau_mot_de_passe') or ''
        if nouveau:
            if not check_password(data.get('ancien_mot_de_passe') or '', u.password):
                err['ancien_mot_de_passe'] = 'Mot de passe actuel incorrect.'
            try:
                V.v_mdp(nouveau)
            except Exception:
                err['nouveau_mot_de_passe'] = 'Le mot de passe doit contenir au moins 8 caractères avec des lettres et des chiffres.'
            if nouveau != (data.get('confirmation') or ''):
                err['confirmation'] = 'Les mots de passe ne correspondent pas.'
        if err:
            raise ApiError(next(iter(err.values())), err, 'DONNEES_INVALIDES', 400)
        dup = {}
        if 'email' in vals and Utilisateur.objects.filter(email__iexact=vals['email']).exclude(pk=u.pk).exists():
            dup['email'] = 'Email déjà utilisé.'
        if 'telephone' in vals and Utilisateur.objects.filter(telephone=vals['telephone']).exclude(pk=u.pk).exists():
            dup['telephone'] = 'Téléphone déjà utilisé.'
        if dup:
            raise ApiError(next(iter(dup.values())), dup, 'DOUBLON', 409)
        for k, v in vals.items():
            setattr(u, k, v)
        if nouveau:
            u.set_password(nouveau)
            u.doit_changer_mdp = False
            audit(u, 'CHANGEMENT_MDP', 'utilisateur', u.id)
        u.save()
        return Response(ser_user(u))


# ---------- Paramètres ----------
def ser_etab(e):
    return {'nom': e.nom, 'adresse': e.adresse, 'telephone': e.telephone, 'email': e.email, 'logo': photo_url(e.logo)}


class ParametresView(APIView):
    parser_classes = MULTI

    def get(self, request):
        from scolarite.services import annee_courante
        return Response({'etablissement': ser_etab(Etablissement.get()), 'annee_courante': annee_courante().id})

    @transaction.atomic
    def put(self, request):
        if request.user.role != 'ADMIN':
            raise Refus('Accès réservé à l\'administrateur.')
        e, data, err = Etablissement.get(), request.data, {}
        nom = ' '.join((data.get('nom') or '').split())
        if not (2 <= len(nom) <= 100):
            err['nom'] = 'Le nom doit contenir entre 2 et 100 caractères.'
        try:
            adresse = V.v_adresse(data.get('adresse'))
        except Exception:
            err['adresse'] = 'L\'adresse doit contenir entre 3 et 120 caractères.'
        try:
            tel = V.v_tel(data.get('telephone'), fixe=True)
        except Exception:
            err['telephone'] = 'Téléphone invalide.'
        email = (data.get('email') or '').strip()
        if email:
            try:
                email = V.v_email(email)
            except Exception:
                err['email'] = 'Adresse email invalide.'
        if request.FILES.get('logo'):
            try:
                e.logo = V.v_logo(request.FILES['logo'])
            except Exception:
                err['logo'] = 'Format de logo non accepté.'
        if err:
            raise ApiError(next(iter(err.values())), err, 'DONNEES_INVALIDES', 400)
        e.nom, e.adresse, e.telephone, e.email = nom, adresse, tel, email
        if str(data.get('supprimer_logo')).lower() in ('true', '1'):
            e.logo = None
        e.save()
        if str(data.get('annee_courante') or '').isdigit():
            from scolarite.models import AnneeScolaire
            a = AnneeScolaire.objects.filter(pk=int(data['annee_courante'])).first()
            if a:
                AnneeScolaire.objects.update(courante=False)
                a.courante = True
                a.save(update_fields=['courante'])
        audit(request.user, 'MODIF_PARAMETRES', 'etablissement', e.id)
        from scolarite.services import annee_courante
        return Response({'etablissement': ser_etab(e), 'annee_courante': annee_courante().id})
