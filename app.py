from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
# Clé secrète pour signer les sessions (obligatoire pour utiliser session)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')

# ------------------------------------------------------------
# GESTION DU FICHIER JSON (lecture/écriture)
# ------------------------------------------------------------
DATA_FILE = "data.json"

def load_data():
    """Charge les données depuis data.json. Si le fichier n'existe pas, crée une structure par défaut."""
    if not os.path.exists(DATA_FILE):
        return {"counter": 0, "entries": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    """Sauvegarde les données dans data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------------------------------------------------
# AUTHENTIFICATION (deux comptes fixes)
# ------------------------------------------------------------
USERS = {
    "youssouf": "admin2026",
    "hajar": "admin2026"
}

# ------------------------------------------------------------
# ROUTES PUBLIQUES
# ------------------------------------------------------------
@app.route('/')
def index():
    """Page publique : affiche le compteur et les PV traités."""
    data = load_data()
    counter = data["counter"]
    # Filtrer les entrées dont le statut est "traité"
    traites = [entry for entry in data["entries"] if entry.get("status") == "traité"]
    return render_template('index.html', counter=counter, traites=traites)

# ------------------------------------------------------------
# ROUTES D'AUTHENTIFICATION
# ------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Formulaire de connexion."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            # Connexion réussie : stocke le nom dans la session
            session['user'] = username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Identifiants incorrects', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion : supprime l'utilisateur de la session."""
    session.pop('user', None)
    flash('Vous êtes déconnecté.', 'success')
    return redirect(url_for('index'))

# ------------------------------------------------------------
# ROUTES PROTÉGÉES (admin)
# ------------------------------------------------------------
def login_required(f):
    """Décorateur simple pour vérifier que l'utilisateur est connecté."""
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
    """Page d'administration : affiche le tableau et le compteur."""
    data = load_data()
    return render_template('admin.html', data=data, username=session['user'])

# ------------------------------------------------------------
# ACTIONS SUR LES DONNÉES (admin uniquement)
# ------------------------------------------------------------
@app.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    """Ajoute une nouvelle entrée (date, caidat, statut par défaut 'non traité')."""
    date = request.form['date']
    caidat = request.form['caidat']
    # Empêcher les doublons : même date ET même caidat ne peuvent coexister
    data = load_data()
    for entry in data["entries"]:
        if entry["date"] == date and entry["caidat"] == caidat:
            flash(f"Une entrée avec la date {date} et le caidat {caidat} existe déjà.", 'error')
            return redirect(url_for('admin'))
    # Génération d'un nouvel ID (incrémental simple)
    new_id = max([e["id"] for e in data["entries"]], default=0) + 1
    new_entry = {
        "id": new_id,
        "date": date,
        "caidat": caidat,
        "status": "non traité"
    }
    data["entries"].append(new_entry)
    save_data(data)
    flash("Entrée ajoutée avec succès.", 'success')
    return redirect(url_for('admin'))

@app.route('/update_status/<int:entry_id>', methods=['POST'])
@login_required
def update_status(entry_id):
    """Met à jour le statut d'une entrée."""
    new_status = request.form['status']
    data = load_data()
    for entry in data["entries"]:
        if entry["id"] == entry_id:
            entry["status"] = new_status
            save_data(data)
            flash("Statut mis à jour.", 'success')
            break
    else:
        flash("Entrée introuvable.", 'error')
    return redirect(url_for('admin'))

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Supprime une entrée."""
    data = load_data()
    data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
    save_data(data)
    flash("Entrée supprimée.", 'success')
    return redirect(url_for('admin'))

@app.route('/update_counter', methods=['POST'])
@login_required
def update_counter():
    """Modifie le compteur de fiches."""
    try:
        new_counter = int(request.form['counter'])
    except ValueError:
        flash("Veuillez entrer un nombre valide.", 'error')
        return redirect(url_for('admin'))
    data = load_data()
    data["counter"] = new_counter
    save_data(data)
    flash("Compteur mis à jour.", 'success')
    return redirect(url_for('admin'))

# ------------------------------------------------------------
# LANCEMENT
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)