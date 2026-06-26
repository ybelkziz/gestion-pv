from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import tempfile, uuid
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from functools import wraps
import os, io, pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cadetaf_sig_2026_secret')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///gestion_pv.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
# expire_on_commit=False évite le DetachedInstanceError après commit/close
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

# ── MODÈLES ───────────────────────────────────────────────────────────────────

class Fiche(Base):
    __tablename__ = 'fiches'
    id             = Column(Integer, primary_key=True, autoincrement=True)
    fiche_numero   = Column(Integer, unique=True, nullable=False)
    date_pv        = Column(String(100), nullable=False)
    caidat         = Column(String(100), nullable=False)
    n_autorisation = Column(String(50))
    x_coord        = Column(Float)
    y_coord        = Column(Float)
    lambert_zone   = Column(Integer, default=1)
    metrage        = Column(Integer, default=100)
    long_2         = Column(Integer, default=50)
    accord         = Column(String(10), default='non')
    observation    = Column(Text)
    responsable    = Column(String(50))
    date_creation  = Column(DateTime, default=datetime.utcnow)
    status         = Column(SQLAlchemyEnum('traité','en cours','non traité', name='status_enum'), default='non traité')

class FicheCounter(Base):
    __tablename__ = 'fiche_counter'
    id    = Column(Integer, primary_key=True, default=1)
    value = Column(Integer, default=0)

class ImportLog(Base):
    __tablename__ = 'import_logs'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    filename    = Column(String(255))
    nb_imported = Column(Integer, default=0)
    nb_skipped  = Column(Integer, default=0)
    imported_by = Column(String(50))
    imported_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ── CAIDATS ───────────────────────────────────────────────────────────────────
# Source : hajar_youssef_caidat.xlsx — données officielles (71 caïdats)

# Caïdats N° 1-35 — gérés par Hajar
CAIDATS_HAJAR_DATA = [
    {'id':1,  'nom':'Amouguer',              'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':2,  'nom':'Bni Guil',              'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':3,  'nom':'Bni Tadjite',           'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':4,  'nom':'Bouanane',              'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':5,  'nom':'Boumerieme',            'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':6,  'nom':'En-nzala',              'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':7,  'nom':'Gourrama',              'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':8,  'nom':'Taghbalte',             'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':9,  'nom':'Ain Chair',             'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':10, 'nom':'Bouarfa',               'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':11, 'nom':'Er-rich',               'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':12, 'nom':'Figuig',                'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':13, 'nom':"M'Zizel",               'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':14, 'nom':'Sidi Aayad',            'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':15, 'nom':'Sidi Ali',              'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':16, 'nom':'Talsint',               'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':17, 'nom':'Tazarine',              'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':18, 'nom':'Ait Boudaoud',          'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':19, 'nom':'Ait Yahya',             'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':20, 'nom':'Amersid',               'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':21, 'nom':'Guir',                  'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':22, 'nom':'Ktaoua',                'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':23, 'nom':"M'Hamid El Ghizlane",   'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':24, 'nom':'Outerbat',              'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':25, 'nom':'Tagounite',             'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':26, 'nom':'Tendrara',              'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':27, 'nom':'Abbou Lakhal',          'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':28, 'nom':'Agoudim',               'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':29, 'nom':'Ain Chouater',          'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':30, 'nom':'Bou Azmou',             'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':31, 'nom':'Bouchaouene',           'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':32, 'nom':'Fezouata',              'province':'ZAGORA',      'region':'DRAA-TAFILALET'},
    {'id':33, 'nom':'Guers Tiaallaline',     'province':'MIDELT',      'region':'DRAA-TAFILALET'},
    {'id':34, 'nom':'Maatarka',              'province':'FIGUIG',      'region':'ORIENTAL-RIF'},
    {'id':35, 'nom':'Zaouiat Sidi Hamza',    'province':'MIDELT',      'region':'DRAA-TAFILALET'},
]

# Caïdats N° 36-71 — gérés par Youssouf
CAIDATS_YOUSSOUF_DATA = [
    {'id':36, 'nom':'Amellagou',             'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':37, 'nom':'Arfoud',                'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':38, 'nom':'Lkheng',                'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':39, 'nom':"M'Ssici",               'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':40, 'nom':'Melaab',                'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':41, 'nom':'Et-taous',              'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':42, 'nom':'Er-rissani',            'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':43, 'nom':'Ikniouen',              'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':44, 'nom':'Ait Hani',              'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':45, 'nom':'Jorf',                  'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':46, 'nom':"Aghbalou N'Kerdous",    'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':47, 'nom':'Assoul',                'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':48, 'nom':'Boudnib',               'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':49, 'nom':'Errachidia',            'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':50, 'nom':'Alnif',                 'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':51, 'nom':"H'Ssyia",               'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':52, 'nom':'Tadighoust',            'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':53, 'nom':'Bni M\'Hamed-Sijelmassa','province':'ERRACHIDIA', 'region':'DRAA-TAFILALET'},
    {'id':54, 'nom':'Gheris El Ouloui',      'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':55, 'nom':'Moulay Ali Cherif',     'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':56, 'nom':'Fezna',                 'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':57, 'nom':'Er-rteb',               'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':58, 'nom':'Es-sifa',               'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':59, 'nom':'Toudgha El Oulia',      'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':60, 'nom':'Goulmima',              'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':61, 'nom':'Aoufous',               'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':62, 'nom':'Aarab Sebbah Gheris',   'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':63, 'nom':'Aarab Sebbah Ziz',      'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':64, 'nom':'Ait El Farsi',          'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
    {'id':65, 'nom':"Chorfa M'Daghra",       'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':66, 'nom':'Oued Naam',             'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':67, 'nom':'Ferkla Es-soufla',      'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':68, 'nom':'Gheris Es-soufli',      'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':69, 'nom':'Ferkla El Oulia',       'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':70, 'nom':'Es-sfalat',             'province':'ERRACHIDIA',  'region':'DRAA-TAFILALET'},
    {'id':71, 'nom':'Taghzoute N\'Ait Atta', 'province':'TINGHIR',     'region':'DRAA-TAFILALET'},
]

# Listes simples de noms (pour les selects)
CAIDATS_HAJAR    = [c['nom'] for c in CAIDATS_HAJAR_DATA]
CAIDATS_YOUSSOUF = [c['nom'] for c in CAIDATS_YOUSSOUF_DATA]

# Lookup rapide : nom → infos complètes
CAIDATS_LOOKUP = {c['nom']: c for c in CAIDATS_HAJAR_DATA + CAIDATS_YOUSSOUF_DATA}

# Lookup : nom → responsable
CAIDAT_RESPONSABLE = {c['nom']: 'hajar'    for c in CAIDATS_HAJAR_DATA}
CAIDAT_RESPONSABLE.update({c['nom']: 'youssouf' for c in CAIDATS_YOUSSOUF_DATA})

# Toutes provinces et régions disponibles
ALL_PROVINCES = sorted(set(c['province'] for c in CAIDATS_HAJAR_DATA + CAIDATS_YOUSSOUF_DATA))
ALL_REGIONS   = sorted(set(c['region']   for c in CAIDATS_HAJAR_DATA + CAIDATS_YOUSSOUF_DATA))

# Liste triée alphabétiquement de tous les caïdats
ALL_CAIDATS = sorted(CAIDATS_LOOKUP.keys())

USERS = {
    "youssouf": {"password": "admin2026", "caidats": CAIDATS_YOUSSOUF},
    "hajar":    {"password": "admin2026", "caidats": CAIDATS_HAJAR},
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Veuillez vous connecter.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_counter_value(db):
    """Retourne la valeur entière du compteur (pas l'objet ORM)."""
    c = db.query(FicheCounter).first()
    if not c:
        c = FicheCounter(value=0)
        db.add(c)
        db.commit()
    return c.value

def next_available(db):
    top = db.query(Fiche).order_by(Fiche.fiche_numero.desc()).first()
    counter_val = get_counter_value(db)
    return max(counter_val, top.fiche_numero if top else 0) + 1

def fiche_to_dict(f):
    """Convertit un objet Fiche en dict. Enrichit avec province/région du caïdat."""
    caidat_nom  = f.caidat or ''
    caidat_info = CAIDATS_LOOKUP.get(caidat_nom, {})
    return {
        'id':             f.id,
        'fiche_numero':   f.fiche_numero,
        'n_autorisation': f.n_autorisation or '',
        'caidat':         caidat_nom,
        'caidat_id':      caidat_info.get('id', ''),
        'caidat_province':caidat_info.get('province', ''),
        'caidat_region':  caidat_info.get('region', ''),
        'date_pv':        f.date_pv or '',
        'x_coord':        f.x_coord,
        'y_coord':        f.y_coord,
        'lambert_zone':   f.lambert_zone,
        'metrage':        f.metrage,
        'long_2':         f.long_2,
        'accord':         f.accord or 'non',
        'observation':    f.observation or '',
        'responsable':    f.responsable or '',
        'status':         f.status or 'non traité',
        'date_creation':  f.date_creation,
    }

# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = request.form.get('username','').lower().strip()
        p = request.form.get('password','')
        if u in USERS and USERS[u]['password'] == p:
            session['user'] = u
            flash(f'Bienvenue, {u.capitalize()} !', 'success')
            return redirect(url_for('dashboard'))
        flash('Identifiants incorrects.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    db = SessionLocal()
    counter_val = get_counter_value(db)
    stats = {
        'total':        db.query(Fiche).count(),
        'traites':      db.query(Fiche).filter(Fiche.status=='traité').count(),
        'en_cours':     db.query(Fiche).filter(Fiche.status=='en cours').count(),
        'non_traite':   db.query(Fiche).filter(Fiche.status=='non traité').count(),
        'favorables':   db.query(Fiche).filter(Fiche.accord=='oui').count(),
        'defavorables': db.query(Fiche).filter(Fiche.accord=='non').count(),
    }
    recent_raw   = db.query(Fiche).order_by(Fiche.fiche_numero.desc()).limit(5).all()
    recent       = [fiche_to_dict(f) for f in recent_raw]
    stats_resp   = {u: db.query(Fiche).filter(Fiche.responsable==u).count() for u in USERS}
    db.close()

    return render_template('dashboard.html',
        counter=counter_val,
        next_num=counter_val + 1,
        stats=stats,
        recent=recent,
        stats_resp=stats_resp,
        username=session['user'])

# ── LISTE FICHES ──────────────────────────────────────────────────────────────

PAGE_SIZE = 50   # fiches par page

@app.route('/fiches')
@login_required
def fiches():
    db       = SessionLocal()
    q_status = request.args.get('status', '')
    q_caidat = request.args.get('caidat', '')
    q_accord = request.args.get('accord', '')
    q_resp   = request.args.get('responsable', '')
    q_search = request.args.get('search', '').strip()
    q_mes    = request.args.get('mes_fiches', '')
    q_province = request.args.get('province', '')
    page     = max(1, int(request.args.get('page', 1) or 1))

    query = db.query(Fiche)

    # ── Filtres SQL (rapides, côté base) ──────────────────────
    if q_mes == '1':   query = query.filter(Fiche.responsable == session['user'])
    if q_status:       query = query.filter(Fiche.status == q_status)
    if q_accord:       query = query.filter(Fiche.accord == q_accord)
    if q_resp:         query = query.filter(Fiche.responsable == q_resp)
    if q_caidat:       query = query.filter(Fiche.caidat == q_caidat)
    if q_search:
        query = query.filter(
            Fiche.n_autorisation.ilike(f'%{q_search}%') |
            Fiche.caidat.ilike(f'%{q_search}%') |
            Fiche.observation.ilike(f'%{q_search}%') |
            Fiche.fiche_numero.in_(
                [int(q_search)] if q_search.isdigit() else []
            )
        )

    # Filtre province : liste de caïdats de cette province
    if q_province:
        caidats_prov = [c['nom'] for c in CAIDATS_HAJAR_DATA + CAIDATS_YOUSSOUF_DATA
                        if c['province'] == q_province]
        query = query.filter(Fiche.caidat.in_(caidats_prov))

    total = query.count()
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, total_pages)

    rows      = query.order_by(Fiche.fiche_numero.desc())                      .offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
    all_fiches = [fiche_to_dict(f) for f in rows]
    db.close()

    return render_template('fiches.html',
        fiches=all_fiches,
        total=total,
        page=page,
        total_pages=total_pages,
        page_size=PAGE_SIZE,
        caidats=ALL_CAIDATS,
        caidats_hajar=CAIDATS_HAJAR,
        caidats_youssouf=CAIDATS_YOUSSOUF,
        all_provinces=ALL_PROVINCES,
        filters={'status': q_status, 'caidat': q_caidat, 'accord': q_accord,
                 'responsable': q_resp, 'search': q_search,
                 'mes_fiches': q_mes, 'province': q_province},
        username=session['user'])

# ── NOUVELLE FICHE ────────────────────────────────────────────────────────────

@app.route('/fiches/nouvelle', methods=['GET','POST'])
@login_required
def nouvelle_fiche():
    db = SessionLocal()
    prochain = next_available(db)

    if request.method == 'POST':
        try:
            fiche_num = int(request.form['fiche_numero'])
        except (ValueError, KeyError):
            flash('Numéro de fiche invalide.', 'error')
            db.close()
            return redirect(url_for('nouvelle_fiche'))

        if db.query(Fiche).filter_by(fiche_numero=fiche_num).first():
            flash(f'Le numéro {fiche_num} est déjà utilisé.', 'error')
            db.close()
            return redirect(url_for('nouvelle_fiche'))

        top     = db.query(Fiche).order_by(Fiche.fiche_numero.desc()).first()
        cur_max = max(get_counter_value(db), top.fiche_numero if top else 0)

        if fiche_num > cur_max + 1:
            flash(f'Impossible de sauter au n° {fiche_num}. Prochain disponible : {cur_max+1}.', 'error')
            db.close()
            return redirect(url_for('nouvelle_fiche'))

        def sf(v):
            try: return float(v) if v else None
            except: return None
        def si(v, d):
            try: return int(v) if v else d
            except: return d

        new_fiche = Fiche(
            fiche_numero   = fiche_num,
            date_pv        = request.form.get('date_pv',''),
            caidat         = request.form.get('caidat',''),
            n_autorisation = request.form.get('n_autorisation',''),
            x_coord        = sf(request.form.get('x_coord')),
            y_coord        = sf(request.form.get('y_coord')),
            lambert_zone   = si(request.form.get('lambert_zone'), 1),
            metrage        = si(request.form.get('metrage'), 100),
            long_2         = si(request.form.get('long_2'), 50),
            accord         = request.form.get('accord','non'),
            observation    = request.form.get('observation',''),
            responsable    = session['user'],
            status         = request.form.get('status','non traité'),
        )
        db.add(new_fiche)

        # Avancer le compteur si nécessaire
        c = db.query(FicheCounter).first()
        if not c:
            c = FicheCounter(value=fiche_num)
            db.add(c)
        elif fiche_num > c.value:
            c.value = fiche_num

        db.commit()
        db.close()
        flash(f'Fiche N° {fiche_num} créée.', 'success')
        return redirect(url_for('fiches'))

    user_caidats = USERS[session['user']]['caidats']
    db.close()
    return render_template('nouvelle_fiche.html',
        prochain=prochain,
        caidats=user_caidats,
        all_caidats=ALL_CAIDATS,
        caidats_lookup=CAIDATS_LOOKUP,
        caidats_hajar=CAIDATS_HAJAR,
        caidats_youssouf=CAIDATS_YOUSSOUF,
        username=session['user'])

# ── MODIFIER FICHE ────────────────────────────────────────────────────────────

@app.route('/fiches/<int:fiche_id>/modifier', methods=['GET','POST'])
@login_required
def modifier_fiche(fiche_id):
    db = SessionLocal()
    f = db.query(Fiche).filter_by(id=fiche_id).first()
    if not f:
        flash('Fiche introuvable.', 'error')
        db.close()
        return redirect(url_for('fiches'))

    if request.method == 'POST':
        def si(v, d):
            try: return int(v) if v else d
            except: return d
        def sf(v):
            try: return float(v) if v else None
            except: return None

        f.date_pv        = request.form.get('date_pv', f.date_pv)
        f.caidat         = request.form.get('caidat', f.caidat)
        f.n_autorisation = request.form.get('n_autorisation', f.n_autorisation)
        f.x_coord        = sf(request.form.get('x_coord'))
        f.y_coord        = sf(request.form.get('y_coord'))
        f.lambert_zone   = si(request.form.get('lambert_zone'), f.lambert_zone)
        f.metrage        = si(request.form.get('metrage'), f.metrage)
        f.long_2         = si(request.form.get('long_2'), f.long_2)
        f.accord         = request.form.get('accord', f.accord)
        f.observation    = request.form.get('observation', f.observation)
        f.status         = request.form.get('status', f.status)
        num = f.fiche_numero
        db.commit()
        db.close()
        flash(f'Fiche N° {num} mise à jour.', 'success')
        return redirect(url_for('fiches'))

    fiche_data = fiche_to_dict(f)
    db.close()
    return render_template('modifier_fiche.html',
        fiche=fiche_data, caidats=ALL_CAIDATS, username=session['user'])

# ── SUPPRIMER ─────────────────────────────────────────────────────────────────

@app.route('/fiches/<int:fiche_id>/supprimer', methods=['POST'])
@login_required
def supprimer_fiche(fiche_id):
    db = SessionLocal()
    f = db.query(Fiche).filter_by(id=fiche_id).first()
    if f:
        num = f.fiche_numero
        db.delete(f)
        db.commit()
        flash(f'Fiche N° {num} supprimée. Le numéro reste réservé.', 'info')
    db.close()
    return redirect(url_for('fiches'))

# ── AJAX STATUS ───────────────────────────────────────────────────────────────

@app.route('/api/fiche/<int:fiche_id>/status', methods=['POST'])
@login_required
def api_status(fiche_id):
    data  = request.get_json()
    new_s = data.get('status')
    if new_s not in ('traité','en cours','non traité'):
        return jsonify({'ok':False}), 400
    db = SessionLocal()
    f  = db.query(Fiche).filter_by(id=fiche_id).first()
    if not f:
        db.close()
        return jsonify({'ok':False}), 404
    f.status = new_s
    db.commit()
    db.close()
    return jsonify({'ok':True, 'status':new_s})

# ── AJAX CAIDAT ───────────────────────────────────────────────────────────────

@app.route('/api/fiche/<int:fiche_id>/caidat', methods=['POST'])
@login_required
def api_caidat(fiche_id):
    """Met à jour le caïdat d'une fiche via AJAX (utile après import)."""
    data       = request.get_json()
    new_caidat = data.get('caidat', '').strip()

    db = SessionLocal()
    fi = db.query(Fiche).filter_by(id=fiche_id).first()
    if not fi:
        db.close()
        return jsonify({'ok': False, 'error': 'Fiche introuvable'}), 404

    # Cas spécial __reset__ : remettre "à compléter" — testé EN PREMIER
    if new_caidat == '__reset__':
        fi.caidat      = ''
        fi.responsable = ''
        db.commit()
        db.close()
        return jsonify({'ok': True, 'caidat': '', 'reset': True})

    # Vérifier que le caïdat existe bien dans la liste officielle
    if new_caidat not in ALL_CAIDATS:
        db.close()
        return jsonify({'ok': False, 'error': f'Caïdat inconnu : {new_caidat}'}), 400

    # Le responsable est déduit du caïdat (source officielle : fichier Excel)
    responsable = CAIDAT_RESPONSABLE.get(new_caidat, '')
    fi.caidat      = new_caidat
    fi.responsable = responsable
    db.commit()
    db.close()
    info = CAIDATS_LOOKUP.get(new_caidat, {})
    return jsonify({'ok': True, 'caidat': new_caidat,
                    'province':    info.get('province', ''),
                    'region':      info.get('region', ''),
                    'caidat_id':   info.get('id', ''),
                    'responsable': responsable})

# ── IMPORT EXCEL ──────────────────────────────────────────────────────────────


def _build_logs(rows):
    """Formate les logs d'import pour le template."""
    def fmt(val):
        if not val: return ''
        if isinstance(val, str):
            try:
                from datetime import datetime as dt
                return dt.fromisoformat(val.split('.')[0]).strftime('%d/%m/%Y %H:%M')
            except: return val
        try: return val.strftime('%d/%m/%Y %H:%M')
        except: return str(val)
    return [{'filename': l.filename, 'nb_imported': l.nb_imported,
             'nb_skipped': l.nb_skipped, 'imported_by': l.imported_by,
             'imported_at': fmt(l.imported_at)}
            for l in rows]

# Dossier temporaire pour stocker les fichiers Excel entre les deux étapes
UPLOAD_TMP = os.path.join(os.path.dirname(__file__), 'tmp_imports')
os.makedirs(UPLOAD_TMP, exist_ok=True)


def _process_df_row(row, caidat_choisi, responsable_import, db, counter_val):
    """Traite une ligne du DataFrame et l'insère en base. Retourne 'ok','skip','exists'."""
    raw = row.get('fiche_N_') or row.get('fiche_N')
    try:
        is_na = pd.isna(raw)
    except:
        is_na = not str(raw).strip()
    if is_na:
        return 'skip'

    num = int(float(raw))
    if db.query(Fiche).filter_by(fiche_numero=num).first():
        return 'exists'

    # ── Date PV : extraire uniquement la partie date (max 100 chars) ──────────
    dpv = row.get('date_pv', '')
    if pd.notna(dpv) and isinstance(dpv, (int, float)):
        dpv = (pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(dpv))).strftime('%d/%m/%Y')
    else:
        dpv = str(dpv).strip() if pd.notna(dpv) else ''
    # Nettoyer : garder seulement les 10 premiers caractères si c'est une date dd/mm/yyyy
    # sinon tronquer à 100 caractères pour éviter StringDataRightTruncation
    if dpv and len(dpv) > 10:
        # Essayer d'extraire juste la date (dd/mm/yyyy) en début de chaîne
        import re
        date_match = re.match(r'(\d{2}/\d{2}/\d{4})', dpv)
        if date_match:
            dpv = date_match.group(1)
        else:
            dpv = dpv[:100]  # tronquer à 100 chars max

    acc = 'oui' if str(row.get('accord', 'non')).strip().lower() == 'oui' else 'non'

    # ── f100 : ignorer si 'nan' ou vide ──────────────────────────────────────
    f100_raw = row.get('f100')
    f100_val = ''
    if f100_raw is not None and pd.notna(f100_raw):
        f100_str = str(f100_raw).strip()
        if f100_str.lower() not in ('nan', 'none', '', '<null>'):
            f100_val = f100_str

    def gf(k1, k2=None):
        v = row.get(k1) or (row.get(k2) if k2 else None)
        try: return float(v) if v is not None and pd.notna(v) else None
        except: return None

    def gi(k1, k2=None, d=0):
        v = row.get(k1) or (row.get(k2) if k2 else None)
        try: return int(float(v)) if v is not None and pd.notna(v) else d
        except: return d

    obs_raw = str(row.get('observation') or row.get('observatio') or '').strip()
    if obs_raw.lower() in ('<null>', 'nan', 'none', ''): obs_raw = ''
    obs = (f'[Feuille topo 1/100: {f100_val}]' + (' — ' + obs_raw if obs_raw else '')) if f100_val else obs_raw

    db.add(Fiche(
        fiche_numero   = num,
        date_pv        = dpv,
        caidat         = caidat_choisi,
        n_autorisation = str(row.get('N_auto') or '').strip(),
        x_coord        = gf('X', 'x_coord'),
        y_coord        = gf('Y', 'y_coord'),
        lambert_zone   = gi('lambert_zo', 'lambert_zone', 1),
        metrage        = gi('metrage', d=100),
        long_2         = gi('long_2', d=50),
        accord         = acc,
        observation    = obs,
        responsable    = responsable_import,
        status         = 'traité' if acc == 'oui' else 'non traité',
    ))
    return ('ok', num)


@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_excel():
    """
    Import en 2 étapes.
    Le fichier Excel est stocké temporairement sur disque (évite le 413).
    step=1 → upload fichier → aperçu + token fichier temp
    step=2 → choix caïdat + token → import réel depuis fichier temp
    """

    # ── ÉTAPE 2 : Import réel depuis fichier temporaire ───────────────────────
    if request.method == 'POST' and request.form.get('step') == '2':
        caidat_choisi = request.form.get('caidat_import', '').strip()
        token         = request.form.get('file_token', '').strip()
        filename      = request.form.get('filename', 'import.xlsx')

        if caidat_choisi and caidat_choisi not in ALL_CAIDATS:
            flash('Caïdat inconnu. Sélectionnez un caïdat valide ou laissez "À compléter".', 'error')
            return redirect(url_for('import_excel'))

        # Récupérer le fichier temporaire via le token
        tmp_path = os.path.join(UPLOAD_TMP, f'{token}.pkl')
        if not os.path.exists(tmp_path):
            flash('Session expirée ou fichier introuvable. Veuillez réimporter le fichier.', 'error')
            return redirect(url_for('import_excel'))

        try:
            df = pd.read_pickle(tmp_path)
        except Exception as e:
            flash(f'Erreur de lecture du fichier temporaire : {e}', 'error')
            return redirect(url_for('import_excel'))
        finally:
            # Supprimer le fichier temp dans tous les cas
            try: os.remove(tmp_path)
            except: pass

        responsable_import = CAIDAT_RESPONSABLE.get(caidat_choisi, '') if caidat_choisi else ''

        db          = SessionLocal()
        counter_val = get_counter_value(db)
        imported = skipped = already_exists = 0

        for _, row in df.iterrows():
            try:
                result = _process_df_row(row, caidat_choisi, responsable_import, db, counter_val)
                if isinstance(result, tuple) and result[0] == 'ok':
                    num = result[1]
                    if num > counter_val: counter_val = num
                    imported += 1
                elif result == 'exists':
                    already_exists += 1; skipped += 1
                else:
                    skipped += 1
            except Exception:
                # IMPORTANT PostgreSQL : rollback obligatoire après toute erreur
                # sinon la session reste en état PendingRollbackError
                try: db.rollback()
                except: pass
                skipped += 1

        c = db.query(FicheCounter).first()
        if not c:
            db.add(FicheCounter(value=counter_val))
        elif counter_val > c.value:
            c.value = counter_val

        from datetime import datetime as dt_now
        label = caidat_choisi if caidat_choisi else 'sans caïdat'
        db.add(ImportLog(
            filename    = f'{filename} [{dt_now.now().strftime("%d/%m/%Y %H:%M")}]',
            nb_imported = imported,
            nb_skipped  = skipped,
            imported_by = session['user'],
        ))
        db.commit()
        db.close()

        msg = f'Import ({label}) : {imported} fiche(s) importée(s)'
        if already_exists:
            msg += f', {already_exists} déjà existante(s) ignorée(s)'
        flash(msg + '.', 'success')
        return redirect(url_for('fiches'))

    # ── ÉTAPE 1 : Upload + analyse du fichier ─────────────────────────────────
    if request.method == 'POST' and request.form.get('step') == '1':
        f = request.files.get('excel_file')
        if not f or not f.filename.endswith(('.xlsx', '.xls')):
            flash('Fichier Excel requis (.xlsx ou .xls).', 'error')
            return redirect(url_for('import_excel'))

        raw_bytes = f.read()
        try:
            xl = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=None)
        except Exception as e:
            flash(f'Erreur lecture : {e}', 'error')
            return redirect(url_for('import_excel'))

        df = None
        for sn, sdf in xl.items():
            sdf.columns = [str(c).strip() for c in sdf.columns]
            if any(c in sdf.columns for c in ['fiche_N_', 'N_auto', 'fiche_N']):
                df = sdf; break

        if df is None:
            flash('Colonnes attendues introuvables (fiche_N_, N_auto).', 'error')
            return redirect(url_for('import_excel'))

        db = SessionLocal()
        nums_existants = {r[0] for r in db.query(Fiche.fiche_numero).all()}
        db.close()

        nouvelles = []
        for _, row in df.iterrows():
            raw = row.get('fiche_N_') or row.get('fiche_N')
            try:
                num = int(float(raw))
                if num not in nums_existants:
                    nouvelles.append(num)
            except:
                pass

        if not nouvelles:
            flash('Toutes les fiches de ce fichier existent déjà en base.', 'warning')
            return redirect(url_for('import_excel'))

        # Stocker le DataFrame sur disque avec un token unique (évite le 413)
        token    = str(uuid.uuid4())
        tmp_path = os.path.join(UPLOAD_TMP, f'{token}.pkl')
        df.to_pickle(tmp_path)

        # Aperçu : 5 premières nouvelles fiches
        apercu = []
        for _, row in df.iterrows():
            raw = row.get('fiche_N_') or row.get('fiche_N')
            try:
                num = int(float(raw))
                if num in set(nouvelles[:5]):
                    dpv = row.get('date_pv', '')
                    if isinstance(dpv, (int, float)):
                        dpv = (pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(dpv))).strftime('%d/%m/%Y')
                    apercu.append({
                        'num':    num,
                        'n_auto': str(row.get('N_auto') or '').strip(),
                        'date':   str(dpv).strip() if pd.notna(dpv) else '',
                        'accord': str(row.get('accord') or '').strip(),
                        'f100':   str(row.get('f100') or '').strip(),
                    })
            except:
                pass

        db2  = SessionLocal()
        logs = _build_logs(db2.query(ImportLog).order_by(ImportLog.imported_at.desc()).limit(10).all())
        db2.close()

        return render_template('import.html',
            step=2,
            filename=f.filename,
            file_token=token,
            nb_nouvelles=len(nouvelles),
            nb_existantes=len(df) - len(nouvelles),
            apercu=apercu,
            caidats_hajar=CAIDATS_HAJAR,
            caidats_youssouf=CAIDATS_YOUSSOUF,
            caidats_lookup=CAIDATS_LOOKUP,
            logs=logs,
            username=session['user'])

    # ── GET ────────────────────────────────────────────────────────────────────
    db   = SessionLocal()
    rows = db.query(ImportLog).order_by(ImportLog.imported_at.desc()).limit(10).all()
    logs = _build_logs(rows)

    nb_sans_caidat = db.query(Fiche).filter(
        (Fiche.caidat == '') | (Fiche.caidat == None)
    ).count()
    db.close()

    return render_template('import.html',
        step=1, logs=logs, nb_sans_caidat=nb_sans_caidat,
        username=session['user'])

    def fmt_date(val):
        """SQLite retourne parfois un str, parfois un datetime — on gère les deux."""
        if not val:
            return ''
        if isinstance(val, str):
            # SQLite stocke au format 'YYYY-MM-DD HH:MM:SS.ffffff'
            try:
                from datetime import datetime as dt
                d = dt.fromisoformat(val.split('.')[0])
                return d.strftime('%d/%m/%Y %H:%M')
            except Exception:
                return val
        try:
            return val.strftime('%d/%m/%Y %H:%M')
        except Exception:
            return str(val)

    logs = [{'filename':    l.filename,
             'nb_imported': l.nb_imported,
             'nb_skipped':  l.nb_skipped,
             'imported_by': l.imported_by,
             'imported_at': fmt_date(l.imported_at)}
            for l in rows]

    # Compter les fiches sans caïdat pour afficher le bloc de correction
    nb_sans_caidat = db.query(Fiche).filter(
        (Fiche.caidat == '') | (Fiche.caidat == None)
    ).count()
    db.close()

    return render_template('import.html',
        step=1,
        logs=logs,
        nb_sans_caidat=nb_sans_caidat,
        username=session['user'])

# ── API STATS ─────────────────────────────────────────────────────────────────

@app.route('/api/stats')
@login_required
def api_stats():
    db = SessionLocal()
    rows = db.query(Fiche).all()
    by_caidat, by_month, by_resp = {}, {}, {'youssouf':0,'hajar':0}
    for f in rows:
        by_caidat[f.caidat] = by_caidat.get(f.caidat,0)+1
        # SQLite peut retourner date_creation en str ou en datetime
        dc = f.date_creation
        if dc and isinstance(dc, str):
            try:
                from datetime import datetime as dt
                dc = dt.fromisoformat(dc.split('.')[0])
            except Exception:
                dc = None
        m = dc.strftime('%Y-%m') if dc else 'N/A'
        by_month[m] = by_month.get(m,0)+1
        if f.responsable in by_resp:
            by_resp[f.responsable] += 1
    # KPI live pour mise à jour du tableau de bord
    total       = len(rows)
    traites     = sum(1 for f in rows if f.status == 'traité')
    en_cours    = sum(1 for f in rows if f.status == 'en cours')
    non_traite  = sum(1 for f in rows if f.status == 'non traité')
    favorables  = sum(1 for f in rows if f.accord == 'oui')
    defavorables= sum(1 for f in rows if f.accord == 'non')
    counter_val = get_counter_value(db)
    db.close()
    return jsonify({
        'by_caidat':   by_caidat,
        'by_month':    dict(sorted(by_month.items())),
        'by_resp':     by_resp,
        'kpi': {
            'total':        total,
            'traites':      traites,
            'en_cours':     en_cours,
            'non_traite':   non_traite,
            'favorables':   favorables,
            'defavorables': defavorables,
        },
        'counter': counter_val,
    })

@app.route('/api/counter', methods=['POST'])
@login_required
def api_counter():
    data = request.get_json()
    try:
        new_val = int(data.get('value', 0))
    except:
        return jsonify({'ok':False,'error':'Valeur invalide'}), 400

    db  = SessionLocal()
    cur = get_counter_value(db)
    if new_val <= cur:
        db.close()
        return jsonify({'ok':False,'error':f'Le compteur ne peut pas descendre (actuel: {cur})'}), 400

    c = db.query(FicheCounter).first()
    c.value = new_val
    db.commit()
    db.close()
    return jsonify({'ok':True,'value':new_val})

# ── SUPPRESSION TOTALE DE TOUTES LES FICHES ─────────────────────────────────

@app.route('/api/supprimer_tout', methods=['POST'])
@login_required
def api_supprimer_tout():
    """Supprime TOUTES les fiches et remet le compteur à 0.
    Protégé par un mot de passe de confirmation.
    """
    data = request.get_json()
    confirmation = data.get('confirmation', '')
    if confirmation != 'SUPPRIMER TOUT':
        return jsonify({'ok': False, 'error': 'Confirmation incorrecte'}), 400

    db = SessionLocal()
    nb = db.query(Fiche).count()
    db.query(Fiche).delete()
    db.query(ImportLog).delete()
    # Remettre le compteur à 0
    c = db.query(FicheCounter).first()
    if c:
        c.value = 0
    db.commit()
    db.close()
    return jsonify({'ok': True, 'deleted': nb})

# ── RÉINITIALISATION DES FICHES SANS CAÏDAT ─────────────────────────────────

@app.route('/api/reset_sans_caidat', methods=['POST'])
@login_required
def api_reset_sans_caidat():
    """
    Remet à vide le responsable de toutes les fiches importées sans caïdat.
    Appelé une seule fois pour corriger l'import initial.
    """
    db = SessionLocal()
    # Fiches sans caïdat ET dont le responsable a été forcé à youssouf
    fiches = db.query(Fiche).filter(
        (Fiche.caidat == '') | (Fiche.caidat == None)
    ).all()
    count = 0
    for f in fiches:
        f.responsable = ''   # on efface — sera renseigné quand le caïdat sera choisi
        count += 1
    db.commit()
    db.close()
    return jsonify({'ok': True, 'reset': count})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
