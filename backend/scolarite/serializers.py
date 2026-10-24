import re
from django.conf import settings
from rest_framework import serializers as S
from comptes import validators as V
from comptes.errors import ApiError
from .models import MODES_PAIEMENT


def vide(v):
    return not (v or '').strip()


class EleveIn(S.Serializer):
    nom = S.CharField(max_length=200)
    prenoms = S.CharField(max_length=200)
    date_naissance = S.DateField(error_messages={'invalid': 'Date de naissance hors limites.'})
    sexe = S.ChoiceField(['Garçon', 'Fille'], error_messages={'invalid_choice': 'Veuillez sélectionner le sexe.'})
    adresse = S.CharField(max_length=300)
    observation = S.CharField(required=False, allow_blank=True, default='')

    def validate_nom(self, v): return V.v_nom(v)
    def validate_prenoms(self, v): return V.v_prenom(v)
    def validate_date_naissance(self, v): return V.v_naissance(v, 'ELEVE')
    def validate_adresse(self, v): return V.v_adresse(v)
    def validate_observation(self, v): return V.v_obs(v)


class FamilleIn(S.Serializer):
    pere_nom = S.CharField(required=False, allow_blank=True, default='')
    pere_prenoms = S.CharField(required=False, allow_blank=True, default='')
    mere_nom = S.CharField(required=False, allow_blank=True, default='')
    mere_prenoms = S.CharField(required=False, allow_blank=True, default='')
    contact_parent = S.CharField()
    adresse_parents = S.CharField(max_length=300)
    tuteur_nom = S.CharField(required=False, allow_blank=True, default='')
    tuteur_prenoms = S.CharField(required=False, allow_blank=True, default='')
    tuteur_contact = S.CharField(required=False, allow_blank=True, default='')

    def validate_contact_parent(self, v): return V.v_tel(v)
    def validate_adresse_parents(self, v): return V.v_adresse(v)

    def validate(self, d):
        err = {}
        any_resp = False
        for p in ('pere', 'mere', 'tuteur'):
            n, pr = d.get(f'{p}_nom', ''), d.get(f'{p}_prenoms', '')
            if vide(n) and vide(pr):
                d[f'{p}_nom'] = d[f'{p}_prenoms'] = ''
                continue
            any_resp = True
            try:
                d[f'{p}_nom'] = V.v_nom(n)
            except S.ValidationError as e:
                err[f'{p}_nom'] = e.detail[0]
            try:
                d[f'{p}_prenoms'] = V.v_prenom(pr)
            except S.ValidationError as e:
                err[f'{p}_prenoms'] = e.detail[0]
        if not any_resp and not err:
            err['pere_nom'] = 'Renseignez au moins un responsable (père, mère ou tuteur).'
        if not vide(d.get('tuteur_nom')) or not vide(d.get('tuteur_contact')):
            try:
                d['tuteur_contact'] = V.v_tel(d.get('tuteur_contact', ''))
            except S.ValidationError as e:
                err['tuteur_contact'] = e.detail[0]
        else:
            d['tuteur_contact'] = ''
        if err:
            raise S.ValidationError(err)
        return d


class InscriptionIn(S.Serializer):
    annee = S.IntegerField(error_messages={'required': 'Veuillez choisir l\'année scolaire.', 'invalid': 'Veuillez choisir l\'année scolaire.'})
    classe = S.IntegerField(error_messages={'required': 'Veuillez choisir une classe.', 'invalid': 'Veuillez choisir une classe.'})
    eleve_id = S.IntegerField(required=False, allow_null=True)
    eleve = EleveIn()
    famille = FamilleIn()
    mode_paiement = S.ChoiceField(MODES_PAIEMENT, error_messages={'invalid_choice': 'Veuillez choisir le mode de paiement.', 'required': 'Veuillez choisir le mode de paiement.'})
    rattacher_famille = S.BooleanField(required=False, default=False)


class ClasseIn(S.Serializer):
    nom = S.CharField(min_length=2, max_length=50, error_messages={'min_length': 'Le nom doit contenir entre 2 et 50 caractères.', 'max_length': 'Le nom doit contenir entre 2 et 50 caractères.', 'blank': 'Ce champ est obligatoire.'})
    droit_inscription = S.IntegerField(min_value=0, max_value=10_000_000, error_messages={'min_value': 'Montant invalide.', 'max_value': 'Montant invalide.', 'invalid': 'Montant invalide.'})
    caisse_soutien = S.IntegerField(min_value=0, max_value=10_000_000, error_messages={'min_value': 'Montant invalide.', 'max_value': 'Montant invalide.', 'invalid': 'Montant invalide.'})
    annee = S.IntegerField(required=False)


class MatiereIn(S.Serializer):
    classe = S.IntegerField(required=False)
    nom = S.CharField(required=False, error_messages={'blank': 'La matière doit contenir entre 2 et 100 caractères.'})
    coefficient = S.IntegerField(min_value=1, max_value=6, error_messages={'min_value': 'Le coefficient doit être compris entre 1 et 6.', 'max_value': 'Le coefficient doit être compris entre 1 et 6.', 'invalid': 'Le coefficient doit être compris entre 1 et 6.', 'required': 'Le coefficient doit être compris entre 1 et 6.'})
    professeur = S.IntegerField(required=False, allow_null=True)

    def validate_nom(self, v):
        v = ' '.join(v.split())
        if not (2 <= len(v) <= 100):
            raise S.ValidationError('La matière doit contenir entre 2 et 100 caractères.')
        return v


def v_heure(v, champ):
    m = re.fullmatch(r'(\d{1,2}):(\d{2})(:\d{2})?', str(v or ''))
    if not m:
        raise S.ValidationError({champ: 'Les cours ont lieu entre 07:00 et 18:00.'})
    h, mi = int(m[1]), int(m[2])
    if mi not in (0, 30) or not (7 * 60 <= h * 60 + mi <= 18 * 60):
        raise S.ValidationError({champ: 'Les cours ont lieu entre 07:00 et 18:00 (pas de 30 minutes).'})
    from datetime import time
    return time(h, mi)


class CoursIn(S.Serializer):
    matiere = S.IntegerField(error_messages={'required': 'Veuillez choisir une matière.', 'invalid': 'Veuillez choisir une matière.'})
    jour = S.IntegerField(min_value=1, max_value=5, error_messages={'min_value': 'Les cours ont lieu du lundi au vendredi.', 'max_value': 'Les cours ont lieu du lundi au vendredi.', 'required': 'Les cours ont lieu du lundi au vendredi.', 'invalid': 'Les cours ont lieu du lundi au vendredi.'})
    heure_debut = S.CharField()
    heure_fin = S.CharField()
    salle = S.CharField(required=False, allow_blank=True, max_length=30, default='')

    def validate(self, d):
        d['heure_debut'] = v_heure(d['heure_debut'], 'heure_debut')
        d['heure_fin'] = v_heure(d['heure_fin'], 'heure_fin')
        if d['heure_debut'].hour * 60 + d['heure_debut'].minute >= 18 * 60 or d['heure_debut'] >= d['heure_fin']:
            raise S.ValidationError({'heure_fin': 'L\'heure de fin doit être postérieure à l\'heure de début.'})
        return d


def photo_url(f):
    return f.url if f else None
