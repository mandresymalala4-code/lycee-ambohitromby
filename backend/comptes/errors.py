"""Format d'erreur unique : { status, code, message, champs } (§12.2)."""
import logging
from django.db import IntegrityError
from django.db.models import ProtectedError, RestrictedError
from django.http import Http404
from rest_framework import exceptions as E
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

log = logging.getLogger('lycee')
MSG = {
    401: 'Votre session a expiré. Veuillez vous reconnecter.',
    403: "Vous n'avez pas le droit d'effectuer cette action.",
    404: "Cet élément n'existe plus.",
    500: 'Une erreur est survenue. Veuillez réessayer ou contacter l\'administrateur.',
}


class ApiError(E.APIException):
    status_code = 400
    default_code = 'ERREUR'

    def __init__(self, message, champs=None, code=None, status=None):
        self.message = message
        self.champs = champs or {}
        self.code = code or self.default_code
        if status:
            self.status_code = status
        super().__init__(message)


def Conflit(message, champ=None, code='CONFLIT'):
    return ApiError(message, {champ: message} if champ else {}, code, 409)


def Invalide(message, champ=None, code='DONNEES_INVALIDES'):
    return ApiError(message, {champ: message} if champ else {}, code, 400)


def Refus(message=None, code='ACCES_REFUSE'):
    return ApiError(message or MSG[403], {}, code, 403)


def Introuvable(message=None):
    return ApiError(message or MSG[404], {}, 'INTROUVABLE', 404)


def _flatten(detail, prefix=''):
    out = {}
    if isinstance(detail, dict):
        for k, v in detail.items():
            out.update(_flatten(v, f'{prefix}.{k}' if prefix else k))
    elif isinstance(detail, list):
        if detail and all(isinstance(x, (str, E.ErrorDetail)) for x in detail):
            out[prefix or 'non_field_errors'] = str(detail[0])
        else:
            for i, v in enumerate(detail):
                out.update(_flatten(v, f'{prefix}.{i}' if prefix else str(i)))
    else:
        out[prefix or 'non_field_errors'] = str(detail)
    return out


def body(status, code, message, champs=None):
    return Response({'status': status, 'code': code, 'message': message, 'champs': champs or {}}, status=status)


def exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return body(exc.status_code, exc.code, exc.message, exc.champs)
    if isinstance(exc, (E.NotAuthenticated, E.AuthenticationFailed, InvalidToken, TokenError)):
        return body(401, 'SESSION_EXPIREE', MSG[401])
    if isinstance(exc, E.PermissionDenied):
        m = str(exc.detail)
        return body(403, 'ACCES_REFUSE', MSG[403] if m.startswith('You do not') else m)
    if isinstance(exc, (Http404, E.NotFound)):
        return body(404, 'INTROUVABLE', MSG[404])
    if isinstance(exc, E.ValidationError):
        champs = _flatten(exc.detail)
        first = next(iter(champs.values()), 'Données invalides.')
        champs.pop('non_field_errors', None)
        return body(400, 'DONNEES_INVALIDES', first, champs)
    if isinstance(exc, (ProtectedError, RestrictedError)):
        return body(409, 'SUPPRESSION_IMPOSSIBLE',
                    'Cet élément est utilisé ailleurs dans l\'application. Suppression impossible.')
    if isinstance(exc, IntegrityError):
        return body(409, 'DOUBLON', 'Cette valeur existe déjà ou est invalide (doublon ou contrainte).')
    if isinstance(exc, E.Throttled):
        return body(429, 'TROP_DE_TENTATIVES', 'Trop de tentatives. Réessayez dans 15 minutes.')
    if isinstance(exc, (E.ParseError, E.UnsupportedMediaType)):
        return body(400, 'REQUETE_INVALIDE', 'Requête invalide.')
    if isinstance(exc, E.MethodNotAllowed):
        return body(405, 'METHODE_INTERDITE', 'Méthode non autorisée.')
    if isinstance(exc, E.APIException):
        return body(exc.status_code, 'ERREUR', str(exc.detail))
    log.exception('Erreur interne', exc_info=exc)
    return body(500, 'ERREUR_INTERNE', MSG[500])


# Pages d'erreur hors DRF (URL inconnue, erreur serveur) : toujours du JSON au même format
def _json(status, code, message):
    from django.http import JsonResponse
    return JsonResponse({'status': status, 'code': code, 'message': message, 'champs': {}}, status=status)


def json_404(request, exception=None):
    return _json(404, 'INTROUVABLE', MSG[404])


def json_500(request):
    return _json(500, 'ERREUR_INTERNE', MSG[500])


def json_403(request, exception=None):
    return _json(403, 'ACCES_REFUSE', MSG[403])


def json_400(request, exception=None):
    return _json(400, 'REQUETE_INVALIDE', 'Requête invalide.')
