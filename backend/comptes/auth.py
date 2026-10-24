from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class StatutJWTAuthentication(JWTAuthentication):
    """Refuse un jeton dont le compte n'est plus actif (suspendu, refusé…)."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.statut != 'VALIDE':
            raise AuthenticationFailed('Compte inactif.')
        return user
