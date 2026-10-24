from django.core.management.base import BaseCommand
from django.db import transaction
from absences.models import Absence, Appel
from comptes.models import DonneeDemo, Discipline, Professeur, Utilisateur
from notes.models import Note
from scolarite.models import Eleve, Famille, Inscription, Matiere, Paiement


def effacer():
    ids = lambda m: list(DonneeDemo.objects.filter(modele=m).values_list('objet_id', flat=True))
    users, eleves, fams, discs = ids('Utilisateur'), ids('Eleve'), ids('Famille'), ids('Discipline')
    with transaction.atomic():
        ins = Inscription.objects.filter(eleve_id__in=eleves)
        matric = list(Eleve.objects.filter(id__in=eleves).values_list('matricule', flat=True))
        Absence.objects.filter(inscription__in=ins).delete()
        Appel.objects.filter(matiere__professeur__utilisateur_id__in=users).delete()
        Note.objects.filter(inscription__in=ins).delete()
        Paiement.objects.filter(inscription__in=ins).delete()
        Paiement.objects.filter(eleve_matricule__in=matric).delete()
        n_ins = ins.count()
        ins.delete()
        Eleve.objects.filter(id__in=eleves).delete()
        Famille.objects.filter(id__in=fams, eleves__isnull=True).delete()
        Matiere.objects.filter(professeur__utilisateur_id__in=users).delete()
        Utilisateur.objects.filter(id__in=users).delete()
        Discipline.objects.filter(id__in=discs, matieres__isnull=True, professeurs__isnull=True).delete()
        DonneeDemo.objects.all().delete()
    return n_ins


class Command(BaseCommand):
    help = "Efface les données de démonstration sans toucher aux données réelles."

    def handle(self, *a, **o):
        n = effacer()
        self.stdout.write(self.style.SUCCESS(f'Données de démonstration effacées ({n} inscriptions).'))
