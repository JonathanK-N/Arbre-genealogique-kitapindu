from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'kitapindu_secret_key'

def init_db():
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS membres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        date_naissance TEXT,
        date_deces TEXT,
        sexe TEXT,
        parent_id INTEGER,
        conjoint_id INTEGER,
        photo TEXT,
        notes TEXT,
        FOREIGN KEY (parent_id) REFERENCES membres (id)
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
    membres = c.execute('''SELECT id, nom, prenom, date_naissance, date_deces, 
                          sexe, parent_id, conjoint_id FROM membres''').fetchall()
    conn.close()
    
    return jsonify([{
        'id': m[0], 'nom': m[1], 'prenom': m[2], 'date_naissance': m[3],
        'date_deces': m[4], 'sexe': m[5], 'parent_id': m[6], 'conjoint_id': m[7]
    } for m in membres])

@app.route('/api/membres', methods=['POST'])
def add_membre():
    if 'admin' not in session:
        return jsonify({'error': 'Non autorisé'}), 401
    
    data = request.json
    conn = sqlite3.connect('kitapindu.db')
    c = conn.cursor()
    c.execute('''INSERT INTO membres (nom, prenom, date_naissance, date_deces, 
                 sexe, parent_id, conjoint_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['nom'], data['prenom'], data.get('date_naissance'), 
               data.get('date_deces'), data['sexe'], data.get('parent_id'),
               data.get('conjoint_id'), data.get('notes')))
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