"""
Générateur de Fiche de Vérification CADETAF — v3
- Logo PNG réel intégré
- Pied de page image réelle
- Cases à cocher correctes
- Mise en page compacte et fidèle
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import io, os

W, H = A4  # 595.27 x 841.89 pts

import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
LOGO_PATH   = _os.path.join(_BASE, 'static', 'logo.png')
FOOTER_PATH = _os.path.join(_BASE, 'static', 'pied_de_page.png')

BLACK      = colors.black
BLUE_DARK  = colors.HexColor('#1F3864')
GOLD_BG    = colors.HexColor('#FDF3E3')

def draw_checkbox(c, x, y, size=7.5, checked=False):
    """Case à cocher : carré + coche si coché."""
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.5)
    c.setFillColor(WHITE if not checked else WHITE)
    c.rect(x, y, size, size, fill=0)
    if checked:
        c.setLineWidth(0.7)
        c.setStrokeColor(BLACK)
        # Coche ✓ manuscrite
        c.line(x+1,   y+size*0.45, x+size*0.38, y+size*0.1)
        c.line(x+size*0.38, y+size*0.1, x+size-1, y+size*0.85)

WHITE = colors.white

def draw_fiche(c, data, logo_path=LOGO_PATH, footer_path=FOOTER_PATH):
    ML = 1.5*cm    # marge gauche
    MR = W - 1.5*cm  # marge droite
    MT = H - 1.2*cm  # haut
    FW = MR - ML     # largeur utile : ~17.5cm
    CX = W / 2

    accord = str(data.get('accord', 'non')).lower().strip()
    # Nettoyer observation
    obs = str(data.get('observation', '') or '')
    for p in ('[Feuille topo 1/100:', ']', '<Null>', 'nan', 'None'):
        obs = obs.replace(p, '')
    obs = obs.strip(' —\n').strip()

    # ── FILIGRANE léger ────────────────────────────────────────────
    c.saveState()
    c.setFillColor(colors.HexColor('#F5E6C8'))
    c.setFillAlpha(0.10)
    c.setFont('Helvetica-Bold', 180)
    c.translate(CX, H/2 - 2*cm)
    c.rotate(32)
    c.drawCentredString(0, 0, "CADETAF")
    c.restoreState()

    y = MT

    # ── LOGO PNG ───────────────────────────────────────────────────
    logo_w = FW * 0.58   # ~10cm
    logo_h = logo_w * (285/793)  # ratio réel
    lx = CX - logo_w/2
    c.drawImage(logo_path, lx, y - logo_h,
                width=logo_w, height=logo_h,
                mask='auto', preserveAspectRatio=True)
    y -= logo_h + 8

    # Ligne de séparation sous logo
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.6)
    c.line(ML, y, MR, y)
    y -= 16

    # ── Fiche N° / Date ────────────────────────────────────────────
    c.setFillColor(BLACK)
    c.setFont('Helvetica', 8.5)
    c.drawString(ML, y, "Fiche N°")
    c.setFont('Helvetica-Bold', 8.5)
    fnum = str(data.get('fiche_numero', ''))
    c.drawString(ML + 38, y, fnum)
    c.setFont('Helvetica', 8.5)
    fnum_w = c.stringWidth(fnum, 'Helvetica-Bold', 8.5)
    c.drawString(ML + 38 + fnum_w + 3, y, "/Dir")
    date_ed = str(data.get('date_edition', datetime.now().strftime('%d/%m/%Y')))
    c.drawString(MR - 80, y, "Le")
    c.setFont('Helvetica-Bold', 8.5)
    c.drawString(MR - 63, y, date_ed)
    c.setFont('Helvetica', 8.5)
    y -= 22

    # ── Titre principal ────────────────────────────────────────────
    title = "FICHE DE VERIFICATION DE COORDONNEES"
    tw = FW * 0.68
    tx0 = CX - tw/2
    c.setStrokeColor(BLACK)
    c.setLineWidth(0.7)
    c.rect(tx0, y - 2, tw, 12, fill=0)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(CX, y + 1, title)
    y -= 20

    # ══════════════════════════════════════════════════════════════
    # SECTION 1 : AUTORISATION
    # ══════════════════════════════════════════════════════════════
    def hline(yy, lw=0.4):
        c.setStrokeColor(BLACK); c.setLineWidth(lw)
        c.line(ML, yy, MR, yy)

    hline(y + 9)
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(BLACK)
    c.drawString(ML, y, "INFORMATIONS SUR L'AUTORISATION OBJET DU TRANSFERT :")
    hline(y - 2)
    y -= 13

    c.setFont('Helvetica', 8)
    c.drawString(ML, y, "Numéro de l'autorisation à transférer :")
    c.setFont('Helvetica-Bold', 9)
    c.drawString(ML + 160, y, str(data.get('n_autorisation', '')))
    hline(y - 2)
    y -= 12

    # Longueur / Largeur
    c.setFont('Helvetica', 7.8)
    c.drawString(ML + 30, y, "Longueur")
    c.drawString(CX - 30, y, "Largeur")
    y -= 10
    metrage = data.get('metrage', '')
    c.drawString(ML + 30, y, "mentionnée")
    c.setFont('Helvetica-Bold', 8)
    c.drawString(ML + 80, y, str(metrage) if metrage else '')
    c.setFont('Helvetica', 7.8)
    c.drawString(CX - 30, y, "mentionnée")
    long2 = data.get('long_2', '')
    c.setFont('Helvetica-Bold', 8)
    c.drawString(CX + 40, y, str(long2) if long2 else '')
    c.drawString(MR - 40, y, "Filon")
    c.setFont('Helvetica', 7.8)
    y -= 10
    c.drawString(ML + 30, y, "dans le PV =")
    c.drawString(CX - 30, y, "dans le PV =")
    hline(y - 2)
    y -= 12

    # Coordonnées
    c.setFont('Helvetica', 7.8)
    c.drawString(ML + 30, y, "Nouvelles Coordonnées")
    c.drawString(ML + 120, y, "X =")
    c.setFont('Helvetica-Bold', 8.5)
    xv = data.get('x_coord', '')
    yv = data.get('y_coord', '')
    if xv: c.drawString(ML + 136, y, str(int(float(xv))))
    c.setFont('Helvetica', 7.8)
    c.drawString(CX + 5, y, "Y =")
    c.setFont('Helvetica-Bold', 8.5)
    if yv: c.drawString(CX + 20, y, str(int(float(yv))))
    hline(y - 2)
    y -= 11

    c.setFont('Helvetica', 7.8)
    c.drawString(ML + 120, y, "Carte Géographique 1/100")
    c.setFont('Helvetica-Bold', 8)
    f100 = str(data.get('f100', data.get('caidat', '')) or '')
    c.drawString(ML + 230, y, f100)
    hline(y - 2)
    y -= 15

    c.setFont('Helvetica-Bold', 8)
    c.drawString(ML, y, "Réf. PV :")
    c.setFont('Helvetica', 8)
    dpv    = str(data.get('date_pv', '') or '')[:60]
    caidat = str(data.get('caidat', '') or '')
    # Caïdat en rouge/bleu foncé avant la date
    if caidat:
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(BLUE_DARK)
        c.drawString(ML + 48, y, caidat)
        c.setFillColor(BLACK)
        c.setFont('Helvetica', 8)
        c.drawString(ML + 48 + c.stringWidth(caidat, 'Helvetica-Bold', 8) + 6, y, dpv)
    else:
        c.drawString(ML + 48, y, dpv)

    # ══════════════════════════════════════════════════════════════
    # SECTION 2 : INFORMATIONS COORDONNÉES
    # ══════════════════════════════════════════════════════════════
    y -= 22
    hline(y + 9)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(ML, y, "INFORMATIONS SUR LES COORDONNEES")
    hline(y - 2)
    y -= 14

    # Colonnes oui/non — alignées à droite
    col_oui_label = MR - 70
    col_non_label = MR - 28
    box_sz = 7.5
    label_w = 22

    c.setFont('Helvetica', 8)
    c.drawCentredString(col_oui_label + label_w/2, y + 6, "oui")
    c.drawCentredString(col_non_label + label_w/2, y + 6, "non")

    # Logique cases à cocher
    obs_lower = obs.lower()

    # ── Règle 1 : dans domaine CADETAF ───────────────────────────
    # Toujours OUI sauf si observation mentionne "hors zone" / "hors cadetaf"
    hors_zone_mots = ['hors zone', 'hors cadetaf', 'hors de la zone',
                      'hors du domaine', 'hors domaine', 'exterieur',
                      'hors-zone', 'horszone', 'en dehors', 'hors zoning cadetaf']
    in_cadetaf = not any(m in obs_lower for m in hors_zone_mots)

    # ── Règle 2 : zones objets d'appel à la concurrence ──────────
    # OUI si l'un des mots-clés est détecté
    conc_mots = ['concurrence', 'appel', 'apc', 'zoning',
                 'appel public', 'appel a la concurrence',
                 'objet appel', 'zone appel']
    in_concurrence = any(m in obs_lower for m in conc_mots)

    # ── Règle 3 : rayon d'autres AMA ─────────────────────────────
    # OUI si l'un des mots-clés est détecté
    ama_mots = ['ama', 'domaine', 'autoris', 'autre ama',
                'autres ama', 'rayon', 'chevauchement', 'chevauche']
    in_ama = any(m in obs_lower for m in ama_mots)

    ck = [
        (in_cadetaf,    not in_cadetaf),
        (in_concurrence, not in_concurrence),
        (in_ama,         not in_ama),
    ]

    questions = [
        "Font-elles parties du domaine CADETAF ?",
        "Rentrent-elles dans les zones objets d'appel à la concurrence ?",
        "Rentrent-elles dans le rayon d'autres AMA ?",
    ]
    row_h = 14
    for i, (lbl, (co, cn)) in enumerate(zip(questions, ck)):
        ry = y - 5 - i * row_h
        c.setFont('Helvetica', 7.8)
        c.setFillColor(BLACK)
        c.drawString(ML, ry, lbl)
        draw_checkbox(c, col_oui_label + (label_w - box_sz)/2, ry - 1, box_sz, co)
        draw_checkbox(c, col_non_label + (label_w - box_sz)/2, ry - 1, box_sz, cn)

    y -= 5 + len(questions) * row_h + 16

    # ── Remarques SIG ──────────────────────────────────────────────
    c.setFont('Helvetica', 8)
    c.setFillColor(BLACK)
    c.drawString(ML, y, "Remarques SIG :")

    obs_x  = ML + 70
    obs_w  = FW - 70
    obs_h  = 55

    c.setStrokeColor(BLACK); c.setLineWidth(0.5)
    c.rect(obs_x, y - obs_h + 9, obs_w, obs_h, fill=0)

    if obs and obs.lower() not in ('0', '<null>', ''):
        c.setFont('Helvetica', 7.5)
        words, lines_out, line = obs.split(), [], ''
        for w in words:
            t = (line + ' ' + w).strip()
            if c.stringWidth(t, 'Helvetica', 7.5) < obs_w - 6:
                line = t
            else:
                if line: lines_out.append(line)
                line = w
        if line: lines_out.append(line)
        # top de la box = y - obs_h + 9 + obs_h = y + 9
        # on commence 7pt sous le top → y + 9 - 7 = y + 2
        obs_top = y + 9 - 8
        for li, ln in enumerate(lines_out[:4]):
            c.drawString(obs_x + 3, obs_top - li * 9, ln)

    # ── Avis favorable / défavorable ──────────────────────────────
    # y pointe encore sur le haut de la zone obs ; la box finit à y-obs_h+9
    avis_y = y - obs_h + 9 - 14   # 14pt sous le bas de la box
    av_cx = CX

    # Centrer les deux avis symétriquement autour du centre de page
    fav_x  = CX - 85   # case "Avis Favorable"
    defav_x = CX + 30  # case "Avis défavorable"

    c.setFont('Helvetica', 8.5)
    c.setFillColor(BLACK)
    draw_checkbox(c, fav_x, avis_y, 8, accord == 'oui')
    c.setFillColor(BLACK)
    c.drawString(fav_x + 12, avis_y + 0.5, "Avis Favorable")

    draw_checkbox(c, defav_x, avis_y, 8, accord != 'oui')
    c.setFont('Helvetica', 8.5)
    c.setFillColor(BLACK)
    c.drawString(defav_x + 12, avis_y + 0.5, "Avis defavorable")

    # ══════════════════════════════════════════════════════════════
    # SIGNATURES
    # ══════════════════════════════════════════════════════════════
    y = avis_y - 40
    sig_h = 90
    cw    = FW / 3

    sig_labels = [
        "Avis du responsable SIG",
        "Avis du Chef du Service Technique",
        "Avis du Directeur",
    ]
    c.setStrokeColor(BLACK); c.setLineWidth(0.5)
    # Seulement les 2 traits verticaux séparateurs intérieurs
    for i in range(1, 3):
        vx = ML + i * cw
        c.line(vx, y + 15, vx, y - sig_h)
    for i, lbl in enumerate(sig_labels):
        sx = ML + i * cw
        c.setFont('Helvetica-Bold', 7.5)
        c.setFillColor(BLACK)
        c.drawCentredString(sx + cw/2, y + 8, lbl)
        c.setFont('Helvetica', 7.5)
        c.drawString(sx + 4, y - sig_h + 22, "Signature:")

    # ══════════════════════════════════════════════════════════════
    # PIED DE PAGE — image réelle
    # ══════════════════════════════════════════════════════════════
    footer_y = 0.8*cm
    footer_w = FW
    footer_h = footer_w * (79/1225)   # ratio réel

    c.drawImage(footer_path,
                ML, footer_y,
                width=footer_w, height=footer_h,
                mask='auto', preserveAspectRatio=True)


def generer_pdf_fiche(fiche_data):
    buf = io.BytesIO()
    cv  = canvas.Canvas(buf, pagesize=A4)
    draw_fiche(cv, fiche_data)
    cv.showPage(); cv.save()
    buf.seek(0)
    return buf.getvalue()

def generer_pdf_fiches_multiples(fiches_data):
    buf = io.BytesIO()
    cv  = canvas.Canvas(buf, pagesize=A4)
    for fd in fiches_data:
        draw_fiche(cv, fd)
        cv.showPage()
    cv.save()
    buf.seek(0)
    return buf.getvalue()


if __name__ == '__main__':
    tests = [
        {
            'fiche_numero':  3511,
            'n_autorisation': '132/04',
            'metrage':        100,
            'long_2':         '',
            'x_coord':        608869,
            'y_coord':        433618,
            'f100':           'Tawz Ouest',
            'date_pv':        'PV Taouz du 23/04/2026',
            'date_edition':   '01/07/2026',
            'accord':         'oui',
            'observation':    "remarque: existence d'anciens travaux",
        },
        {
            'fiche_numero':  3514,
            'n_autorisation': '530/08',
            'metrage':        50,
            'long_2':         '',
            'x_coord':        607202,
            'y_coord':        431270,
            'f100':           'Tawz Ouest',
            'date_pv':        'PV Taouz du 23/04/2026',
            'date_edition':   '01/07/2026',
            'accord':         'non',
            'observation':    "remarque: rentre dans le domaine de l'AMA N°98/07",
        },
        {
            'fiche_numero':  3469,
            'n_autorisation': '2025/18',
            'metrage':        100,
            'long_2':         '',
            'x_coord':        589825,
            'y_coord':        160941,
            'f100':           'Gourrama',
            'date_pv':        'PV khang mdaghra 01/04/2026',
            'date_edition':   '22/06/2026',
            'accord':         'non',
            'observation':    'remarque: rentre dans le domaine de 3 autorisations, 2023/192, 2025/17 et 2023/330',
        },
    ]
    pdf = generer_pdf_fiches_multiples(tests)
    with open('/home/claude/test_fiche_v3.pdf', 'wb') as f:
        f.write(pdf)
    print(f"✅ {len(pdf)} bytes — {len(tests)} fiches")
