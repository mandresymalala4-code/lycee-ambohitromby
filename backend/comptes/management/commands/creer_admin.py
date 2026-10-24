import getpass
from datetime import date
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from comptes import validators as V
from comptes.models import Utilisateur


class Command(BaseCommand):
    help = "Crée le compte Administrateur (email et mot de passe demandés si absents)."

    def add_arguments(self, p):
        p.add_argument('--email'); p.add_argument('--password')
        p.add_argument('--nom', default='ADMINISTRATEUR'); p.add_argument('--prenom', default='Principal')
        p.add_argument('--telephone', default='0340000001'); p.add_argument('--adresse', default='Ambohitromby, Antananarivo')
        p.add_argument('--naissance', default='1980-01-01'); p.add_argument('--sexe', default='Homme')

    def handle(self, *a, **o):
        email = o['email'] or input('Email de l\'administrateur : ')
        pw = o['password'] or getpass.getpass('Mot de passe : ')
        if not o['password']:
            if getpass.getpass('Confirmation : ') != pw:
                raise CommandError('Les mots de passe ne correspondent pas.')
        try:
            email = V.v_email(email); V.v_mdp(pw)
            nom, prenom = V.v_nom(o['nom']), V.v_prenom(o['prenom'])
            tel = V.v_tel(o['telephone']); adr = V.v_adresse(o['adresse'])
            naiss = V.v_naissance(date.fromisoformat(o['naissance']), 'ADMIN')
        except ValidationError as e:
            raise CommandError(str(e.detail[0]))
        if Utilisateur.objects.filter(email__iexact=email).exists() or Utilisateur.objects.filter(telephone=tel).exists():
            raise CommandError('Email ou téléphone déjà utilisé.')
        Utilisateur.objects.create_user(email, pw, role='ADMIN', nom=nom, prenom=prenom, date_naissance=naiss, sexe=o['sexe'],
                                        adresse=adr, telephone=tel, statut='VALIDE')
        self.stdout.write(self.style.SUCCESS(f'Administrateur {email} créé.'))
