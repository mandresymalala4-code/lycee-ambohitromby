"""Génération des PDF (ReportLab, A4) — logo, établissement, année scolaire, date, pagination (§9)."""
import io
import os
from datetime import datetime
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

BLEU, BLEU_FONCE, BLEU_CLAIR = colors.HexColor('#1E3A8A'), colors.HexColor('#0F172A'), colors.HexColor('#3B82F6')
GRIS, ROUGE, VERT = colors.HexColor('#F1F5F9'), colors.HexColor('#DC2626'), colors.HexColor('#16A34A')
PALETTE = ['#DBEAFE', '#DCFCE7', '#FEF3C7', '#FCE7F3', '#E0E7FF', '#CCFBF1', '#FEE2E2', '#EDE9FE', '#FFEDD5', '#E2E8F0']
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']

S = {
    'n': ParagraphStyle('n', fontName='Helvetica', fontSize=9, leading=11.5),
    'p': ParagraphStyle('p', fontName='Helvetica', fontSize=8, leading=10),
    'pb': ParagraphStyle('pb', fontName='Helvetica-Bold', fontSize=8, leading=10),
    'pc': ParagraphStyle('pc', fontName='Helvetica', fontSize=8, leading=10, alignment=1),
    'h1': ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=BLEU, alignment=1, spaceAfter=4),
    'h2': ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=BLEU_FONCE, spaceBefore=6, spaceAfter=3),
    'sub': ParagraphStyle('sub', fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=6),
}


def P(t, s='n'):
    return Paragraph(str(t if t is not None else ''), S[s] if isinstance(s, str) else s)


def esc(t):
    return str(t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def fmt_ar(n):
    return f'{int(n):,}'.replace(',', ' ') + ' Ar'


def fmt_date(d):
    return d.strftime('%d/%m/%Y') if d else ''


def fmt_tel(t):
    t = str(t or '')
    return f'{t[:3]} {t[3:5]} {t[5:8]} {t[8:]}' if len(t) == 10 else t


def n2(x):
    return '—' if x is None else f'{x:.2f}'.replace('.', ',')


def heures(x):
    x = float(x or 0)
    return (f'{x:.2f}'.rstrip('0').rstrip('.') or '0').replace('.', ',') + ' h'


# --- nombre en lettres (français) ---
U = ['zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze',
     'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf']
D = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante']


def _cent(n):
    if n < 20:
        return U[n]
    if n < 70:
        d, u = divmod(n, 10)
        return D[d] + ('-et-un' if u == 1 else ('-' + U[u] if u else ''))
    if n < 80:
        return 'soixante-' + ('et-onze' if n == 71 else U[n - 60])
    if n == 80:
        return 'quatre-vingts'
    return 'quatre-vingt-' + U[n - 80]


def _mille(n):
    c, r = divmod(n, 100)
    if c == 0:
        return _cent(r)
    p = 'cent' if c == 1 else U[c] + ' cent' + ('s' if r == 0 else '')
    return p + (' ' + _cent(r) if r else '')


def en_lettres(n):
    n = int(n)
    if n == 0:
        return 'zéro'
    out = []
    mi, r = divmod(n, 1_000_000)
    m, r = divmod(r, 1000)
    if mi:
        out.append(_mille(mi) + (' million' + ('s' if mi > 1 else '')))
    if m:
        out.append('mille' if m == 1 else _mille(m).replace('quatre-vingts', 'quatre-vingt') + ' mille')
    if r:
        out.append(_mille(r))
    return ' '.join(out)


def dessiner_logo(c, x, y, taille, logo_path=None):
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, x, y, taille, taille, preserveAspectRatio=True, mask='auto')
            return
        except Exception:
            pass
    c.saveState()
    c.setFillColor(BLEU)
    c.circle(x + taille / 2, y + taille / 2, taille / 2, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', taille * 0.36)
    c.drawCentredString(x + taille / 2, y + taille * 0.34, 'LA')
    c.setStrokeColor(BLEU_CLAIR)
    c.setLineWidth(1.4)
    c.arc(x + taille * 0.14, y + taille * 0.14, x + taille * 0.86, y + taille * 0.86, 200, 140)
    c.restoreState()


def construire(contenu, etab, annee_libelle, paysage=False, titre='Document'):
    buf = io.BytesIO()
    size = landscape(A4) if paysage else A4
    W, H = size
    logo = etab.logo.path if etab.logo else None
    maintenant = timezone.localtime().strftime('%d/%m/%Y à %H:%M')

    def decor(c, doc):
        c.saveState()
        dessiner_logo(c, 1.5 * cm, H - 2.7 * cm, 1.7 * cm, logo)
        c.setFillColor(BLEU)
        c.setFont('Helvetica-Bold', 13)
        c.drawString(3.5 * cm, H - 1.6 * cm, (etab.nom or 'LYCÉE AMBOHITROMBY').upper())
        c.setFillColor(colors.HexColor('#475569'))
        c.setFont('Helvetica', 7.8)
        c.drawString(3.5 * cm, H - 2.1 * cm, f'{etab.adresse} · Tél. {fmt_tel(etab.telephone)}' + (f' · {etab.email}' if etab.email else ''))
        c.setFillColor(BLEU_FONCE)
        c.setFont('Helvetica-Bold', 9)
        c.drawRightString(W - 1.5 * cm, H - 1.6 * cm, f'Année scolaire : {annee_libelle}')
        c.setStrokeColor(BLEU)
        c.setLineWidth(1.2)
        c.line(1.5 * cm, H - 2.9 * cm, W - 1.5 * cm, H - 2.9 * cm)
        c.setStrokeColor(colors.HexColor('#CBD5E1'))
        c.setLineWidth(0.5)
        c.line(1.5 * cm, 1.3 * cm, W - 1.5 * cm, 1.3 * cm)
        c.setFillColor(colors.HexColor('#64748B'))
        c.setFont('Helvetica', 7.5)
        c.drawString(1.5 * cm, 0.8 * cm, f'Édité le {maintenant}')
        c.drawRightString(W - 1.5 * cm, 0.8 * cm, f'Page {doc.page}')
        c.restoreState()

    doc = BaseDocTemplate(buf, pagesize=size, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=3.3 * cm, bottomMargin=1.7 * cm, title=titre, author=etab.nom)
    doc.addPageTemplates([PageTemplate(id='p', frames=[Frame(1.5 * cm, 1.7 * cm, W - 3 * cm, H - 5.0 * cm, id='f', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=decor)])
    doc.build(contenu)
    return buf.getvalue()


def tableau(data, widths, entete=True, align_center=(), extra=None, repeat=1):
    t = Table(data, colWidths=widths, repeatRows=repeat if entete else 0)
    st = [('FONT', (0, 0), (-1, -1), 'Helvetica', 8), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    if entete:
        st += [('BACKGROUND', (0, 0), (-1, 0), BLEU), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8)]
        st += [('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS])]
    for c in align_center:
        st.append(('ALIGN', (c, 0), (c, -1), 'CENTER'))
    t.setStyle(TableStyle(st + (extra or [])))
    return t


# ---------------- Reçu ----------------
def pdf_recu(p, etab):
    ann = p.annee.libelle
    st = []
    st.append(P('REÇU D\'INSCRIPTION', 'h1'))
    if p.statut == 'ANNULE':
        st.append(P('<font color="#DC2626"><b>*** ANNULÉ ***</b></font>', ParagraphStyle('a', parent=S['sub'], fontSize=13, leading=16)))
    st.append(P(f'N° <b>{p.numero_recu}</b> — {timezone.localtime(p.date_paiement).strftime("%d/%m/%Y à %H:%M")}', 'sub'))
    info = [[P('Matricule', 'pb'), P(esc(p.eleve_matricule)), P('Année scolaire', 'pb'), P(ann)],
            [P('Nom', 'pb'), P(esc(p.eleve_nom)), P('Classe', 'pb'), P(esc(p.classe_nom))],
            [P('Prénoms', 'pb'), P(esc(p.eleve_prenoms)), P('Mode de paiement', 'pb'), P(esc(p.mode_paiement))]]
    t = tableau(info, [3 * cm, 5.5 * cm, 3.5 * cm, 5.5 * cm], entete=False,
                extra=[('BACKGROUND', (0, 0), (0, -1), GRIS), ('BACKGROUND', (2, 0), (2, -1), GRIS)])
    st += [t, Spacer(1, 0.5 * cm), P('Détail du paiement', 'h2')]
    det = [['Désignation', 'Montant'], ['Droit d\'inscription', fmt_ar(p.droit_inscription)], ['Caisse de soutien', fmt_ar(p.caisse_soutien)],
           ['MONTANT TOTAL PAYÉ', fmt_ar(p.total)]]
    st.append(tableau(det, [12 * cm, 5.5 * cm], extra=[('ALIGN', (1, 0), (1, -1), 'RIGHT'), ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 9),
                                                         ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE'))]))
    st.append(Spacer(1, 0.3 * cm))
    st.append(P(f'Arrêté le présent reçu à la somme de <b>{esc(en_lettres(p.total))} ariary</b>.'))
    st.append(Spacer(1, 1.2 * cm))
    sig = Table([[P('Signature du parent / tuteur', 'pc'), P('Signature et cachet de l\'établissement', 'pc')]], colWidths=[8.75 * cm, 8.75 * cm], rowHeights=[3 * cm])
    sig.setStyle(TableStyle([('VALIGN', (0, 0), (-1, 0), 'TOP'), ('BOX', (0, 0), (0, 0), 0.4, colors.HexColor('#CBD5E1')), ('BOX', (1, 0), (1, 0), 0.4, colors.HexColor('#CBD5E1'))]))
    st.append(sig)
    return construire(st, etab, ann, titre=f'Reçu {p.numero_recu}')


# ---------------- Bulletins ----------------
def _bulletin_story(b, etab, decision=None):
    ord_t = '1er' if b['trimestre'] == 1 else f'{b["trimestre"]}ème'
    st = [P('BULLETIN SCOLAIRE', 'h1'), P(f'{ord_t} trimestre — Année scolaire : {b["annee"]}', 'sub')]
    if b['provisoire']:
        st.append(P('<font color="#F59E0B"><b>PROVISOIRE</b></font> — Bulletin incomplet : ' + f'{b["matieres_sans_note"]} matière(s) sans note', ParagraphStyle('pv', parent=S['sub'])))
    info = [[P('Matricule', 'pb'), P(b['matricule']), P('Classe', 'pb'), P(esc(b['classe']))],
            [P('Nom', 'pb'), P(esc(b['nom'])), P('Effectif de la classe', 'pb'), P(b['effectif_classe'])],
            [P('Prénoms', 'pb'), P(esc(b['prenoms'])), P('Trimestre', 'pb'), P(ord_t)]]
    st.append(tableau(info, [3 * cm, 6 * cm, 4 * cm, 4.5 * cm], entete=False, extra=[('BACKGROUND', (0, 0), (0, -1), GRIS), ('BACKGROUND', (2, 0), (2, -1), GRIS)]))
    st.append(Spacer(1, 0.4 * cm))
    rows = [['Matière', 'Coef.', 'DS', 'Examen', 'Moyenne', 'Points', 'Appréciation']]
    for l in b['lignes']:
        rows.append([P(esc(l['matiere'])), l['coefficient'], n2(l['ds']), n2(l['examen']), n2(l['note']), n2(l['points']), P(l['appreciation'] or '—')])
    rows.append([P('<b>TOTAL</b>'), b['total_coefficients'], '', '', '', n2(b['total_points']), ''])
    st.append(tableau(rows, [5 * cm, 1.4 * cm, 1.8 * cm, 1.9 * cm, 2.2 * cm, 2.2 * cm, 3 * cm], align_center=(1, 2, 3, 4, 5),
                      extra=[('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 8), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE'))]))
    st.append(Spacer(1, 0.4 * cm))
    rang = '—' if not b['rang'] else f'{b["rang"]}{"er" if b["rang"] == 1 else "e"} / {b["effectif_classe_classe"]}'
    res = [[P('Total des coefficients', 'pb'), P(b['total_coefficients']), P('Moyenne générale', 'pb'), P(f'<b>{n2(b["moyenne"])} / 20</b>')],
           [P('Total des points', 'pb'), P(n2(b['total_points'])), P('Rang', 'pb'), P(f'<b>{rang}</b>')],
           [P('Absences justifiées', 'pb'), P(heures(b['absences_justifiees'])), P('Absences injustifiées', 'pb'), P(heures(b['absences_injustifiees']))],
           [P('Appréciation générale', 'pb'), P(b['appreciation'] or '—'), P('Retards', 'pb'), P(b['retards'])]]
    st.append(tableau(res, [4.2 * cm, 4.3 * cm, 4.2 * cm, 4.8 * cm], entete=False, extra=[('BACKGROUND', (0, 0), (0, -1), GRIS), ('BACKGROUND', (2, 0), (2, -1), GRIS)]))
    st.append(Spacer(1, 0.4 * cm))
    txt = esc(decision if decision is not None else b['decision']) or '<br/><br/><br/>'
    dec = Table([[P('<b>Décision du conseil des professeurs</b>', 'p')], [P(txt, 'n')]], colWidths=[17.5 * cm], rowHeights=[0.7 * cm, 2.2 * cm])
    dec.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.5, BLEU), ('BACKGROUND', (0, 0), (-1, 0), GRIS), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    st.append(dec)
    st.append(Spacer(1, 0.5 * cm))
    st.append(P(f'Fait à {esc(etab.adresse.split(",")[0])}, le {timezone.localdate().strftime("%d/%m/%Y")}'))
    sig = Table([[P('Le Parent / Tuteur', 'pc'), P('Le Professeur principal', 'pc'), P('Le Chef d\'établissement', 'pc')]], colWidths=[5.8 * cm] * 3, rowHeights=[2.2 * cm])
    sig.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    st.append(sig)
    return st


def pdf_bulletins(liste, etab):
    st = []
    for i, b in enumerate(liste):
        if i:
            st.append(PageBreak())
        st += _bulletin_story(b, etab)
    return construire(st, etab, liste[0]['annee'] if liste else '', titre='Bulletins')


# ---------------- Listes ----------------
def pdf_liste_eleves(rows, titre, filtres, annee, etab):
    st = [P(titre.upper(), 'h1'), P(f'{filtres} — Effectif : {len(rows)} — Tri alphabétique', 'sub')]
    data = [['N°', 'Matricule', 'Nom', 'Prénoms', 'Naissance', 'Sexe', 'Classe', 'Adresse']]
    for n, r in enumerate(rows, 1):
        data.append([n, r['matricule'], P(esc(r['nom'])), P(esc(r['prenoms'])), fmt_date(r['date_naissance']), r['sexe'], P(esc(r['classe_nom'])), P(esc(r['adresse']))])
    st.append(tableau(data, [0.9 * cm, 2.1 * cm, 3.1 * cm, 3.1 * cm, 2 * cm, 1.4 * cm, 2.2 * cm, 3.7 * cm], align_center=(0, 4, 5)))
    return construire(st, etab, annee, titre=titre)


def pdf_liste_profs(rows, filtres, annee, etab):
    st = [P('LISTE DES PROFESSEURS', 'h1'), P(f'{filtres} — Effectif : {len(rows)}', 'sub')]
    data = [['N°', 'Code', 'Nom', 'Prénoms', 'Matière', 'Téléphone', 'Email']]
    for n, r in enumerate(rows, 1):
        data.append([n, r['code'] or '', P(esc(r['nom'])), P(esc(r['prenoms'])), P(esc(r['matiere_nom'])), fmt_tel(r['telephone']), P(esc(r['email']))])
    st.append(tableau(data, [0.9 * cm, 1.9 * cm, 3.2 * cm, 3.2 * cm, 3 * cm, 2.6 * cm, 3.7 * cm], align_center=(0,)))
    return construire(st, etab, annee, titre='Liste des professeurs')


# ---------------- Emploi du temps ----------------
def pdf_edt(cours, titre, sous_titre, mode, annee, etab):
    """cours: liste de dict (ser_cours). mode: 'classe' (affiche professeur) ou 'prof' (affiche classe)."""
    slots = [(7 * 60 + 30 * i) for i in range(22)]  # 07:00 → 17:30
    data = [['Heure'] + JOURS] + [[(f'{s // 60:02d}:00' if s % 60 == 0 else '')] + [''] * 5 for s in slots]
    couleurs, extra = {}, []
    for c in cours:
        h1, m1 = map(int, c['heure_debut'].split(':'))
        h2, m2 = map(int, c['heure_fin'].split(':'))
        r1, r2 = (h1 * 60 + m1 - 420) // 30 + 1, (h2 * 60 + m2 - 420) // 30
        col = c['jour']
        coul = couleurs.setdefault(c['matiere_nom'], PALETTE[len(couleurs) % len(PALETTE)])
        second = c['professeur_nom'] if mode == 'classe' else c['classe_nom']
        lignes = [f'<b>{esc(c["matiere_nom"])}</b>', esc(second), f'{c["heure_debut"]} - {c["heure_fin"]}' + (f' · {esc(c["salle"])}' if c['salle'] else '')]
        data[r1][col] = P('<br/>'.join(lignes), ParagraphStyle('c', parent=S['p'], fontSize=6.8, leading=8, alignment=1))
        extra.append(('BACKGROUND', (col, r1), (col, r2), colors.HexColor(coul)))
        if r2 > r1:
            extra.append(('SPAN', (col, r1), (col, r2)))
    t = Table(data, colWidths=[1.6 * cm] + [4.9 * cm] * 5, rowHeights=[0.55 * cm] + [0.56 * cm] * 22)
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#CBD5E1')), ('BACKGROUND', (0, 0), (-1, 0), BLEU),
                           ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                           ('FONT', (0, 1), (0, -1), 'Helvetica', 6.5), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)] + extra))
    st = [P(titre.upper(), ParagraphStyle('t', parent=S['h1'], fontSize=13, leading=15, spaceAfter=0)), P(sous_titre, ParagraphStyle('s', parent=S['sub'], spaceAfter=3)), t]
    return construire(st, etab, annee, paysage=True, titre=titre)


# ---------------- Feuille d'appel & rapports ----------------
LIB_STATUT = {'PRESENT': 'Présent', 'ABSENT': 'Absent', 'RETARD': 'Retard', 'JUSTIFIEE': 'Absence justifiée'}


def pdf_feuille_appel(ctx, lignes, annee, etab):
    st = [P('FEUILLE D\'APPEL', 'h1')]
    info = [[P('Classe', 'pb'), P(esc(ctx['classe'])), P('Matière', 'pb'), P(esc(ctx['matiere']))],
            [P('Professeur', 'pb'), P(esc(ctx['professeur'] or '—')), P('Jour', 'pb'), P(ctx['jour'])],
            [P('Date', 'pb'), P(ctx['date']), P('Séance', 'pb'), P(ctx['seance'])]]
    st.append(tableau(info, [3 * cm, 6 * cm, 3 * cm, 5.5 * cm], entete=False, extra=[('BACKGROUND', (0, 0), (0, -1), GRIS), ('BACKGROUND', (2, 0), (2, -1), GRIS)]))
    st.append(Spacer(1, 0.4 * cm))
    data = [['N°', 'Matricule', 'Nom', 'Prénoms', 'Statut', 'Heures', 'Motif', 'Observation']]
    for n, l in enumerate(lignes, 1):
        data.append([n, l['matricule'], P(esc(l['nom'])), P(esc(l['prenoms'])), LIB_STATUT.get(l['statut'], ''), heures(l['heures_absence']) if l['statut'] != 'PRESENT' else '—', P(esc(l['motif'])), P(esc(l['observation']))])
    st.append(tableau(data, [0.8 * cm, 2 * cm, 3 * cm, 3 * cm, 2.4 * cm, 1.3 * cm, 2.5 * cm, 2.5 * cm], align_center=(0, 4, 5),
                      extra=[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FEE2E2')) for i, l in enumerate(lignes, 1) if l['statut'] == 'ABSENT']))
    return construire(st, etab, annee, titre='Feuille d\'appel')


def pdf_rapport_absences(titre, classe, rows, annee, etab):
    st = [P('RAPPORT D\'ABSENCES', 'h1'), P(f'Classe : {esc(classe)} — {esc(titre)}', 'sub')]
    data = [['N°', 'Matricule', 'Nom', 'Prénoms', 'Justifiées', 'Injustifiées', 'Retards', 'Total', 'Alerte']]
    extra = []
    for n, r in enumerate(rows, 1):
        data.append([n, r['matricule'], P(esc(r['nom'])), P(esc(r['prenoms'])), heures(r['justifiees']), heures(r['injustifiees']), r['retards'], heures(r['total']), 'ALERTE > 15 h' if r['alerte'] else ''])
        if r['alerte']:
            extra += [('BACKGROUND', (0, n), (-1, n), colors.HexColor('#FEE2E2')), ('TEXTCOLOR', (0, n), (-1, n), ROUGE)]
    tot = lambda k: sum(r[k] for r in rows)
    data.append(['', '', P('<b>TOTAL CLASSE</b>'), '', heures(tot('justifiees')), heures(tot('injustifiees')), tot('retards'), heures(tot('total')), f'{sum(1 for r in rows if r["alerte"])} alerte(s)'])
    extra += [('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 8), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE'))]
    st.append(tableau(data, [0.8 * cm, 2 * cm, 3 * cm, 3 * cm, 1.8 * cm, 2 * cm, 1.4 * cm, 1.5 * cm, 2.3 * cm], align_center=(0, 4, 5, 6, 7), extra=extra))
    return construire(st, etab, annee, titre='Rapport d\'absences')
