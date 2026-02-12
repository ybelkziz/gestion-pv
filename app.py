from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cle_secrete_pour_dev')

# ------------------------------------------------------------
# CONFIGURATION BASE DE DONNÉES
# ------------------------------------------------------------
# En local (PyCharm) : on utilise SQLite (fichier local)
# Sur Render : on utilise PostgreSQL (via la variable d'environnement)
if 'RENDER' in os.environ:
    # Mode production (Render)
    SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')
    # Render fournit une URL qui commence par postgres://, SQLAlchemy attend postgresql://
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    # Mode développement (local)
    SQLALCHEMY_DATABASE_URL = 'sqlite:///gestion_pv.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ------------------------------------------------------------
# MODÈLE (TABLE) POUR LES PV
# ------------------------------------------------------------
class PV(Base):
    __tablename__ = 'pvs'
    id = Column(Integer, primary_key=True)
    date = Column(String)
    caidat = Column(String)
    status = Column(Enum('traité', 'en cours', 'non traité'), default='non traité')

# ------------------------------------------------------------
# MODÈLE POUR LE COMPTEUR (une seule ligne)
# ------------------------------------------------------------
class Counter(Base):
    __tablename__ = 'counter'
    id = Column(Integer, primary_key=True, default=1)
    value = Column(Integer, default=0)

# Création des tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# ------------------------------------------------------------
# AUTHENTIFICATION
# ------------------------------------------------------------
USERS = {
    "youssouf": "belkziz",
    "hajar": "benlamine"
}

# ------------------------------------------------------------
# ROUTES PUBLIQUES
# ------------------------------------------------------------
@app.route('/')
def index():
    db = SessionLocal()
    counter = db.query(Counter).first()
    if not counter:
        counter = Counter(value=0)
        db.add(counter)
        db.commit()
    counter_value = counter.value
    # Filtrer les PV avec statut 'traité'
    traites = db.query(PV).filter(PV.status == 'traité').all()
    db.close()
    return render_template('index.html', counter=counter_value, traites=traites)

# ------------------------------------------------------------
# ROUTES D'AUTHENTIFICATION
# ------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['user'] = username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Identifiants incorrects', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Vous êtes déconnecté.', 'success')
    return redirect(url_for('index'))

# ------------------------------------------------------------
# ROUTES PROTÉGÉES
# ------------------------------------------------------------
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Veuillez vous connecter.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
def admin():
    db = SessionLocal()
    counter = db.query(Counter).first()
    if not counter:
        counter = Counter(value=0)
        db.add(counter)
        db.commit()
    all_pvs = db.query(PV).all()
    db.close()
    return render_template('admin.html', data={'entries': all_pvs, 'counter': counter.value}, username=session['user'])

@app.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    date = request.form['date']
    caidat = request.form['caidat']
    db = SessionLocal()
    # Vérifier les doublons
    existing = db.query(PV).filter_by(date=date, caidat=caidat).first()
    if existing:
        flash(f"Une entrée avec la date {date} et le caidat {caidat} existe déjà.", 'error')
        db.close()
        return redirect(url_for('admin'))
    new_entry = PV(date=date, caidat=caidat, status='non traité')
    db.add(new_entry)
    db.commit()
    db.close()
    flash("Entrée ajoutée avec succès.", 'success')
    return redirect(url_for('admin'))

@app.route('/update_status/<int:entry_id>', methods=['POST'])
@login_required
def update_status(entry_id):
    new_status = request.form['status']
    db = SessionLocal()
    entry = db.query(PV).filter_by(id=entry_id).first()
    if entry:
        entry.status = new_status
        db.commit()
        flash("Statut mis à jour.", 'success')
    else:
        flash("Entrée introuvable.", 'error')
    db.close()
    return redirect(url_for('admin'))

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    db = SessionLocal()
    entry = db.query(PV).filter_by(id=entry_id).first()
    if entry:
        db.delete(entry)
        db.commit()
        flash("Entrée supprimée.", 'success')
    else:
        flash("Entrée introuvable.", 'error')
    db.close()
    return redirect(url_for('admin'))

@app.route('/update_counter', methods=['POST'])
@login_required
def update_counter():
    try:
        new_counter = int(request.form['counter'])
    except ValueError:
        flash("Veuillez entrer un nombre valide.", 'error')
        return redirect(url_for('admin'))
    db = SessionLocal()
    counter = db.query(Counter).first()
    if not counter:
        counter = Counter(value=0)
        db.add(counter)
    counter.value = new_counter
    db.commit()
    db.close()
    flash("Compteur mis à jour.", 'success')
    return redirect(url_for('admin'))

# ------------------------------------------------------------
# LANCEMENT
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)