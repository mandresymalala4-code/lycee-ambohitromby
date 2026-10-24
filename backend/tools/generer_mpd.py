"""Génère le MPD (Modèle Physique des Données) en PDF à partir des modèles Django réels.

Usage (depuis backend/, venv activé) :  python tools/generer_mpd.py
Sortie : ../frontend/public/documentation/mpd.pdf  et  ../documentation/MPD_Lycee_Ambohitromby.pdf
Nécessite : pip install pypdf   (outil de développement, non requis pour faire tourner l'application)
"""
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django  # noqa: E402

django.setup()
from django.apps import apps  # noqa: E402
from django.db import connection, models  # noqa: E402
from django.db.models import F, Q  # noqa: E402
from pypdf import PdfWriter, PdfReader  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A3, A4, landscape  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak  # noqa: E402

APPS = ['comptes', 'scolarite', 'absences', 'notes']
COUL = {'comptes': '#1E3A8A', 'scolarite': '#15803D', 'absences': '#B45309', 'notes': '#6D28D9'}
DESC = {
    'utilisateur': "Comptes de connexion (administrateurs et professeurs), état du compte, thème, verrouillage.",
    'discipline': "Référentiel des matières enseignables (Mathématiques, Français…).",
    'professeur': "Données propres au professeur : code PRF-NNNN, CIN (14 chiffres), matière enseignée.",
    'etablissement': "Paramètres de l'établissement (nom, adresse, contacts, logo) — ligne unique.",
    'journal_audit': "Historique des actions sensibles (connexions, clôtures, corrections).",
    'donnee_demo': "Repères des lignes créées par la commande charger_demo (pour effacer_demo).",
    'annee_scolaire': "Années scolaires 2020-2021 à 2045-2046 ; une seule est « courante ».",
    'trimestre': "Trois trimestres par année, avec dates et état de clôture.",
    'classe': "Classes d'une année scolaire, avec droit d'inscription et caisse de soutien.",
    'famille': "Parents / tuteur ; le contact parent est unique (frères et sœurs partagent la famille).",
    'eleve': "Identité permanente de l'élève ; matricule AAAA-NNNN unique.",
    'inscription': "Inscription d'un élève dans une classe pour une année (unique par élève et année).",
    'paiement': "Reçu d'inscription (REC-AAAA-NNNNN) conservé même si l'inscription est supprimée (statut ANNULE).",
    'matiere': "Matière d'une classe : coefficient (1 à 6) et professeur affecté.",
    'cours': "Créneau hebdomadaire de l'emploi du temps (lundi–vendredi, 07:00–18:00).",
    'appel': "Séance d'appel (classe, matière, date, durée) ; unique par matière, date et séance.",
    'absence': "Ligne d'appel par élève : présent, absent, retard ou absence justifiée, heures et motif.",
    'note': "Notes DS et Examen (0 à 20) par élève, matière et trimestre.",
    'resultat_trimestre': "Total des points, moyenne et rang (ex æquo gérés) par élève et trimestre.",
    'decision_conseil': "Décision du conseil des professeurs portée sur le bulletin.",
}
# Positions du diagramme (x, y haut) sur A3 paysage
POS = {
    'utilisateur': (30, 790), 'journal_audit': (30, 520), 'etablissement': (30, 340), 'donnee_demo': (30, 190),
    'professeur': (255, 790), 'discipline': (255, 560), 'matiere': (255, 400),
    'cours': (480, 790), 'appel': (480, 600), 'absence': (480, 360),
    'annee_scolaire': (705, 790), 'trimestre': (705, 640), 'classe': (705, 470), 'resultat_trimestre': (705, 250),
    'famille': (930, 790), 'eleve': (930, 650), 'inscription': (930, 480), 'paiement': (930, 290), 'note': (930, 150), 'decision_conseil': (705, 110),
}
BW, RH, HH = 180, 12.5, 19


def modeles():
    out = []
    for a in APPS:
        for m in apps.get_app_config(a).get_models():
            out.append((a, m))
    return out


def tipo(f):
    t = (f.db_type(connection) or '').replace(' AUTO_INCREMENT', '')
    return t.replace('integer', 'int')


def q_txt(q):
    if isinstance(q, Q):
        parts = [q_txt(c) for c in q.children]
        s = f' {q.connector} '.join(parts)
        return f'NOT ({s})' if q.negated else (f'({s})' if len(parts) > 1 else s)
    k, v = q
    f, _, op = k.partition('__')
    ops = {'gte': '>=', 'lte': '<=', 'gt': '>', 'lt': '<', 'isnull': 'IS NULL' if v else 'IS NOT NULL'}
    if op == 'isnull':
        return f'{f} {ops[op]}'
    if isinstance(v, F):
        v = v.name
    elif isinstance(v, datetime.time):
        v = v.strftime('%H:%M')
    return f'{f} {ops.get(op, "=")} {v}'


def info(m):
    t = m._meta.db_table
    cols, pk = [], m._meta.pk.column
    for f in m._meta.concrete_fields:
        flags = []
        if f.primary_key:
            flags.append('PK')
        if f.remote_field:
            flags.append('FK')
        if f.unique and not f.primary_key:
            flags.append('UQ')
        ref = ''
        if f.remote_field:
            od = f.remote_field.on_delete.__name__.replace('DO_NOTHING', 'NO ACTION').replace('PROTECT', 'RESTRICT').replace('SET_NULL', 'SET NULL')
            ref = f"→ {f.remote_field.model._meta.db_table}.{f.remote_field.model._meta.pk.column}  (ON DELETE {od})"
        cols.append({'nom': f.column, 'type': tipo(f), 'null': 'OUI' if f.null else 'NON', 'flags': flags, 'ref': ref,
                     'defaut': '' if f.default is models.NOT_PROVIDED or callable(f.default) else str(f.default)})
    uq = [c for c in m._meta.constraints if isinstance(c, models.UniqueConstraint)]
    ck = [c for c in m._meta.constraints if isinstance(c, models.CheckConstraint)]
    idx = list(m._meta.indexes)
    ut = [list(u) for u in m._meta.unique_together]
    return {'table': t, 'cols': cols, 'uq': uq, 'ck': ck, 'idx': idx, 'ut': ut, 'm': m}


def fks(infos):
    res = []
    for i in infos:
        for f in i['m']._meta.concrete_fields:
            if f.remote_field:
                res.append((i['table'], f.remote_field.model._meta.db_table, f.column, isinstance(f, models.OneToOneField)))
    return res


# ---------------- diagramme (A3 paysage) ----------------
def diagramme(infos, app_de):
    buf = io.BytesIO()
    W, H = landscape(A3)
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setFillColor(colors.HexColor('#0F172A')); c.setFont('Helvetica-Bold', 20)
    c.drawString(30, H - 34, 'MPD — Diagramme relationnel · Lycée Ambohitromby')
    c.setFont('Helvetica', 9.5); c.setFillColor(colors.HexColor('#475569'))
    c.drawString(30, H - 50, 'Seules les colonnes clés sont représentées (PK, FK, UQ). Le détail complet figure dans le dictionnaire de données (pages suivantes).')
    # légende
    lx = W - 330
    for k, a in enumerate(APPS):
        c.setFillColor(colors.HexColor(COUL[a])); c.roundRect(lx + k * 80, H - 52, 12, 12, 3, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#0F172A')); c.setFont('Helvetica', 9); c.drawString(lx + k * 80 + 16, H - 49, a)
    box = {}
    for i in infos:
        t = i['table']
        cles = [x for x in i['cols'] if x['flags']]
        autres = len(i['cols']) - len(cles)
        h = HH + RH * (len(cles) + (1 if autres else 0)) + 6
        x, y = POS[t]
        box[t] = (x, y - h, BW, h)
    # liens
    def centre(b): return (b[0] + b[2] / 2, b[1] + b[3] / 2)
    def bord(b, px, py):
        cx, cy = centre(b); dx, dy = px - cx, py - cy
        if dx == 0 and dy == 0: return cx, cy
        sx = (b[2] / 2) / abs(dx) if dx else 1e9; sy = (b[3] / 2) / abs(dy) if dy else 1e9
        s = min(sx, sy); return cx + dx * s, cy + dy * s
    TRACE = {'saisi_par_id', 'enregistre_par_id', 'valide_par_id', 'utilisateur_id_audit'}
    for (enfant, parent, col, un_un) in fks(infos):
        if enfant == parent:
            b = box[enfant]; c.setStrokeColor(colors.HexColor('#94A3B8')); c.setLineWidth(1.1); c.setDash(3, 2)
            c.line(b[0], b[1] + b[3] - 12, b[0] - 14, b[1] + b[3] - 12); c.line(b[0] - 14, b[1] + b[3] - 12, b[0] - 14, b[1] + b[3] - 30); c.line(b[0] - 14, b[1] + b[3] - 30, b[0], b[1] + b[3] - 30); c.setDash()
            continue
        bc, bp = box[enfant], box[parent]
        x1, y1 = bord(bc, *centre(bp)); x2, y2 = bord(bp, *centre(bc))
        trace = parent == 'utilisateur' and enfant != 'professeur'
        c.setStrokeColor(colors.HexColor('#CBD5E1' if trace else '#64748B')); c.setLineWidth(.9 if trace else 1.1)
        if trace: c.setDash(4, 3)
        c.line(x1, y1, x2, y2); c.setDash()
        c.setFillColor(colors.HexColor('#1E3A8A')); c.setFont('Helvetica-Bold', 8)
        def lab(x, y, tx, ox, oy):
            c.setFillColor(colors.white); c.circle(x + ox, y + oy, 6, fill=1, stroke=0)
            c.setFillColor(colors.HexColor('#1E3A8A')); c.drawCentredString(x + ox, y + oy - 3, tx)
        ux = (x2 - x1); uy = (y2 - y1); n = (ux ** 2 + uy ** 2) ** .5 or 1
        lab(x1, y1, '1' if un_un else 'N', ux / n * 12, uy / n * 12)
        lab(x2, y2, '1', -ux / n * 12, -uy / n * 12)
    # tables
    for i in infos:
        t = i['table']; x, y, w, h = box[t]; col = colors.HexColor(COUL[app_de[t]])
        c.setFillColor(colors.Color(0, 0, 0, alpha=.07)); c.roundRect(x + 2.5, y - 2.5, w, h, 6, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setStrokeColor(col); c.setLineWidth(1.3); c.roundRect(x, y, w, h, 6, fill=1, stroke=1)
        c.setFillColor(col); c.roundRect(x, y + h - HH, w, HH, 6, fill=1, stroke=0); c.rect(x, y + h - HH, w, HH / 2, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 10); c.drawString(x + 8, y + h - 13.5, t)
        cles = [z for z in i['cols'] if z['flags']]; yy = y + h - HH - RH + 2
        for z in cles:
            c.setFillColor(colors.HexColor('#0F172A')); c.setFont('Helvetica-Bold' if 'PK' in z['flags'] else 'Helvetica', 8)
            c.drawString(x + 8, yy, z['nom']); c.setFont('Helvetica', 6.8); c.setFillColor(colors.HexColor('#64748B'))
            c.drawRightString(x + w - 8, yy, ' '.join(z['flags']) + ' · ' + z['type'][:14])
            yy -= RH
        rest = len(i['cols']) - len(cles)
        if rest:
            c.setFont('Helvetica-Oblique', 7.5); c.setFillColor(colors.HexColor('#64748B')); c.drawString(x + 8, yy, f'+ {rest} autre(s) colonne(s)')
    c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#64748B'))
    c.drawString(30, 18, 'Notation : 1 = côté parent (clé référencée) · N = côté enfant (clé étrangère) · pointillés = liens de traçabilité vers utilisateur (saisi_par, enregistre_par, valide_par) · SGBD cible : MariaDB / MySQL (InnoDB, utf8mb4)')
    c.showPage(); c.save()
    return buf.getvalue()


# ---------------- couverture + dictionnaire (A4) ----------------
def en_tete(c, doc):
    W, H = A4
    c.saveState(); c.setFont('Helvetica-Bold', 9); c.setFillColor(colors.HexColor('#1E3A8A'))
    if doc.page > 1:
        c.drawString(1.8 * cm, H - 1.3 * cm, 'MPD · Lycée Ambohitromby'); c.setStrokeColor(colors.HexColor('#1E3A8A')); c.setLineWidth(.8)
        c.line(1.8 * cm, H - 1.5 * cm, W - 1.8 * cm, H - 1.5 * cm)
    c.setFont('Helvetica', 8); c.setFillColor(colors.HexColor('#64748B'))
    c.drawRightString(W - 1.8 * cm, 1.0 * cm, f'Page {doc.page + 2}'); c.drawString(1.8 * cm, 1.0 * cm, f'Généré le {datetime.date.today():%d/%m/%Y}')
    c.restoreState()


def couverture():
    buf = io.BytesIO(); W, H = A4; c = canvas.Canvas(buf, pagesize=A4)
    c.setFillColor(colors.HexColor('#0F172A')); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#1E3A8A')); c.circle(W * .85, H * .9, 190, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#3B82F6')); c.circle(W * .1, H * .12, 120, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 34); c.drawString(2.2 * cm, H * .56, 'Modèle Physique')
    c.drawString(2.2 * cm, H * .56 - 42, 'des Données (MPD)')
    c.setFont('Helvetica', 15); c.setFillColor(colors.HexColor('#BFDBFE')); c.drawString(2.2 * cm, H * .56 - 82, 'Gestion d’étude dans un lycée — LYCÉE AMBOHITROMBY')
    c.setFont('Helvetica', 11); c.setFillColor(colors.white)
    for k, tx in enumerate(['SGBD : MariaDB / MySQL (XAMPP) · moteur InnoDB · jeu de caractères utf8mb4', 'Base : lycee_ambohitromby',
                             f'Document généré automatiquement depuis les modèles de l’application · {datetime.date.today():%d/%m/%Y}']):
        c.drawString(2.2 * cm, H * .56 - 120 - k * 18, tx)
    c.showPage(); c.save(); return buf.getvalue()


def dictionnaire(infos, app_de):
    buf = io.BytesIO(); W, H = A4
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=2.0 * cm, bottomMargin=1.6 * cm, title='MPD Lycée Ambohitromby')
    doc.addPageTemplates([PageTemplate(id='p', frames=[Frame(1.8 * cm, 1.6 * cm, W - 3.6 * cm, H - 3.6 * cm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=en_tete)])
    h1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=17, textColor=colors.HexColor('#1E3A8A'), spaceAfter=8)
    h2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=11.5, textColor=colors.white, leading=14)
    n = ParagraphStyle('n', fontName='Helvetica', fontSize=8.6, leading=11)
    s = ParagraphStyle('s', fontName='Helvetica', fontSize=7.6, leading=9.5)
    sb = ParagraphStyle('sb', fontName='Helvetica-Bold', fontSize=7.6, leading=9.5)
    esc = lambda x: str(x).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    st = [Paragraph('1. Présentation', h1),
          Paragraph("Ce document décrit la structure physique de la base de données <b>lycee_ambohitromby</b> : tables, colonnes, types, clés primaires (PK), clés étrangères (FK), contraintes d’unicité (UQ), contraintes de validité (CHECK) et index. "
                    "Il est généré à partir des modèles réels de l’application ; il est donc toujours conforme au schéma créé par les migrations.", n), Spacer(1, 6),
          Paragraph(f"<b>{len(infos)}</b> tables métier réparties en 4 modules : comptes, scolarite, absences, notes. "
                    "Les tables techniques de Django (auth_*, django_*, token_blacklist_*) ne sont pas détaillées.", n), Spacer(1, 10)]
    t = [[Paragraph('<b>Table</b>', s), Paragraph('<b>Module</b>', s), Paragraph('<b>Rôle</b>', s)]] + [[Paragraph(i['table'], s), Paragraph(app_de[i['table']], s), Paragraph(esc(DESC[i['table']]), s)] for i in infos]
    tb = Table(t, colWidths=[3.6 * cm, 2.2 * cm, 11.6 * cm], repeatRows=1)
    tb.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')), ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#CBD5E1')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    st += [tb, PageBreak(), Paragraph('2. Dictionnaire de données', h1)]
    for i in infos:
        col = colors.HexColor(COUL[app_de[i['table']]])
        head = Table([[Paragraph(f"{i['table']}  <font size=8 color='#DBEAFE'>· module {app_de[i['table']]}</font>", h2)]], colWidths=[W - 3.6 * cm])
        head.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), col), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
        rows = [[Paragraph(f'<b>{x}</b>', s) for x in ('Colonne', 'Type', 'Null', 'Clés', 'Défaut', 'Référence')]]
        for z in i['cols']:
            rows.append([Paragraph(f"<b>{z['nom']}</b>" if 'PK' in z['flags'] else z['nom'], s), Paragraph(esc(z['type']), s), z['null'], Paragraph(' '.join(z['flags']), sb), Paragraph(esc(z['defaut']), s), Paragraph(esc(z['ref']), s)])
        tab = Table(rows, colWidths=[3.1 * cm, 2.9 * cm, 1.0 * cm, 1.3 * cm, 2.2 * cm, 6.9 * cm], repeatRows=1)
        tab.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 7.6), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')), ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#CBD5E1')),
                                 ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('ALIGN', (2, 0), (2, -1), 'CENTER')]))
        extra = [Paragraph(f"<i>{esc(DESC[i['table']])}</i>", s), Spacer(1, 3)]
        lignes = []
        for u in i['uq']:
            lignes.append(f"<b>UNIQUE</b> {u.name} ({', '.join(u.fields)})")
        for u in i['ut']:
            lignes.append(f"<b>UNIQUE</b> ({', '.join(u)})")
        for c_ in i['ck']:
            lignes.append(f"<b>CHECK</b> {c_.name} : {esc(q_txt(c_.condition))}")
        for x in i['idx']:
            lignes.append(f"<b>INDEX</b> ({', '.join(x.fields)})")
        for z in i['cols']:
            if 'UQ' in z['flags']:
                lignes.append(f"<b>UNIQUE</b> ({z['nom']})")
        cons = [Spacer(1, 3)] + [Paragraph('• ' + l, s) for l in lignes]
        st += [KeepTogether([head, Spacer(1, 3)] + extra + [tab] + cons), Spacer(1, 12)]
    doc.build(st)
    return buf.getvalue()


def main():
    ms = modeles()
    app_de = {m._meta.db_table: a for a, m in ms}
    ordre = list(POS)
    infos = sorted([info(m) for _, m in ms], key=lambda i: ordre.index(i['table']))
    manque = [i['table'] for i in infos if i['table'] not in POS]
    assert not manque, manque
    w = PdfWriter()
    for part in (couverture(), diagramme(infos, app_de), dictionnaire(infos, app_de)):
        for p in PdfReader(io.BytesIO(part)).pages:
            w.add_page(p)
    w.add_metadata({'/Title': 'MPD - Lycée Ambohitromby', '/Author': 'Lycée Ambohitromby'})
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for dest in (os.path.join(base, 'frontend', 'public', 'documentation', 'mpd.pdf'), os.path.join(base, 'documentation', 'MPD_Lycee_Ambohitromby.pdf')):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            w.write(f)
        print('écrit :', dest)
    print(f'{len(infos)} tables, {len(w.pages)} pages')


if __name__ == '__main__':
    main()
