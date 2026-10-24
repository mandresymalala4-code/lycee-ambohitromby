from datetime import date, time
from decimal import Decimal
from django.test import override_settings
from comptes.models import Utilisateur
from notes.models import Note
from notes.services import recalculer, note_trimestrielle, appreciation
from scolarite.models import Cours, Inscription, Matiere, Trimestre
from comptes.models import Discipline as _D
from absences.models import Absence, Appel
from .base import Base, prof_payload, eleve_payload


class AuthTests(Base):
    def test_T01_connexion_admin_et_prof(self):
        self.assertEqual(self.as_admin()['role'], 'ADMIN')
        self.client.credentials()
        self.assertEqual(self.as_prof()['role'], 'PROFESSEUR')

    def test_T02_mauvais_mot_de_passe(self):
        r = self.client.post('/api/auth/login/', {'email': 'admin@test.mg', 'password': 'faux12345'}, format='json')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['message'], 'Email ou mot de passe incorrect.')

    def test_verrouillage_apres_5_echecs(self):
        for _ in range(5):
            r = self.client.post('/api/auth/login/', {'email': 'admin@test.mg', 'password': 'faux12345'}, format='json')
        self.assertEqual(r.status_code, 429)
        r = self.client.post('/api/auth/login/', {'email': 'admin@test.mg', 'password': 'Admin12345'}, format='json')
        self.assertEqual(r.status_code, 429)

    def test_T03_T04_T05_compte_prof_en_attente_puis_valide(self):
        r = self.client.post('/api/auth/register-professeur/', prof_payload(), format='multipart')
        self.assertEqual(r.status_code, 201, r.content)
        r = self.client.post('/api/auth/login/', {'email': 'jean@test.mg', 'password': 'Secret123'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('attente de validation', r.json()['message'])
        self.as_admin()
        att = self.client.get('/api/professeurs/en-attente/').json()
        self.assertEqual(len(att), 1)
        r = self.client.post(f'/api/professeurs/{att[0]["id"]}/valider/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['code'].startswith('PRF-'))
        self.client.credentials()
        self.assertEqual(self.login('jean@test.mg', 'Secret123')['role'], 'PROFESSEUR')

    def test_T06_unicite_email_tel_cin(self):
        self.client.post('/api/auth/register-professeur/', prof_payload(), format='multipart')
        for champ, chg in (('email', {'telephone': '0349999999', 'cin': '99999999999999'}), ('telephone', {'email': 'x@test.mg', 'cin': '99999999999999'}),
                           ('cin', {'email': 'y@test.mg', 'telephone': '0349999998'})):
            r = self.client.post('/api/auth/register-professeur/', prof_payload(**chg), format='multipart')
            self.assertEqual(r.status_code, 409, r.content)
            self.assertIn(champ, r.json()['champs'])

    def test_T07_T08_validations(self):
        for chg, champ in (({'telephone': '0412345678'}, 'telephone'), ({'telephone': '034123456'}, 'telephone'), ({'mot_de_passe': 'abcdefgh', 'confirmation': 'abcdefgh'}, 'mot_de_passe'),
                           ({'confirmation': 'Autre1234'}, 'confirmation'), ({'nom': 'rakoto'}, 'nom'), ({'prenom': 'JEAN'}, 'prenom'),
                           ({'date_naissance': '2015-01-01'}, 'date_naissance'), ({'cin': '12345'}, 'cin'), ({'cin': '101234567890'}, 'cin'), ({'cin': '101234567890123'}, 'cin'), ({'cin': '1012345678901a'}, 'cin')):
            r = self.client.post('/api/auth/register-professeur/', prof_payload(**chg), format='multipart')
            self.assertEqual(r.status_code, 400, (chg, r.content))
            self.assertIn(champ, r.json()['champs'])

    def test_mot_de_passe_oublie(self):
        r = self.client.post('/api/auth/mot-de-passe-oublie/', {'email': 'prof@test.mg', 'telephone': '0340000002', 'mot_de_passe': 'Nouveau123', 'confirmation': 'Nouveau123'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.login('prof@test.mg', 'Nouveau123')['role'], 'PROFESSEUR')
        r = self.client.post('/api/auth/mot-de-passe-oublie/', {'email': 'prof@test.mg', 'telephone': '0349999999', 'mot_de_passe': 'Nouveau123', 'confirmation': 'Nouveau123'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_T27_prof_refuse_sur_routes_admin(self):
        self.as_prof()
        self.assertEqual(self.client.post('/api/inscriptions/', {}, format='json').status_code, 403)
        self.assertEqual(self.client.put('/api/parametres/', {'nom': 'X'}, format='json').status_code, 403)
        self.assertEqual(self.client.post('/api/classes/', {'nom': 'X', 'droit_inscription': 1, 'caisse_soutien': 0, 'annee': self.annee.id}, format='json').status_code, 403)
        self.assertEqual(self.client.get(f'/api/bulletins/1/?trimestre=1').status_code, 403)
        self.assertEqual(self.client.get('/api/resultats/?classe=1&trimestre=1').status_code, 403)

    def test_prof_ne_voit_pas_les_montants(self):
        self.as_prof()
        c = self.client.get(f'/api/classes/?annee={self.annee.id}').json()[0]
        self.assertNotIn('droit_inscription', c)
        self.assertNotIn('total', c)


class InscriptionTests(Base):
    def setUp(self):
        super().setUp()
        self.as_admin()

    def test_T10_inscription_complete(self):
        r = self.inscrire()
        self.assertEqual(r.status_code, 201, r.content)
        d = r.json()
        self.assertRegex(d['matricule'], r'^\d{4}-0001$')
        self.assertEqual(d['paiement']['total'], 50000)
        self.assertTrue(d['paiement']['numero_recu'].startswith('REC-'))
        pdf = self.client.get(f'/api/inscriptions/{d["id"]}/recu/')
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_T11_doublon_inscription(self):
        r = self.inscrire()
        eid = r.json()['eleve_id']
        r2 = self.inscrire(eleve_id=eid)
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(r2.json()['message'], 'Cet élève est déjà inscrit pour cette année scolaire.')
        self.assertEqual(self.inscrire().status_code, 409)

    def test_T12_deux_freres_meme_famille(self):
        self.inscrire()
        r = self.inscrire(nom='RABE', prenoms='Tiana')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['code'], 'FAMILLE_EXISTE')
        r = self.inscrire(nom='RABE', prenoms='Tiana', rattacher_famille=True)
        self.assertEqual(r.status_code, 201, r.content)
        from scolarite.models import Famille, Eleve
        self.assertEqual(Famille.objects.count(), 1)
        self.assertEqual(Eleve.objects.count(), 2)

    def test_inscription_transactionnelle(self):
        n = Inscription.objects.count()
        r = self.inscrire(mode_paiement='Bitcoin')
        self.assertEqual(r.status_code, 400)
        p = eleve_payload(self.seconde, self.annee)
        p['famille']['contact_parent'] = '0412345678'
        self.assertEqual(self.client.post('/api/inscriptions/', p, format='json').status_code, 400)
        self.assertEqual(Inscription.objects.count(), n)
        from scolarite.models import Eleve, Paiement
        self.assertEqual((Eleve.objects.count(), Paiement.objects.count()), (0, 0))

    def test_T09_dates_naissance(self):
        for d in ('1997-12-31', '2014-01-01'):
            p = eleve_payload(self.seconde, self.annee)
            p['eleve']['date_naissance'] = d
            r = self.client.post('/api/inscriptions/', p, format='json')
            self.assertEqual(r.status_code, 400, d)
        p = eleve_payload(self.seconde, self.annee)
        p['eleve']['nom'] = 'rabe'
        self.assertEqual(self.client.post('/api/inscriptions/', p, format='json').status_code, 400)

    def test_T14_suppression_classe_non_vide(self):
        self.inscrire()
        r = self.client.delete(f'/api/classes/{self.seconde.id}/')
        self.assertEqual(r.status_code, 409)
        self.assertIn('Elle ne peut pas être supprimée', r.json()['message'])

    def test_T13_filtre_par_annee(self):
        self.inscrire()
        autre = self.client.get('/api/annees/').json()
        a2 = next(a for a in autre if a['annee_debut'] == self.annee.annee_debut - 1)
        self.assertEqual(self.client.get(f'/api/eleves/?annee={a2["id"]}').json(), [])
        self.assertEqual(len(self.client.get(f'/api/eleves/?annee={self.annee.id}').json()), 1)

    def test_suppression_inscription_annule_recu(self):
        i = self.inscrire().json()
        r = self.client.delete(f'/api/eleves/{i["id"]}/')
        self.assertEqual(r.status_code, 204)
        from scolarite.models import Paiement, Eleve
        self.assertEqual(Paiement.objects.get().statut, 'ANNULE')
        self.assertEqual(Eleve.objects.count(), 0)

    def test_T15_matiere_coefficients(self):
        for coef in (0, 7, 2.5, 'abc'):
            r = self.client.post('/api/matieres/', {'classe': self.seconde.id, 'nom': 'Latin', 'coefficient': coef}, format='json')
            self.assertEqual(r.status_code, 400, coef)
        r = self.client.post('/api/matieres/', {'classe': self.seconde.id, 'nom': 'L', 'coefficient': 2}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/matieres/', {'classe': self.seconde.id, 'nom': 'Anglais', 'coefficient': 2}, format='json')
        self.assertEqual(r.status_code, 409)

    def test_T16_emploi_du_temps(self):
        base = {'matiere': self.m_ang.id, 'jour': 1, 'heure_debut': '08:00', 'heure_fin': '10:00'}
        self.assertEqual(self.client.post('/api/emplois-du-temps/', base, format='json').status_code, 201)
        for chg in ({'heure_debut': '06:30'}, {'heure_fin': '18:30'}, {'heure_fin': '07:30', 'heure_debut': '08:00'}, {'heure_debut': '08:15'}, {'jour': 6}):
            r = self.client.post('/api/emplois-du-temps/', {**base, **chg}, format='json')
            self.assertEqual(r.status_code, 400, chg)
        r = self.client.post('/api/emplois-du-temps/', {**base, 'matiere': self.m_mat.id, 'heure_debut': '09:00', 'heure_fin': '11:00'}, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['message'], 'Un cours est déjà prévu à ce créneau pour cette classe.')
        # conflit professeur dans une autre classe
        autre = self.annee.classes.get(nom='1ère S')
        m2 = Matiere.objects.create(classe=autre, discipline=self.anglais, coefficient=2, professeur=self.prof)
        r = self.client.post('/api/emplois-du-temps/', {'matiere': m2.id, 'jour': 1, 'heure_debut': '09:00', 'heure_fin': '10:00'}, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertIn('Ce professeur a déjà un cours', r.json()['message'])


class NotesTests(Base):
    def setUp(self):
        super().setUp()
        self.as_admin()
        self.ins = [Inscription.objects.get(pk=self.inscrire(nom=f'ELEVE{c}'.replace('1', 'A').replace('2', 'B').replace('3', 'C').replace('4', 'D'), prenoms='Test', contact=f'034050{i:04d}').json()['id']) for i, c in enumerate(range(1, 5))]
        self.t1 = Trimestre.objects.get(annee=self.annee, numero=1)

    def saisir(self, matiere, rows, tri=1):
        return self.client.post('/api/notes/', {'classe': self.seconde.id, 'trimestre': tri, 'matiere': matiere.id,
                                                'notes': [{'inscription_id': i.id, 'ds': a, 'examen': b} for i, (a, b) in zip(self.ins, rows)]}, format='json')

    def test_T20_notes_invalides(self):
        for bad in (20.5, -1, 'abc', '12.345'):
            r = self.saisir(self.m_mat, [(bad, 10), (10, 10), (10, 10), (10, 10)])
            self.assertEqual(r.status_code, 400, bad)
        self.assertEqual(Note.objects.count(), 0)

    def test_T21_T22_calculs(self):
        self.assertEqual(note_trimestrielle(Decimal(12), Decimal(14)), Decimal('13.00'))
        r = self.saisir(self.m_mat, [(12, 14), (0, 0), (None, None), (20, 20)])
        self.assertEqual(r.status_code, 200, r.content)
        l = r.json()['lignes'][0]
        self.assertEqual(l['note'], 13.0)
        # exemple §8.2 : Maths coef 4 (12,14) ; Français coef 3 (10,11) ; Anglais coef 2 (15,16)
        fr = Matiere.objects.create(classe=self.seconde, discipline=_D.objects.create(nom='Français'), coefficient=3)
        i0 = self.ins[0]
        Note.objects.create(inscription=i0, matiere=fr, trimestre=self.t1, ds=10, examen=11)
        Note.objects.create(inscription=i0, matiere=self.m_ang, trimestre=self.t1, ds=15, examen=16)
        recalculer(self.seconde, self.t1)
        from notes.models import ResultatTrimestre
        r0 = ResultatTrimestre.objects.get(inscription=i0, trimestre=self.t1)
        self.assertEqual((r0.total_coefficients, r0.total_points, r0.moyenne), (9, Decimal('114.50'), Decimal('12.72')))

    def test_T23_classement_ex_aequo(self):
        self.saisir(self.m_mat, [(18, 18), (14, 14), (14, 14), (8, 8)])
        d = self.client.get(f'/api/resultats/?classe={self.seconde.id}&trimestre=1').json()
        self.assertEqual([l['rang'] for l in d['lignes']], [1, 2, 2, 4])

    def test_T24_correction_recalcule_rangs(self):
        self.saisir(self.m_mat, [(18, 18), (14, 14), (10, 10), (8, 8)])
        self.saisir(self.m_mat, [(5, 5), (14, 14), (10, 10), (8, 8)])
        d = self.client.get(f'/api/resultats/?classe={self.seconde.id}&trimestre=1').json()
        par = {l['inscription_id']: l['rang'] for l in d['lignes']}
        self.assertEqual(par[self.ins[0].id], 4)
        self.assertEqual(par[self.ins[1].id], 1)

    def test_appreciation(self):
        self.assertEqual(appreciation(Decimal('4.99')), 'Très insuffisant')
        self.assertEqual(appreciation(Decimal('12')), 'Assez bien')
        self.assertEqual(appreciation(Decimal('18')), 'Excellent')

    def test_T18_prof_matiere_autre_403(self):
        self.as_prof()
        self.assertEqual(self.saisir(self.m_mat, [(10, 10)] * 4).status_code, 403)
        self.assertEqual(self.client.get(f'/api/notes/?classe={self.seconde.id}&trimestre=1&matiere={self.m_mat.id}').status_code, 403)
        self.assertEqual(self.saisir(self.m_ang, [(10, 10)] * 4).status_code, 200)

    def test_T25_trimestre_cloture(self):
        self.saisir(self.m_ang, [(10, 10)] * 4)
        self.client.post(f'/api/trimestres/{self.t1.id}/cloture/', {'cloture': True}, format='json')
        self.as_prof()
        r = self.saisir(self.m_ang, [(12, 12)] * 4)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['message'], 'Trimestre clôturé : contactez l\'administrateur.')
        self.as_admin()
        self.assertEqual(self.saisir(self.m_ang, [(12, 12)] * 4).status_code, 200)
        from comptes.models import JournalAudit
        self.assertTrue(JournalAudit.objects.filter(action='CORRECTION_NOTE_APRES_CLOTURE').exists())

    def test_T26_bulletin_pdf(self):
        self.saisir(self.m_mat, [(12, 14), (10, 10), (10, 10), (10, 10)])
        r = self.client.get(f'/api/bulletins/{self.ins[0].id}/?trimestre=1').json()
        self.assertTrue(r['provisoire'] or r['matieres_sans_note'] == 0)
        self.assertEqual(r['rang'], 1)
        p = self.client.get(f'/api/bulletins/{self.ins[0].id}/pdf/?trimestre=1')
        self.assertEqual(p.status_code, 200)
        self.assertTrue(p.content.startswith(b'%PDF'))
        c = self.client.get(f'/api/bulletins/classe/{self.seconde.id}/pdf/?trimestre=1')
        self.assertTrue(c.content.startswith(b'%PDF'))


class AbsenceTests(Base):
    def setUp(self):
        super().setUp()
        self.as_admin()
        self.ins = [Inscription.objects.get(pk=self.inscrire(nom='ELEVEA', prenoms='Test', contact='0340600001').json()['id']),
                    Inscription.objects.get(pk=self.inscrire(nom='ELEVEB', prenoms='Test', contact='0340600002').json()['id'])]
        Trimestre.objects.filter(annee=self.annee).update(date_debut=date(self.annee.annee_debut, 1, 1), date_fin=date(self.annee.annee_fin, 8, 31))
        self.t = Trimestre.objects.get(annee=self.annee, numero=1)
        Trimestre.objects.filter(annee=self.annee, numero__in=(2, 3)).update(date_debut=date(2090, 1, 1), date_fin=date(2090, 1, 2))
        Trimestre.objects.filter(pk=self.t.pk).update(date_fin=date(2089, 12, 31))
        self.d = self.jour_passe(1)
        self.cours = Cours.objects.create(matiere=self.m_ang, jour=1, heure_debut=time(8, 0), heure_fin=time(10, 0))

    def appel(self, rows, d=None, jour=None, cours=True, **extra):
        d = d or self.d
        p = {'classe': self.seconde.id, 'matiere': self.m_ang.id, 'date': d.isoformat(), 'jour': jour or d.isoweekday(),
             'cours': self.cours.id if cours else None,
             'lignes': [{'inscription_id': i.id, **r} for i, r in zip(self.ins, rows)]}
        p.update(extra)
        return self.client.post('/api/appels/', p, format='json')

    def test_T17_dates_invalides(self):
        from datetime import timedelta
        r = self.appel([{'statut': 'PRESENT'}] * 2, jour=2)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['message'], 'La date ne correspond pas au jour choisi.')
        futur = date.today() + timedelta(days=7)
        while futur.isoweekday() > 5:
            futur += timedelta(days=1)
        r = self.appel([{'statut': 'PRESENT'}] * 2, d=futur, jour=futur.isoweekday())
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['message'], 'La date ne peut pas être dans le futur.')

    def test_appel_et_heures_par_defaut(self):
        r = self.appel([{'statut': 'ABSENT'}, {'statut': 'RETARD', 'heures_absence': 0.5}])
        self.assertEqual(r.status_code, 201, r.content)
        l = r.json()['lignes']
        self.assertEqual((l[0]['heures_absence'], l[1]['heures_absence']), (2.0, 0.5))
        self.assertEqual(self.appel([{'statut': 'PRESENT'}] * 2).status_code, 409)

    def test_validations_appel(self):
        self.assertEqual(self.appel([{'statut': 'JUSTIFIEE'}, {'statut': 'PRESENT'}]).status_code, 400)
        self.assertEqual(self.appel([{'statut': 'ABSENT', 'heures_absence': 3}, {'statut': 'PRESENT'}]).status_code, 400)
        self.assertEqual(self.appel([{'statut': 'ABSENT', 'heures_absence': 1.1}, {'statut': 'PRESENT'}]).status_code, 400)
        self.assertEqual(self.appel([{'statut': 'XXX'}, {'statut': 'PRESENT'}]).status_code, 400)
        self.assertEqual(Appel.objects.count(), 0)

    def test_T19_alerte_16h(self):
        from datetime import timedelta
        d = self.d
        for k in range(8):
            r = self.appel([{'statut': 'ABSENT'}, {'statut': 'PRESENT'}], d=d - timedelta(weeks=k))
            self.assertEqual(r.status_code, 201, r.content)
        al = self.client.get(f'/api/absences/alertes/?annee={self.annee.id}').json()
        self.assertEqual(len(al), 1)
        self.assertEqual(al[0]['heures'], 16.0)
        rec = self.client.get(f'/api/absences/recapitulatif/?classe={self.seconde.id}&periode=trimestre&trimestre=1').json()
        self.assertTrue(rec['lignes'][0]['alerte'])
        self.assertFalse(rec['lignes'][1]['alerte'])
        n = self.client.get('/api/notifications/').json()
        self.assertTrue(any(x['type'] == 'alerte_absences' for x in n))
        self.assertTrue(self.client.get(f'/api/absences/rapport/pdf/?classe={self.seconde.id}&periode=trimestre&trimestre=1').content.startswith(b'%PDF'))

    def test_seuil_strict_15h(self):
        from datetime import timedelta
        for k in range(7):
            self.appel([{'statut': 'ABSENT', 'heures_absence': 2}, {'statut': 'PRESENT'}], d=self.d - timedelta(weeks=k))
        self.appel([{'statut': 'ABSENT', 'heures_absence': 1}, {'statut': 'PRESENT'}], d=self.d - timedelta(weeks=7))
        self.assertEqual(self.client.get(f'/api/absences/alertes/?annee={self.annee.id}').json(), [])   # 15 h pile : pas d'alerte

    def test_T18_prof_appel_matiere(self):
        self.as_prof()
        base = {'classe': self.seconde.id, 'date': self.d.isoformat(), 'jour': 1, 'lignes': [{'inscription_id': self.ins[0].id, 'statut': 'PRESENT'}]}
        r = self.client.post('/api/appels/', {**base, 'matiere': self.m_mat.id}, format='json')
        self.assertEqual(r.status_code, 403)
        r = self.client.post('/api/appels/', {**base, 'matiere': self.m_ang.id, 'cours': self.cours.id}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.as_prof('autre@test.mg')
        r = self.client.put(f'/api/appels/{r.json()["appel"]["id"]}/', base, format='json')
        self.assertEqual(r.status_code, 403)

    def test_prof_sans_cours_ce_jour(self):
        self.as_prof()
        d = self.jour_passe(3)
        r = self.client.post('/api/appels/', {'classe': self.seconde.id, 'matiere': self.m_ang.id, 'date': d.isoformat(), 'jour': 3,
                                              'lignes': [{'inscription_id': self.ins[0].id, 'statut': 'PRESENT'}]}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['message'], 'Aucun cours de votre matière n\'est prévu ce jour pour cette classe.')


class PdfEtStatsTests(Base):
    def test_pdfs_et_stats(self):
        self.as_admin()
        self.inscrire()
        Cours.objects.create(matiere=self.m_ang, jour=2, heure_debut=time(8, 0), heure_fin=time(10, 0), salle='A1')
        for url in (f'/api/eleves/pdf/?annee={self.annee.id}', '/api/professeurs/pdf/', f'/api/emplois-du-temps/pdf/?classe={self.seconde.id}'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertTrue(r.content.startswith(b'%PDF'), url)
        s = self.client.get(f'/api/statistiques/admin/?annee={self.annee.id}').json()
        self.assertEqual((s['total_eleves'], s['total_professeurs'], s['total_classes']), (1, 2, 7))
        self.assertEqual(s['total_droits'], 50000)
        self.as_prof()
        self.assertTrue(self.client.get('/api/mon-emploi-du-temps/pdf/').content.startswith(b'%PDF'))
        s = self.client.get(f'/api/statistiques/professeur/?annee={self.annee.id}').json()
        self.assertEqual(s['mes_classes'], 1)
        self.assertEqual(self.client.get('/api/statistiques/admin/').status_code, 403)

    def test_erreurs_json_jamais_500(self):
        self.as_admin()
        r = self.client.get('/api/eleves/99999/')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(set(r.json()), {'status', 'code', 'message', 'champs'})
        self.client.credentials()
        r = self.client.get('/api/classes/')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['message'], 'Votre session a expiré. Veuillez vous reconnecter.')

    def test_parametres_et_logo(self):
        self.as_admin()
        r = self.client.put('/api/parametres/', {'nom': 'Lycée Test', 'adresse': 'Rue 1', 'telephone': '0202222222', 'email': ''}, format='multipart')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['etablissement']['nom'], 'Lycée Test')
        self.assertEqual(self.client.put('/api/parametres/', {'nom': 'L', 'adresse': 'Rue 1', 'telephone': '1'}, format='multipart').status_code, 400)

    def test_suppression_prof_et_regles(self):
        self.as_admin()
        r = self.client.put(f'/api/professeurs/{self.prof.id}/', prof_payload(email='prof@test.mg', telephone='0340000002', cin='11111111111111', matiere='Physique'), format='multipart')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.client.delete(f'/api/professeurs/{self.prof.id}/').status_code, 204)
        self.m_ang.refresh_from_db()
        self.assertIsNone(self.m_ang.professeur)


class SecuriteSessionTests(Base):
    def test_cin_14_chiffres_message(self):
        r = self.client.post('/api/auth/register-professeur/', prof_payload(cin='101234567890'), format='multipart')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['champs']['cin'], 'Le CIN doit contenir exactement 14 chiffres.')
        r = self.client.post('/api/auth/register-professeur/', prof_payload(cin='1012 3456 7890 12'), format='multipart')
        self.assertEqual(r.status_code, 201, r.content)

    def test_entetes_no_store(self):
        for r in (self.client.post('/api/auth/login/', {'email': 'x@x.mg', 'password': 'zzzzzzzz1'}, format='json'), self.client.get('/api/classes/')):
            cc = r['Cache-Control']
            for t in ('no-store', 'no-cache', 'must-revalidate'):
                self.assertIn(t, cc)
            self.assertEqual(r['Pragma'], 'no-cache')
        self.as_admin()
        self.assertIn('no-store', self.client.get(f'/api/eleves/pdf/?annee={self.annee.id}')['Cache-Control'])

    def test_deconnexion_invalide_le_refresh(self):
        d = self.as_admin()
        r = self.client.post('/api/auth/refresh/', {'refresh': d['refresh']}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout/', {'refresh': d['refresh']}, format='json').status_code, 204)
        r = self.client.post('/api/auth/refresh/', {'refresh': d['refresh']}, format='json')
        self.assertEqual(r.status_code, 401)

    def test_jeton_invalide_ou_absent_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer abc.def.ghi')
        r = self.client.get('/api/classes/')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['message'], 'Votre session a expiré. Veuillez vous reconnecter.')


    def test_url_inconnue_json(self):
        from django.test import override_settings
        self.as_admin()
        with override_settings(DEBUG=False):
            r = self.client.get('/api/n-existe-pas/')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(set(r.json()), {'status', 'code', 'message', 'champs'})
