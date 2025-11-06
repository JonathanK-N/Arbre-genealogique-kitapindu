from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'kitapindu_secret_key'

def init_db():
    # Supprimer l'ancienne base si elle existe
    import os
    if os.path.exists('kitapindu.db'):
        os.remove('kitapindu.db')
    
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS membres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        postnom TEXT,
        prenom TEXT NOT NULL,
        date_naissance TEXT,
        date_deces TEXT,
        sexe TEXT NOT NULL,
        adresse TEXT,
        pere_id INTEGER,
        mere_id INTEGER,
        conjoint_id INTEGER,
        photo TEXT,
        notes TEXT,
        est_decede INTEGER DEFAULT 0,
        FOREIGN KEY (pere_id) REFERENCES membres (id),
        FOREIGN KEY (mere_id) REFERENCES membres (id),
        FOREIGN KEY (conjoint_id) REFERENCES membres (id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')
    
    # Admin par défaut
    admin_exists = c.execute('SELECT COUNT(*) FROM admin').fetchone()[0]
    if admin_exists == 0:
        c.execute('INSERT INTO admin (username, password) VALUES (?, ?)', 
                 ('admin', generate_password_hash('kitapindu2024')))
    
    # Données d'exemple complètes
    membre_exists = c.execute('SELECT COUNT(*) FROM membres').fetchone()[0]
    if membre_exists == 0:
        # Génération 1 - Fondateurs
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Wa', 'Mwamba', '1920-01-15', 'M', 'Kinshasa, Lemba', 2))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Mbuyi', 'Wa', 'Marie', '1925-06-10', 'F', 'Kinshasa, Lemba', 1))
        
        # Génération 2 - Enfants (5 enfants)
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Mwamba', 'Jean', '1945-03-20', 'M', 'Kinshasa, Kasa-Vubu', 1, 2, 4))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Tshimanga', 'Wa', 'Thérèse', '1950-08-15', 'F', 'Kinshasa, Kasa-Vubu', 3))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Mwamba', 'Paul', '1948-07-10', 'M', 'Lubumbashi, Kenya', 1, 2, 6))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Kabongo', 'Wa', 'Sylvie', '1952-12-05', 'F', 'Lubumbashi, Kenya', 5))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Mwamba', 'André', '1950-11-22', 'M', 'Mbuji-Mayi, Dibindi', 1, 2, 8))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Mukendi', 'Wa', 'Françoise', '1955-04-18', 'F', 'Mbuji-Mayi, Dibindi', 7))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Mwamba', 'Pierre', '1953-09-30', 'M', 'Kananga, Katoka', 1, 2, 10))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Ngalula', 'Wa', 'Célestine', '1958-01-25', 'F', 'Kananga, Katoka', 9))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id, est_decede) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Mwamba', 'Jeanne', '1956-05-14', 'F', 'Kinshasa, Lemba', 1, 2, 1))
        
        # Génération 3 - Petits-enfants (12 enfants)
        # Enfants de Jean et Thérèse
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Jean', 'Michel', '1970-02-14', 'M', 'Kinshasa, Kasa-Vubu', 3, 4))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Jean', 'Sophie', '1972-08-22', 'F', 'Kinshasa, Kasa-Vubu', 3, 4))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Jean', 'David', '1975-12-30', 'M', 'Kinshasa, Kasa-Vubu', 3, 4))
        
        # Enfants de Paul et Sylvie
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Paul', 'Claire', '1978-05-18', 'F', 'Lubumbashi, Kenya', 5, 6))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Paul', 'Emmanuel', '1980-09-12', 'M', 'Lubumbashi, Kenya', 5, 6))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Paul', 'Grâce', '1983-03-07', 'F', 'Lubumbashi, Kenya', 5, 6))
        
        # Enfants d'André et Françoise
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'André', 'Joseph', '1981-11-03', 'M', 'Mbuji-Mayi, Dibindi', 7, 8))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'André', 'Esther', '1984-07-19', 'F', 'Mbuji-Mayi, Dibindi', 7, 8))
        
        # Enfants de Pierre et Célestine
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Pierre', 'Samuel', '1985-12-25', 'M', 'Kananga, Katoka', 9, 10))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Pierre', 'Ruth', '1988-04-11', 'F', 'Kananga, Katoka', 9, 10))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Pierre', 'Daniel', '1990-10-16', 'M', 'Kananga, Katoka', 9, 10))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_auth():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    admin = c.execute('SELECT password FROM admin WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if admin and check_password_hash(admin[0], password):
        session['admin'] = True
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/api/membres')
def get_membres():
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    membres = c.execute('''SELECT id, nom, postnom, prenom, date_naissance, date_deces, 
                          sexe, adresse, pere_id, mere_id, conjoint_id, photo, notes, est_decede FROM membres''').fetchall()
    conn.close()
    
    return jsonify([{
        'id': m[0], 'nom': m[1], 'postnom': m[2], 'prenom': m[3], 'date_naissance': m[4],
        'date_deces': m[5], 'sexe': m[6], 'adresse': m[7], 'pere_id': m[8], 'mere_id': m[9],
        'conjoint_id': m[10], 'photo': m[11], 'notes': m[12], 'est_decede': m[13]
    } for m in membres])

@app.route('/api/membres', methods=['POST'])
def add_membre():
    if 'admin' not in session:
        return jsonify({'error': 'Non autorisé'}), 401
    
    data = request.json
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, date_deces, 
                 sexe, adresse, pere_id, mere_id, conjoint_id, photo, notes, est_decede) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['nom'], data.get('postnom'), data['prenom'], data.get('date_naissance'), 
               data.get('date_deces'), data['sexe'], data.get('adresse'), data.get('pere_id'),
               data.get('mere_id'), data.get('conjoint_id'), data.get('photo'), 
               data.get('notes'), data.get('est_decede', 0)))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8080)
@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    if 'admin' not in session:
        return jsonify({'error': 'Non autorisé'}), 401
    
    if 'photo' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Ici vous pouvez ajouter la logique de sauvegarde des photos
    # Pour l'instant, on retourne juste un succès
    return jsonify({'success': True, 'filename': file.filename})