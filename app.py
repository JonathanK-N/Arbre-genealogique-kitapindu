import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kitapindu-secret-key-2024')

# Configuration
DATABASE = 'kitapindu.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Créer la table des membres
    conn.execute('''
        CREATE TABLE IF NOT EXISTS membres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            postnom TEXT,
            prenom TEXT NOT NULL,
            sexe TEXT NOT NULL CHECK (sexe IN ('M', 'F')),
            date_naissance DATE,
            date_deces DATE,
            adresse TEXT,
            pere_id INTEGER,
            mere_id INTEGER,
            conjoint_id INTEGER,
            notes TEXT,
            est_decede BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pere_id) REFERENCES membres (id),
            FOREIGN KEY (mere_id) REFERENCES membres (id),
            FOREIGN KEY (conjoint_id) REFERENCES membres (id)
        )
    ''')
    
    # Vérifier si des données existent déjà
    cursor = conn.execute('SELECT COUNT(*) FROM membres')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insérer des données d'exemple
        sample_data = [
            ('Kitapindu', 'Wa', 'Moise', 'M', '1920-01-01', None, 'Kinshasa', None, None, None, 'Patriarche fondateur', 0),
            ('Kitapindu', 'Wa', 'Marie', 'F', '1925-03-15', None, 'Kinshasa', None, None, 1, 'Épouse du patriarche', 0),
            ('Kitapindu', 'Wa', 'Jean', 'M', '1945-06-20', None, 'Lubumbashi', 1, 2, None, 'Fils aîné', 0),
            ('Kitapindu', 'Wa', 'Paul', 'M', '1947-09-10', None, 'Kinshasa', 1, 2, None, 'Deuxième fils', 0),
            ('Kitapindu', 'Wa', 'Grace', 'F', '1950-12-05', None, 'Goma', 1, 2, None, 'Fille cadette', 0),
        ]
        
        conn.executemany('''
            INSERT INTO membres (nom, postnom, prenom, sexe, date_naissance, date_deces, adresse, pere_id, mere_id, conjoint_id, notes, est_decede)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
    
    conn.commit()
    conn.close()

# Routes principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'kitapindu2024':
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Identifiants incorrects', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Compter les membres
    cursor = conn.execute('SELECT COUNT(*) FROM membres')
    members_count = cursor.fetchone()[0]
    
    # Derniers membres ajoutés
    cursor = conn.execute('''
        SELECT id, nom, postnom, prenom, date_naissance 
        FROM membres 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    latest_members = []
    for row in cursor.fetchall():
        member = {
            'id': row[0],
            'full_name': f"{row[1]} {row[2] or ''} {row[3]}".strip(),
            'birth_date': datetime.strptime(row[4], '%Y-%m-%d') if row[4] else None
        }
        latest_members.append(member)
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         members_count=members_count, 
                         latest_members=latest_members)

# API Routes
@app.route('/api/membres')
def api_membres():
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT id, nom, postnom, prenom, sexe, date_naissance, date_deces, 
               adresse, pere_id, mere_id, conjoint_id, notes, est_decede
        FROM membres
        ORDER BY nom, prenom
    ''')
    
    membres = []
    for row in cursor.fetchall():
        full_name = f"{row[1]} {row[2] or ''} {row[3]}".strip()
        membre = {
            'id': row[0],
            'nom': row[1],
            'postnom': row[2],
            'prenom': row[3],
            'full_name': full_name,
            'sexe': row[4],
            'date_naissance': row[5],
            'date_deces': row[6],
            'adresse': row[7],
            'pere_id': row[8],
            'mere_id': row[9],
            'conjoint_id': row[10],
            'notes': row[11],
            'est_decede': bool(row[12])
        }
        membres.append(membre)
    
    conn.close()
    return jsonify(membres)

@app.route('/api/tree')
def api_tree():
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT id, nom, postnom, prenom, sexe, date_naissance, date_deces,
               pere_id, mere_id, conjoint_id, est_decede
        FROM membres
    ''')
    
    membres = []
    for row in cursor.fetchall():
        membre = {
            'id': row[0],
            'name': f"{row[1]} {row[2] or ''} {row[3]}".strip(),
            'firstName': row[3],
            'lastName': row[1],
            'fullName': f"{row[1]} {row[2] or ''} {row[3]}".strip(),
            'sex': row[4],
            'gender': row[4],
            'birthDate': row[5],
            'deathDate': row[6],
            'birth_year': row[5][:4] if row[5] else None,
            'death_year': row[6][:4] if row[6] else None,
            'father_id': row[7],
            'mother_id': row[8],
            'spouse_id': row[9],
            'is_deceased': bool(row[10]),
            'isDeceased': bool(row[10]),
            'address': None,
            'notes': None
        }
        membres.append(membre)
    
    conn.close()
    
    # Construire la hiérarchie
    def build_hierarchy(members):
        # Trouver les racines (sans parents)
        roots = [m for m in members if not m['father_id'] and not m['mother_id']]
        if not roots:
            # Si pas de racine claire, prendre le premier membre
            roots = [members[0]] if members else []
        
        def build_node(member):
            children = [m for m in members if m['father_id'] == member['id'] or m['mother_id'] == member['id']]
            return {
                'unitId': f"unit-{member['id']}",
                'members': [member],
                'sex': member['sex'],
                'initials': member['firstName'][0] if member['firstName'] else 'X',
                'label': member['name'],
                'primaryPhoto': None,
                'children': [build_node(child) for child in children] if children else None
            }
        
        if len(roots) == 1:
            return build_node(roots[0])
        else:
            # Créer un nœud racine virtuel
            return {
                'unitId': 'root',
                'members': [],
                'sex': 'U',
                'initials': 'R',
                'label': 'Famille Kitapindu',
                'primaryPhoto': None,
                'children': [build_node(root) for root in roots]
            }
    
    if membres:
        tree = build_hierarchy(membres)
    else:
        tree = {
            'unitId': 'empty',
            'members': [],
            'sex': 'U',
            'initials': 'E',
            'label': 'Aucun membre',
            'primaryPhoto': None,
            'children': None
        }
    
    return jsonify(tree)

@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    
    # Statistiques générales
    stats = {}
    
    # Total membres
    cursor = conn.execute('SELECT COUNT(*) FROM membres')
    stats['total_membres'] = cursor.fetchone()[0]
    
    # Par sexe
    cursor = conn.execute('SELECT sexe, COUNT(*) FROM membres GROUP BY sexe')
    sexe_stats = dict(cursor.fetchall())
    stats['hommes'] = sexe_stats.get('M', 0)
    stats['femmes'] = sexe_stats.get('F', 0)
    
    # Décédés
    cursor = conn.execute('SELECT COUNT(*) FROM membres WHERE est_decede = 1')
    stats['decedes'] = cursor.fetchone()[0]
    
    # Mariages (conjoints)
    cursor = conn.execute('SELECT COUNT(*) FROM membres WHERE conjoint_id IS NOT NULL')
    stats['mariages'] = cursor.fetchone()[0] // 2  # Diviser par 2 car chaque mariage compte 2 fois
    
    # Générations (approximation basée sur la hiérarchie)
    cursor = conn.execute('SELECT COUNT(DISTINCT pere_id) FROM membres WHERE pere_id IS NOT NULL')
    stats['generations'] = cursor.fetchone()[0] + 1  # +1 pour la génération racine
    
    conn.close()
    return jsonify(stats)

@app.route('/api/membres', methods=['POST'])
def api_add_membre():
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Non autorisé'}), 401
    
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO membres (nom, postnom, prenom, sexe, date_naissance, date_deces, 
                           adresse, pere_id, mere_id, conjoint_id, notes, est_decede)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('nom'),
        data.get('postnom'),
        data.get('prenom'),
        data.get('sexe'),
        data.get('date_naissance'),
        data.get('date_deces'),
        data.get('adresse'),
        data.get('pere_id') or None,
        data.get('mere_id') or None,
        data.get('conjoint_id') or None,
        data.get('notes'),
        bool(data.get('est_decede'))
    ))
    
    membre_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': membre_id, 'message': 'Membre ajouté avec succès'})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
