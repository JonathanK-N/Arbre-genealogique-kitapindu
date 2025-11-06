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
        # Données d'exemple
        membres_data = [
            ('Kitapindu', 'Wa', 'Mwamba', '1920-01-15', None, 'M', 'Kinshasa, Lemba', None, None, 2, None, None, 0),
            ('Mbuyi', 'Wa', 'Marie', '1925-06-10', None, 'F', 'Kinshasa, Lemba', None, None, 1, None, None, 0),
            ('Kitapindu', 'Mwamba', 'Jean', '1945-03-20', None, 'M', 'Kinshasa, Kasa-Vubu', 1, 2, 4, None, None, 0),
            ('Tshimanga', 'Wa', 'Thérèse', '1950-08-15', None, 'F', 'Kinshasa, Kasa-Vubu', None, None, 3, None, None, 0),
            ('Kitapindu', 'Mwamba', 'Paul', '1948-07-10', None, 'M', 'Lubumbashi, Kenya', 1, 2, 6, None, None, 0),
            ('Kabongo', 'Wa', 'Sylvie', '1952-12-05', None, 'F', 'Lubumbashi, Kenya', None, None, 5, None, None, 0),
            ('Kitapindu', 'Mwamba', 'André', '1950-11-22', None, 'M', 'Mbuji-Mayi, Dibindi', 1, 2, 8, None, None, 0),
            ('Mukendi', 'Wa', 'Françoise', '1955-04-18', None, 'F', 'Mbuji-Mayi, Dibindi', None, None, 7, None, None, 0),
            ('Kitapindu', 'Mwamba', 'Pierre', '1953-09-30', None, 'M', 'Kananga, Katoka', 1, 2, 10, None, None, 0),
            ('Ngalula', 'Wa', 'Célestine', '1958-01-25', None, 'F', 'Kananga, Katoka', None, None, 9, None, None, 0),
            ('Kitapindu', 'Mwamba', 'Jeanne', '1956-05-14', None, 'F', 'Kinshasa, Lemba', 1, 2, None, None, None, 1),
        ]
        
        for membre in membres_data:
            c.execute('''INSERT INTO membres (nom, postnom, prenom, date_naissance, date_deces, 
                         sexe, adresse, pere_id, mere_id, conjoint_id, photo, notes, est_decede) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', membre)
    
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
