from datetime import date, timedelta
from rest_framework.test import APITestCase
from comptes.models import Professeur, Utilisateur, Discipline
from comptes.services import prochain_code_prof
from scolarite import services as sv
from scolarite.models import Classe, Cours, Matiere


def prof_payload(**k):
    d = dict(nom='RAKOTO', prenom='Jean', date_naissance='1985-05-10', sexe='Homme', adresse='Lot 12 Ambohitromby', telephone='0341234567',
             email='jean@test.mg', cin='10123456789012', matiere='Anglais', mot_de_passe='Secret123', confirmation='Secret123')
    d.update(k)
    return d


def eleve_payload(classe, annee, **k):
    d = {'annee': annee.id, 'classe': classe.id, 'mode_paiement': 'Espèces',
         'eleve': {'nom': 'RABE', 'prenoms': 'Hery', 'date_naissance': '2010-04-12', 'sexe': 'Garçon', 'adresse': 'Lot 5 Itaosy'},
         'famille': {'pere_nom': 'RABE', 'pere_prenoms': 'Paul', 'contact_parent': '0340500267', 'adresse_parents': 'Lot 5 Itaosy'}}
    d.update(k)
    return d


class Base(APITestCase):
    def setUp(self):
        sv.ensure_toutes_annees()
        self.annee = sv.annee_courante()
        sv.ensure_classes(self.annee)
        self.seconde = Classe.objects.get(annee=self.annee, nom='Seconde')
        self.admin = Utilisateur.objects.create_user('admin@test.mg', 'Admin12345', role='ADMIN', nom='ADMIN', prenom='Test', sexe='Homme',
                                                      adresse='Adresse', telephone='0340000001', date_naissance=date(1980, 1, 1), statut='VALIDE')
        self.anglais = Discipline.objects.create(nom='Anglais')
        self.maths = Discipline.objects.create(nom='Mathématiques')
        self.prof = self.mk_prof('prof@test.mg', '0340000002', '11111111111111', self.anglais)
        self.autre = self.mk_prof('autre@test.mg', '0340000003', '22222222222222', self.maths)
        self.m_ang = Matiere.objects.create(classe=self.seconde, discipline=self.anglais, coefficient=2, professeur=self.prof)
        self.m_mat = Matiere.objects.create(classe=self.seconde, discipline=self.maths, coefficient=4, professeur=self.autre)

    def mk_prof(self, email, tel, cin, disc):
        u = Utilisateur.objects.create_user(email, 'Prof12345', role='PROFESSEUR', nom='PROF', prenom='Test', sexe='Homme', adresse='Adresse',
                                            telephone=tel, date_naissance=date(1985, 1, 1), statut='VALIDE')
        return Professeur.objects.create(utilisateur=u, cin=cin, discipline=disc, code=prochain_code_prof())

    def login(self, email, pw):
        r = self.client.post('/api/auth/login/', {'email': email, 'password': pw}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + r.json()['access'])
        return r.json()

    def as_admin(self):
        return self.login('admin@test.mg', 'Admin12345')

    def as_prof(self, email='prof@test.mg'):
        return self.login(email, 'Prof12345')

    def inscrire(self, nom='RABE', prenoms='Hery', contact='0340500267', classe=None, **extra):
        p = eleve_payload(classe or self.seconde, self.annee)
        p['eleve'].update(nom=nom, prenoms=prenoms)
        p['famille'].update(contact_parent=contact)
        p.update(extra)
        return self.client.post('/api/inscriptions/', p, format='json')

    def jour_passe(self, iso=1):
        d = date.today() - timedelta(days=1)
        while d.isoweekday() != iso:
            d -= timedelta(days=1)
        return d
