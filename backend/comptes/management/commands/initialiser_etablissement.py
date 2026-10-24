from django.core.management.base import BaseCommand
from comptes.models import Etablissement
from scolarite import services as sv


class Command(BaseCommand):
    help = "Initialise l'établissement, les années 2020-2046, les trimestres et les sept classes de l'année courante."

    def handle(self, *a, **o):
        Etablissement.get()
        sv.ensure_toutes_annees()
        an = sv.annee_courante()
        sv.ensure_classes(an)
        self.stdout.write(self.style.SUCCESS(f'Établissement initialisé. Année courante : {an.libelle} (7 classes, 3 trimestres).'))
