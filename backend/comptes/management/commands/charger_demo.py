import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from absences.models import Absence, Appel
from comptes.models import DonneeDemo, Discipline, Professeur, Utilisateur
from comptes.services import prochain_code_prof
from notes.models import Note
from notes.services import recalculer
from scolarite import services as sv
from scolarite.models import Classe, Cours, Eleve, Famille, Inscription, Matiere, Paiement
from .effacer_demo import effacer

PROFS = [('RAKOTO', 'Jean Claude', 'Homme', 'Mathématiques', 1978), ('RANDRIA', 'Marie-Ange', 'Femme', 'Français', 1981),
         ('RABE', 'Hery', 'Homme', 'Anglais', 1985), ('RAZAFY', 'Voahangy', 'Femme', 'Physique-Chimie', 1979),
         ('ANDRIANA', 'Tojo', 'Homme', 'SVT', 1983), ('RASOA', 'Lalaina', 'Femme', 'Histoire-Géographie', 1987)]
COEF = {  # discipline -> coef par défaut ; surcharges par série
    'Mathématiques': 4, 'Français': 3, 'Anglais': 2, 'Physique-Chimie': 3, 'SVT': 2, 'Histoire-Géographie': 2}
SERIE = {'S': {'Mathématiques': 5, 'Physique-Chimie': 4, 'SVT': 3}, 'L': {'Français': 5, 'Histoire-Géographie': 3, 'Anglais': 3, 'Mathématiques': 2, 'Physique-Chimie': 1},
         'OSE': {'SVT': 4, 'Histoire-Géographie': 3}}
CLASSES = [('Seconde', 8), ('1ère L', 4), ('1ère S', 6), ('1ère OSE', 4), ('Terminale L', 6), ('Terminale S', 8), ('Terminale OSE', 4)]
NOMS = ['RAKOTOARISOA', 'RANDRIAMAMPIANINA', 'RAZAFINDRABE', 'RASOLOFONIRINA', 'ANDRIANIRINA', 'RAHARIMANANA', 'RAVELOSON', 'RATSIMBAZAFY',
        'RAKOTONDRAZAKA', 'RAFANOMEZANTSOA', 'ANDRIAMANANA', 'RABEMANANJARA', 'RAJAONARISON', 'RASAMOELINA', 'RAZANAKOTO', 'RAMAROSON',
        'RANDRIANASOLO', 'RAKOTOMALALA', 'ANDRIANTSOA', 'RAZAKAMANANA']
PRENOMS_G = ['Hery', 'Tiana', 'Fanilo', 'Mamy', 'Andry', 'Faniry', 'Toky', 'Rindra', 'Nirina', 'Kanto', 'Njaka', 'Solo', 'Aina', 'Tsiory', 'Mahefa', 'Rado']
PRENOMS_F = ['Voahangy', 'Fara', 'Lalaina', 'Mialy', 'Santatra', 'Hanta', 'Volatiana', 'Noro', 'Haingo', 'Miora', 'Lova', 'Tahina', 'Anja', 'Felana', 'Soa', 'Ony']
QUARTIERS = ['Ambohitromby', 'Ambohijatovo', 'Analakely', 'Itaosy', 'Ankadifotsy', 'Andohalo', 'Isotry', 'Ambatomainty']
MODES = ['Espèces', 'MVola', 'Orange Money', 'Airtel Money', 'Chèque/Virement']


def marquer(modele, obj):
    DonneeDemo.objects.get_or_create(modele=modele, objet_id=obj.pk)


class Command(BaseCommand):
    help = "Charge des données de démonstration (6 professeurs, ~40 élèves, absences, notes sur 2 trimestres)."

    def add_arguments(self, p):
        p.add_argument('--reset', action='store_true', help='Efface d\'abord les anciennes données de démonstration.')

    @transaction.atomic
    def handle(self, *a, **o):
        if DonneeDemo.objects.exists():
            if o['reset']:
                effacer()
            else:
                self.stdout.write(self.style.WARNING('Données de démonstration déjà présentes (utilisez --reset ou effacer_demo).'))
                return
        rnd = random.Random(2026)
        sv.ensure_toutes_annees()
        an = sv.annee_courante()
        sv.ensure_classes(an)
        classes = {c.nom: c for c in Classe.objects.filter(annee=an)}
        profs = {}
        for n, (nom, prenom, sexe, disc, an_n) in enumerate(PROFS, 1):
            d, cr = Discipline.objects.get_or_create(nom=disc)
            if cr:
                marquer('Discipline', d)
            u = Utilisateur.objects.create_user(f'prof{n}@demo.ambohitromby.mg', 'Prof12345', role='PROFESSEUR', nom=nom, prenom=prenom,
                                                date_naissance=date(an_n, 3 + n, 10 + n), sexe=sexe, adresse=f'Lot {n} {rnd.choice(QUARTIERS)}',
                                                telephone=f'034000010{n}', statut='VALIDE')
            marquer('Utilisateur', u)
            profs[disc] = Professeur.objects.create(utilisateur=u, cin=f'1012345678901{n}', discipline=d, code=prochain_code_prof())
        # Matières
        matieres = {}
        for cn, c in classes.items():
            serie = 'S' if cn.endswith('S') else ('L' if cn.endswith('L') else ('OSE' if cn.endswith('OSE') else None))
            for disc, coef in COEF.items():
                coef = SERIE.get(serie, {}).get(disc, coef)
                matieres[(cn, disc)] = Matiere.objects.create(classe=c, discipline=Discipline.objects.get(nom=disc), coefficient=coef, professeur=profs[disc])
        # Emploi du temps : carré latin (aucun conflit classe / professeur)
        slots = [(1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (1, 10), (2, 10)]
        discs = list(COEF)
        for ci, (cn, _) in enumerate(CLASSES):
            for mi, disc in enumerate(discs):
                jour, h = slots[(ci + mi) % 7]
                Cours.objects.create(matiere=matieres[(cn, disc)], jour=jour, heure_debut=f'{h:02d}:00', heure_fin=f'{h + 2:02d}:00', salle=f'Salle {ci + 1}{chr(65 + mi)}')
        # Élèves
        nb = 0
        eleves_par_classe = {}
        fam_courante = None
        for ci, (cn, n_el) in enumerate(CLASSES):
            base = 2011 if cn == 'Seconde' else (2010 if cn.startswith('1') else 2009)
            for k in range(n_el):
                sexe = 'Fille' if (nb % 2) else 'Garçon'
                nom = NOMS[(nb * 3 + ci) % len(NOMS)]
                prenom = rnd.choice(PRENOMS_F if sexe == 'Fille' else PRENOMS_G)
                if k % 4 == 3 and fam_courante is not None and ci == fam_courante[0]:
                    fam = fam_courante[1]                       # frère / sœur : même famille
                    nom = fam.pere_nom
                else:
                    fam = Famille.objects.create(pere_nom=nom, pere_prenoms=rnd.choice(PRENOMS_G), mere_nom=NOMS[(nb * 5 + 1) % len(NOMS)],
                                                 mere_prenoms=rnd.choice(PRENOMS_F), contact_parent=f'03400{2000 + nb:05d}'[:10],
                                                 adresse_parents=f'Lot {10 + nb} {rnd.choice(QUARTIERS)}')
                    marquer('Famille', fam)
                    fam_courante = (ci, fam)
                e = Eleve.objects.create(matricule=sv.prochain_matricule(an.annee_debut), nom=nom, prenoms=prenom, sexe=sexe,
                                         date_naissance=date(base - rnd.randint(0, 2), rnd.randint(1, 12), rnd.randint(1, 28)),
                                         adresse=fam.adresse_parents, famille=fam)
                marquer('Eleve', e)
                c = classes[cn]
                ins = Inscription.objects.create(eleve=e, classe=c, annee=an)
                Paiement.objects.create(inscription=ins, annee=an, numero_recu=sv.prochain_recu(an), droit_inscription=c.droit_inscription,
                                        caisse_soutien=c.caisse_soutien, total=c.total, mode_paiement=rnd.choice(MODES),
                                        eleve_matricule=e.matricule, eleve_nom=e.nom, eleve_prenoms=e.prenoms, classe_nom=c.nom)
                eleves_par_classe.setdefault(cn, []).append(ins)
                nb += 1
        # Absences (sur les semaines déjà écoulées des trimestres commencés)
        today = date.today()
        alerte_ids = {eleves_par_classe['Seconde'][0].id, eleves_par_classe['Terminale S'][0].id}
        nb_appels = 0
        for t in an.trimestres.order_by('numero'):
            if t.date_debut > today:
                continue
            debut = max(t.date_debut, min(t.date_fin, today) - timedelta(weeks=8))
            fin = min(t.date_fin, today)
            for (cn, disc), m in matieres.items():
                cours = m.cours.first()
                d = debut
                while d <= fin:
                    if d.isoweekday() == cours.jour:
                        appel = Appel.objects.create(classe=m.classe, matiere=m, cours=cours, date=d, duree_heures=Decimal(str(cours.duree)), saisi_par=m.professeur.utilisateur)
                        lignes = []
                        for ins in eleves_par_classe[cn]:
                            r = rnd.random()
                            st, h, mo = 'PRESENT', Decimal(0), ''
                            if ins.id in alerte_ids:
                                st, h = 'ABSENT', appel.duree_heures
                            elif r < 0.06:
                                st, h = 'ABSENT', appel.duree_heures
                            elif r < 0.10:
                                st, h = 'RETARD', Decimal('0.50')
                            elif r < 0.15:
                                st, h, mo = 'JUSTIFIEE', appel.duree_heures, rnd.choice(['Maladie', 'Raison familiale', 'Rendez-vous médical'])
                            lignes.append(Absence(appel=appel, inscription=ins, statut=st, heures_absence=h, motif=mo))
                        Absence.objects.bulk_create(lignes)
                        nb_appels += 1
                    d += timedelta(days=1)
        # Notes sur 2 trimestres
        for t in list(an.trimestres.order_by('numero'))[:2]:
            for cn, inss in eleves_par_classe.items():
                for ins in inss:
                    niveau = rnd.gauss(11.5, 2.6)
                    for disc in COEF:
                        base = max(3, min(18, niveau + rnd.gauss(0, 2.2)))
                        ds = Decimal(str(round(max(0, min(20, base + rnd.gauss(0, 1.5))) * 4) / 4))
                        ex = Decimal(str(round(max(0, min(20, base + rnd.gauss(0, 1.8))) * 4) / 4))
                        Note.objects.create(inscription=ins, matiere=matieres[(cn, disc)], trimestre=t, ds=ds, examen=ex, saisi_par=profs[disc].utilisateur)
                recalculer(classes[cn], t)
        self.stdout.write(self.style.SUCCESS(f'Démo chargée : 6 professeurs, {nb} élèves, {nb_appels} appels, notes sur 2 trimestres ({an.libelle}).'))
        self.stdout.write('Professeurs : prof1@demo.ambohitromby.mg a prof6@demo.ambohitromby.mg / Prof12345')
