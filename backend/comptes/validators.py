import re
import uuid
from datetime import date
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjVE
from PIL import Image
from rest_framework import serializers

LET = 'A-ZÀ-ÖØ-Þ'
RE_NOM = re.compile(rf"^[{LET} '’\-]+$")
RE_PRENOM_TOK = re.compile(r"^[A-ZÀ-ÖØ-Þ][a-zß-öø-ÿ'’]*$")


def ve(msg):
    return serializers.ValidationError(msg)


def v_nom(v):
    v = ' '.join((v or '').split())
    if not (2 <= len(v) <= 100) or v != v.upper() or not RE_NOM.match(v) or len(re.findall(f'[{LET}]', v)) < 2:
        raise ve('Le nom doit être en majuscules (2 à 100 caractères).')
    return v


def v_prenom(v):
    v = ' '.join((v or '').split())
    toks = [t for t in re.split(r'[ \-]', v) if t]
    if not (2 <= len(v) <= 100) or not toks or any(not RE_PRENOM_TOK.match(t) for t in toks):
        raise ve('Le prénom doit commencer par une majuscule suivie de minuscules.')
    return v


def v_adresse(v):
    v = (v or '').strip()
    if not (3 <= len(v) <= 120):
        raise ve('L\'adresse doit contenir entre 3 et 120 caractères.')
    return v


def v_tel(v, fixe=False):
    d = re.sub(r'[\s.\-]', '', v or '')
    ok = re.fullmatch(r'0[23]\d{8}' if fixe else r'03\d{8}', d)
    if not ok:
        raise ve('Téléphone invalide (10 chiffres, commençant par 03).')
    return d


def v_email(v):
    v = (v or '').strip().lower()
    try:
        validate_email(v)
    except DjVE:
        raise ve('Adresse email invalide.')
    if len(v) > 150:
        raise ve('Adresse email invalide.')
    return v


def v_mdp(v):
    if not v or not (8 <= len(v) <= 128) or not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
        raise ve('Le mot de passe doit contenir au moins 8 caractères avec des lettres et des chiffres.')
    return v


def v_cin(v):
    d = re.sub(r'\s', '', v or '')
    if not re.fullmatch(r'\d{14}', d):
        raise ve('Le CIN doit contenir exactement 14 chiffres.')
    return d


def age(d, today=None):
    t = today or date.today()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


def v_naissance(d, role):
    if role == 'ELEVE':
        mn, mx = date.fromisoformat(settings.ELEVE_NAISSANCE_MIN), date.fromisoformat(settings.ELEVE_NAISSANCE_MAX)
        if not (mn <= d <= mx):
            raise ve('Date de naissance hors limites.')
    else:
        mini = 21 if role == 'PROFESSEUR' else 18
        if d <= date(1950, 1, 1) or age(d) < mini:
            raise ve(f'Date de naissance invalide ({mini} ans minimum).')
    return d


def v_photo(f):
    if f is None:
        return f
    ext = (f.name.rsplit('.', 1)[-1] if '.' in f.name else '').lower()
    if ext not in ('jpg', 'jpeg', 'png') or f.size > 2 * 1024 * 1024:
        raise ve('Format de photo non accepté (JPG ou PNG, 2 Mo maximum).')
    try:
        img = Image.open(f)
        img.verify()
        f.seek(0)
    except Exception:
        raise ve('Format de photo non accepté (JPG ou PNG, 2 Mo maximum).')
    f.name = f'{uuid.uuid4().hex}.{"png" if ext == "png" else "jpg"}'
    return f


def v_logo(f):
    try:
        return v_photo(f)
    except serializers.ValidationError:
        raise ve('Format de logo non accepté.')


def v_obs(v):
    v = (v or '').strip()
    if len(v) > 255:
        raise ve('255 caractères maximum.')
    return v
