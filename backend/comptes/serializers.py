from rest_framework import serializers as S
from . import validators as V
from .models import Utilisateur, Professeur


def photo_url(f):
    return f.url if f else None


def ser_prof_fields(p):
    return {'id': p.id, 'code': p.code, 'cin': p.cin, 'discipline': p.discipline_id, 'discipline_nom': p.discipline.nom,
            'observation': p.observation}


def ser_user(u):
    d = {'id': u.id, 'email': u.email, 'role': u.role, 'nom': u.nom, 'prenom': u.prenom, 'nom_complet': u.nom_complet,
         'sexe': u.sexe, 'date_naissance': u.date_naissance, 'adresse': u.adresse, 'telephone': u.telephone,
         'photo': photo_url(u.photo), 'statut': u.statut, 'theme': u.theme, 'doit_changer_mdp': u.doit_changer_mdp,
         'annee_preferee': u.annee_preferee, 'professeur': None}
    if u.role == 'PROFESSEUR':
        d['professeur'] = ser_prof_fields(u.professeur)
    return d


class ProfesseurIn(S.Serializer):
    """Création de compte (§5.2), ajout par l'admin et modification (§6.8)."""
    nom = S.CharField()
    prenom = S.CharField()
    date_naissance = S.DateField(error_messages={'invalid': 'Date de naissance invalide (21 ans minimum).'})
    sexe = S.ChoiceField(['Homme', 'Femme'], error_messages={'invalid_choice': 'Veuillez sélectionner le sexe.'})
    adresse = S.CharField()
    telephone = S.CharField()
    email = S.CharField(max_length=300)
    cin = S.CharField()
    matiere = S.CharField(error_messages={'blank': 'Veuillez indiquer la matière enseignée.', 'required': 'Veuillez indiquer la matière enseignée.'})
    mot_de_passe = S.CharField(required=False, allow_blank=True, trim_whitespace=False)
    confirmation = S.CharField(required=False, allow_blank=True, trim_whitespace=False)
    photo = S.FileField(required=False, allow_null=True)
    observation = S.CharField(required=False, allow_blank=True, default='')

    def validate_nom(self, v): return V.v_nom(v)
    def validate_prenom(self, v): return V.v_prenom(v)
    def validate_date_naissance(self, v): return V.v_naissance(v, 'PROFESSEUR')
    def validate_adresse(self, v): return V.v_adresse(v)
    def validate_telephone(self, v): return V.v_tel(v)
    def validate_email(self, v): return V.v_email(v)
    def validate_cin(self, v): return V.v_cin(v)
    def validate_photo(self, v): return V.v_photo(v)
    def validate_observation(self, v): return V.v_obs(v)

    def validate_matiere(self, v):
        v = ' '.join(v.split())
        if not (2 <= len(v) <= 100):
            raise S.ValidationError('Veuillez indiquer la matière enseignée.')
        return v

    def validate(self, d):
        mode = self.context.get('mode', 'register')
        pw, conf = d.get('mot_de_passe', ''), d.get('confirmation', '')
        if mode in ('register', 'create') or pw:
            try:
                V.v_mdp(pw)
            except S.ValidationError as e:
                raise S.ValidationError({'mot_de_passe': e.detail[0]})
            if pw != conf:
                raise S.ValidationError({'confirmation': 'Les mots de passe ne correspondent pas.'})
        return d
