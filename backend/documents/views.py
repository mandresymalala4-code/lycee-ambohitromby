from datetime import date
from django.db.models import Avg, Count, Sum, Q
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from absences import services as asv
from absences.models import Absence, Appel
from absences.views import recap_rows, seances_du_jour, matiere_ok, parse_date, controle_date, trouver_appel, lignes_payload
from comptes.errors import Introuvable, Invalide, Refus
from comptes.models import Etablissement, Professeur, Utilisateur
from comptes.permissions import EstAdmin
from comptes.views import profs_qs, row_prof
from notes import services as nsv
from notes.models import Note, ResultatTrimestre
from scolarite import services as ssv
from scolarite.models import AnneeScolaire, Classe, Cours, Inscription, Matiere, Paiement, Trimestre
from scolarite.views import JOURS, cours_qs, get_or_404, ser_cours, ser_row_eleve
from . import pdf


def reponse_pdf(contenu, nom):
    r = HttpResponse(contenu, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nom}"'
    return r


def annee_de(request, defaut=True):
    a = request.query_params.get('annee')
    if a:
        return get_or_404(AnneeScolaire, a)
    return ssv.annee_courante()


# ---------- PDF ----------
class RecuPDF(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk):
        p = get_or_404(Paiement.objects.select_related('annee'), pk)
        return reponse_pdf(pdf.pdf_recu(p, Etablissement.get()), f'{p.numero_recu}.pdf')


class RecuInscriptionPDF(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk):
        i = get_or_404(Inscription.objects.select_related('paiement__annee'), pk)
        if not getattr(i, 'paiement', None):
            raise Introuvable()
        return reponse_pdf(pdf.pdf_recu(i.paiement, Etablissement.get()), f'{i.paiement.numero_recu}.pdf')


class ElevesPDF(APIView):
    def get(self, request):
        qp = request.query_params
        a = annee_de(request)
        params = {k: qp.get(k) for k in ('classe', 'sexe', 'q')}
        params['annee'] = a.id
        rows = [ser_row_eleve(i) for i in ssv.inscriptions_filtrees(params, 'alpha')]
        classe = Classe.objects.filter(pk=qp.get('classe')).first() if qp.get('classe') else None
        filtres = [f'Classe : {classe.nom}' if classe else 'Toutes les classes']
        if qp.get('sexe'):
            filtres.append(f'Sexe : {qp["sexe"]}')
        if qp.get('q'):
            filtres.append(f'Recherche : « {pdf.esc(qp["q"])} »')
        titre = f'Liste des élèves — {classe.nom}' if classe else 'Liste des élèves'
        return reponse_pdf(pdf.pdf_liste_eleves(rows, titre, ' · '.join(filtres), a.libelle, Etablissement.get()), 'liste-eleves.pdf')


class ProfesseursPDF(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        qp = request.query_params
        qs = profs_qs().filter(utilisateur__statut__in=['VALIDE', 'SUSPENDU'])
        filtres = ['Tous les professeurs']
        if qp.get('sexe'):
            qs = qs.filter(utilisateur__sexe=qp['sexe'])
            filtres.append(f'Sexe : {qp["sexe"]}')
        if qp.get('matiere'):
            qs = qs.filter(discipline_id=qp['matiere'])
            filtres.append(f'Matière : {qs.first().discipline.nom}' if qs.exists() else '')
        if qp.get('q'):
            q = qp['q']
            qs = qs.filter(Q(utilisateur__nom__icontains=q) | Q(utilisateur__prenom__icontains=q) | Q(code__icontains=q))
            filtres.append(f'Recherche : « {pdf.esc(q)} »')
        rows = [row_prof(p) for p in qs.order_by('utilisateur__nom', 'utilisateur__prenom')]
        return reponse_pdf(pdf.pdf_liste_profs(rows, ' · '.join(f for f in filtres if f), ssv.annee_courante().libelle, Etablissement.get()), 'liste-professeurs.pdf')


class EdtPDF(APIView):
    def get(self, request):
        classe = get_or_404(Classe.objects.select_related('annee'), request.query_params.get('classe'))
        cours = [ser_cours(c) for c in cours_qs().filter(matiere__classe=classe).order_by('jour', 'heure_debut')]
        return reponse_pdf(pdf.pdf_edt(cours, f'Emploi du temps — {classe.nom}', f'Classe : {classe.nom}', 'classe', classe.annee.libelle, Etablissement.get()), f'emploi-du-temps-{classe.nom}.pdf')


class MonEdtPDF(APIView):
    def get(self, request):
        if request.user.role != 'PROFESSEUR':
            raise Refus()
        a = annee_de(request)
        cours = [ser_cours(c) for c in cours_qs().filter(matiere__professeur__utilisateur=request.user, matiere__classe__annee=a).order_by('jour', 'heure_debut')]
        u = request.user
        return reponse_pdf(pdf.pdf_edt(cours, 'Emploi du temps personnel', f'Professeur : {u.nom} {u.prenom}', 'prof', a.libelle, Etablissement.get()), 'mon-emploi-du-temps.pdf')


class FeuilleAppelPDF(APIView):
    def get(self, request):
        qp = request.query_params
        classe, m = matiere_ok(request.user, qp.get('classe'), qp.get('matiere'))
        d = parse_date(qp.get('date'))
        controle_date(d, qp.get('jour'))
        cid = qp.get('cours') if qp.get('cours') not in (None, '', '0', 'null') else None
        appel = trouver_appel(m, d, cid)
        cours = Cours.objects.filter(pk=cid).first() if cid else None
        lignes = lignes_payload(classe, appel, d, m.id)
        ctx = {'classe': classe.nom, 'matiere': m.discipline.nom, 'professeur': f'{m.professeur.utilisateur.nom} {m.professeur.utilisateur.prenom}' if m.professeur else '',
               'jour': JOURS[d.isoweekday()], 'date': d.strftime('%d/%m/%Y'),
               'seance': f'{cours.heure_debut:%H:%M} - {cours.heure_fin:%H:%M}' if cours else (f'{float(appel.duree_heures):g} h' if appel else '—')}
        return reponse_pdf(pdf.pdf_feuille_appel(ctx, lignes, classe.annee.libelle, Etablissement.get()), 'feuille-appel.pdf')


class RapportAbsencesPDF(APIView):
    def get(self, request):
        classe = get_or_404(Classe.objects.select_related('annee'), request.query_params.get('classe'))
        titre, rows = recap_rows(request.user, classe, request.query_params)
        return reponse_pdf(pdf.pdf_rapport_absences(titre, classe.nom, rows, classe.annee.libelle, Etablissement.get()), 'rapport-absences.pdf')


class BulletinPDF(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk):
        ins = get_or_404(Inscription.objects.select_related('eleve', 'classe', 'annee'), pk)
        t = Trimestre.objects.filter(annee=ins.annee, numero=request.query_params.get('trimestre')).first()
        if not t:
            raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
        b = nsv.bulletin_data(ins, t)
        if request.query_params.get('decision') is not None:
            b['decision'] = request.query_params['decision'][:255]
        return reponse_pdf(pdf.pdf_bulletins([b], Etablissement.get()), f'bulletin-{ins.eleve.matricule}-T{t.numero}.pdf')


class BulletinClassePDF(APIView):
    permission_classes = [EstAdmin]

    def get(self, request, pk):
        classe = get_or_404(Classe.objects.select_related('annee'), pk)
        t = Trimestre.objects.filter(annee=classe.annee, numero=request.query_params.get('trimestre')).first()
        if not t:
            raise Invalide('Veuillez choisir le trimestre.', 'trimestre')
        ins = Inscription.objects.filter(classe=classe, statut='ACTIVE').select_related('eleve', 'classe', 'annee').order_by('eleve__nom', 'eleve__prenoms')
        if not ins:
            raise Invalide('Cette classe ne contient aucun élève.')
        return reponse_pdf(pdf.pdf_bulletins([nsv.bulletin_data(i, t) for i in ins], Etablissement.get()), f'bulletins-{classe.nom}-T{t.numero}.pdf')


# ---------- Statistiques ----------
def mensuel(qs_abs):
    out = {}
    for r in qs_abs.filter(statut__in=['ABSENT', 'JUSTIFIEE']).values('appel__date__year', 'appel__date__month', 'statut').annotate(h=Sum('heures_absence')):
        k = f'{r["appel__date__year"]}-{r["appel__date__month"]:02d}'
        o = out.setdefault(k, {'mois': k, 'justifiees': 0, 'injustifiees': 0})
        o['justifiees' if r['statut'] == 'JUSTIFIEE' else 'injustifiees'] += float(r['h'] or 0)
    return [out[k] for k in sorted(out)]


def dernier_trimestre_avec_notes(annee, matiere_ids=None):
    qs = ResultatTrimestre.objects.filter(trimestre__annee=annee)
    if matiere_ids is not None:
        qs = Note.objects.filter(trimestre__annee=annee, matiere_id__in=matiere_ids)
    n = qs.order_by('-trimestre__numero').values_list('trimestre__numero', flat=True).first()
    return n


class StatsAdmin(APIView):
    permission_classes = [EstAdmin]

    def get(self, request):
        a = annee_de(request)
        ssv.ensure_classes(a)
        ins = Inscription.objects.filter(annee=a, statut='ACTIVE')
        abs_qs = Absence.objects.filter(appel__classe__annee=a)
        fiches = abs_qs.count()
        pres = abs_qs.filter(statut__in=['PRESENT', 'RETARD']).count()
        heures_tot = abs_qs.filter(statut__in=['ABSENT', 'JUSTIFIEE']).aggregate(s=Sum('heures_absence'))['s'] or 0
        nmax = dernier_trimestre_avec_notes(a)
        moyenne = None
        par_classe = []
        if nmax:
            res = ResultatTrimestre.objects.filter(trimestre__annee=a, trimestre__numero=nmax)
            m = res.aggregate(m=Avg('moyenne'))['m']
            moyenne = float(nsv.r2(m)) if m is not None else None
            par_classe = [{'classe': r['inscription__classe__nom'], 'moyenne': float(nsv.r2(r['m']))}
                          for r in res.values('inscription__classe__nom').annotate(m=Avg('moyenne')).order_by('inscription__classe__nom')]
        eff = ssv.effectifs(a.id)
        classes = list(Classe.objects.filter(annee=a))
        sexes = {r['eleve__sexe']: r['n'] for r in ins.values('eleve__sexe').annotate(n=Count('id'))}
        attente = profs_qs().filter(utilisateur__statut='EN_ATTENTE')
        return Response({
            'annee': a.libelle, 'total_eleves': ins.count(), 'total_professeurs': Utilisateur.objects.filter(role='PROFESSEUR', statut='VALIDE').count(),
            'total_classes': len(classes), 'taux_presence': round(pres / fiches * 100, 1) if fiches else None, 'total_absences_heures': float(heures_tot),
            'moyenne_generale': moyenne, 'total_droits': Paiement.objects.filter(annee=a, statut='VALIDE').aggregate(s=Sum('total'))['s'] or 0,
            'trimestre_moyennes': nmax,
            'graph_sexe': [{'name': 'Garçons', 'value': sexes.get('Garçon', 0)}, {'name': 'Filles', 'value': sexes.get('Fille', 0)}],
            'graph_moyennes': par_classe, 'graph_absences': mensuel(abs_qs),
            'graph_effectifs': [{'classe': c.nom, 'effectif': eff.get(c.id, 0)} for c in classes],
            'en_attente': [{'id': p.id, 'nom': f'{p.utilisateur.nom} {p.utilisateur.prenom}', 'matiere': p.discipline.nom} for p in attente[:5]],
            'en_attente_total': attente.count(),
            'dernieres_inscriptions': [{'id': i.id, 'matricule': i.eleve.matricule, 'nom': f'{i.eleve.nom} {i.eleve.prenoms}', 'classe': i.classe.nom, 'date': i.date_inscription}
                                       for i in ins.select_related('eleve', 'classe').order_by('-id')[:5]],
            'alertes': asv.alertes(a)[:10],
        })


class StatsProfesseur(APIView):
    def get(self, request):
        if request.user.role != 'PROFESSEUR':
            raise Refus('Accès réservé au professeur.')
        a = annee_de(request)
        ssv.ensure_classes(a)
        mats = list(Matiere.objects.filter(professeur__utilisateur=request.user, classe__annee=a).select_related('classe', 'discipline'))
        mids = [m.id for m in mats]
        classes_ids = [m.classe_id for m in mats]
        eff = ssv.effectifs(a.id)
        cours = list(cours_qs().filter(matiere_id__in=mids))
        h = sum(c.duree for c in cours)
        today = date.today()
        du_jour = [dict(ser_cours(c), date=today.isoformat(), appel_fait=Appel.objects.filter(matiere=c.matiere, date=today, cours=c).exists())
                   for c in cours if c.jour == today.isoweekday()]
        t = ssv.trimestre_courant(a)
        attendues = sum(eff.get(m.classe_id, 0) for m in mats) * 2
        saisies = sum(1 for n in Note.objects.filter(matiere_id__in=mids, trimestre=t) for x in (n.ds, n.examen) if x is not None)
        moy_cl, moy_all = [], []
        nmax = dernier_trimestre_avec_notes(a, mids)
        if nmax:
            for m in mats:
                vals = [nsv.note_trimestrielle(n.ds, n.examen) for n in Note.objects.filter(matiere=m, trimestre__numero=nmax, trimestre__annee=a, ds__isnull=False, examen__isnull=False)]
                if vals:
                    moy_all += vals
                    moy_cl.append({'classe': m.classe.nom, 'moyenne': float(nsv.r2(sum(vals) / len(vals)))})
        return Response({
            'annee': a.libelle, 'matiere': mats[0].discipline.nom if mats else request.user.professeur.discipline.nom,
            'mes_classes': len(mats), 'mes_eleves': sum(eff.get(c, 0) for c in classes_ids), 'cours_aujourd_hui': len(du_jour),
            'heures_semaine': round(h, 2), 'notes_saisies_pct': round(saisies / attendues * 100) if attendues else 0,
            'moyenne_matiere': float(nsv.r2(sum(moy_all) / len(moy_all))) if moy_all else None, 'trimestre_courant': t.numero,
            'graph_moyennes': moy_cl, 'graph_absences': mensuel(Absence.objects.filter(appel__matiere_id__in=mids)),
            'cours_du_jour': du_jour, 'alertes': asv.alertes(a, mids)[:10],
        })


class Notifications(APIView):
    def get(self, request):
        a = ssv.annee_courante()
        out = []
        if request.user.role == 'ADMIN':
            n = Utilisateur.objects.filter(role='PROFESSEUR', statut='EN_ATTENTE').count()
            if n:
                out.append({'type': 'prof_attente', 'niveau': 'warning', 'message': f'{n} compte(s) professeur en attente de validation.', 'lien': '/professeurs?onglet=attente'})
            for al in asv.alertes(a)[:20]:
                out.append({'type': 'alerte_absences', 'niveau': 'danger', 'message': f'{al["nom"]} {al["prenoms"]} ({al["classe"]}) : {al["heures"]:g} h d\'absences injustifiées (T{al["trimestre"]}).', 'lien': '/absences'})
        else:
            mats = list(Matiere.objects.filter(professeur__utilisateur=request.user, classe__annee=a))
            mids = [m.id for m in mats]
            today = date.today()
            if today.isoweekday() <= 5:
                for c in cours_qs().filter(matiere_id__in=mids, jour=today.isoweekday()):
                    if not Appel.objects.filter(matiere=c.matiere, date=today, cours=c).exists():
                        out.append({'type': 'appel', 'niveau': 'warning', 'message': f'Appel non fait : {c.matiere.classe.nom} à {c.heure_debut:%H:%M}.', 'lien': '/absences'})
            t = ssv.trimestre_courant(a)
            attendues = sum(ssv.classe_effectif(m.classe) for m in mats) * 2
            saisies = sum(1 for n in Note.objects.filter(matiere_id__in=mids, trimestre=t) for x in (n.ds, n.examen) if x is not None)
            if attendues and saisies < attendues:
                out.append({'type': 'notes', 'niveau': 'info', 'message': f'{attendues - saisies} note(s) manquante(s) pour le {t.numero}{"er" if t.numero == 1 else "ème"} trimestre.', 'lien': '/notes'})
            for al in asv.alertes(a, mids)[:10]:
                out.append({'type': 'alerte_absences', 'niveau': 'danger', 'message': f'{al["nom"]} {al["prenoms"]} ({al["classe"]}) : plus de 15 h d\'absences injustifiées.', 'lien': '/absences'})
        return Response(out)
