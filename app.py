import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kitapindu_secret_key_production')

def init_db():
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
    
    admin_exists = c.execute('SELECT COUNT(*) FROM admin').fetchone()[0]
    if admin_exists == 0:
        c.execute('INSERT INTO admin (username, password) VALUES (?, ?)', 
                 ('admin', generate_password_hash('kitapindu2024')))
    
    membre_exists = c.execute('SELECT COUNT(*) FROM membres').fetchone()[0]
    if membre_exists == 0:
        # Génération 1 - Fondateurs
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Kitapindu', 'Wa', 'Mwamba', '1920-01-15', 'M', 'Kinshasa, Lemba', 2))
        c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, conjoint_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 ('Mbuyi', 'Wa', 'Marie', '1925-06-10', 'F', 'Kinshasa, Lemba', 1))
        
        # Génération 2 - 8 enfants
        enfants_g2 = [
            ('Kitapindu', 'Mwamba', 'Jean', '1945-03-20', 'M', 'Kinshasa, Kasa-Vubu', 1, 2),
            ('Kitapindu', 'Mwamba', 'Paul', '1948-07-10', 'M', 'Lubumbashi, Kenya', 1, 2),
            ('Kitapindu', 'Mwamba', 'André', '1950-11-22', 'M', 'Mbuji-Mayi, Dibindi', 1, 2),
            ('Kitapindu', 'Mwamba', 'Pierre', '1953-09-30', 'M', 'Kananga, Katoka', 1, 2),
            ('Kitapindu', 'Mwamba', 'Jeanne', '1956-05-14', 'F', 'Kinshasa, Lemba', 1, 2),
            ('Kitapindu', 'Mwamba', 'Marie-Claire', '1958-08-12', 'F', 'Kinshasa, Ngaliema', 1, 2),
            ('Kitapindu', 'Mwamba', 'Joseph', '1960-12-03', 'M', 'Kinshasa, Gombe', 1, 2),
            ('Kitapindu', 'Mwamba', 'Thérèse', '1962-04-25', 'F', 'Kinshasa, Bandalungwa', 1, 2)
        ]
        
        for enfant in enfants_g2:
            c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', enfant)
        
        # Génération 3 - 45 petits-enfants (environ 5-6 par enfant)
        petits_enfants = []
        prenoms_m = ['Michel', 'David', 'Emmanuel', 'Samuel', 'Daniel', 'Gabriel', 'Raphaël', 'Nathan', 'Benjamin', 'Isaac']
        prenoms_f = ['Sophie', 'Claire', 'Grâce', 'Ruth', 'Esther', 'Rachel', 'Sarah', 'Rebecca', 'Miriam', 'Judith']
        
        id_pere = 3  # Commence avec Jean (id 3)
        for i in range(45):
            if i % 6 == 0 and i > 0:  # Change de père tous les 6 enfants
                id_pere += 1
                if id_pere > 10:  # Reset si on dépasse
                    id_pere = 3
            
            sexe = 'M' if i % 2 == 0 else 'F'
            prenom = prenoms_m[i % 10] if sexe == 'M' else prenoms_f[i % 10]
            annee = 1970 + (i % 25)
            
            petits_enfants.append((
                'Kitapindu', 'Descendant', f'{prenom}_{i+1}', f'{annee}-{(i%12)+1:02d}-{(i%28)+1:02d}',
                sexe, f'Kinshasa, Commune_{i%10}', id_pere, 2
            ))
        
        for pe in petits_enfants:
            c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', pe)
        
        # Génération 4 - 80 arrière-petits-enfants
        arriere_petits_enfants = []
        for i in range(80):
            id_pere = 11 + (i % 45)  # Parents de la génération 3
            sexe = 'M' if i % 2 == 0 else 'F'
            prenom = prenoms_m[i % 10] if sexe == 'M' else prenoms_f[i % 10]
            annee = 1995 + (i % 20)
            
            arriere_petits_enfants.append((
                'Kitapindu', 'Nouvelle', f'{prenom}_{i+100}', f'{annee}-{(i%12)+1:02d}-{(i%28)+1:02d}',
                sexe, f'Kinshasa, Zone_{i%15}', id_pere, None
            ))
        
        for ape in arriere_petits_enfants:
            c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ape)
        
        # Génération 5 - 50 membres
        generation_5 = []
        for i in range(50):
            id_pere = 56 + (i % 80)  # Parents de la génération 4
            sexe = 'M' if i % 2 == 0 else 'F'
            prenom = prenoms_m[i % 10] if sexe == 'M' else prenoms_f[i % 10]
            annee = 2010 + (i % 15)
            
            generation_5.append((
                'Kitapindu', 'Jeune', f'{prenom}_{i+200}', f'{annee}-{(i%12)+1:02d}-{(i%28)+1:02d}',
                sexe, f'Kinshasa, Secteur_{i%20}', id_pere, None
            ))
        
        for g5 in generation_5:
            c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, sexe, adresse, pere_id, mere_id) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', g5)
        
        # Ajouter quelques décédés dans les anciennes générations
        c.execute('UPDATE membres SET est_decede = 1, date_deces = "1995-03-15" WHERE id = 1')  # Mwamba
        c.execute('UPDATE membres SET est_decede = 1, date_deces = "2000-07-22" WHERE id = 2')  # Marie
        c.execute('UPDATE membres SET est_decede = 1, date_deces = "2010-11-08" WHERE id IN (3,4,5)')  # Quelques enfants
    
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

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
