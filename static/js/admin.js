class AdminPanel {
    constructor() {
        this.loadMembers();
        this.setupEventListeners();
    }
    
    async loadMembers() {
        try {
            const response = await fetch('/api/membres');
            const membres = await response.json();
            this.populateTable(membres);
            this.populateParentSelect(membres);
        } catch (error) {
            console.error('Erreur:', error);
        }
    }
    
    populateTable(membres) {
        const tbody = document.querySelector('#membersTable tbody');
        tbody.innerHTML = '';
        
        membres.forEach(membre => {
            const nomComplet = `${membre.prenom} ${membre.postnom || ''} ${membre.nom}`.trim();
            const statut = membre.est_decede ? '☠️ Décédé(e)' : '❤️ Vivant(e)';
            const row = tbody.insertRow();
            row.innerHTML = `
                <td><strong>${nomComplet}</strong></td>
                <td><span class="badge ${membre.sexe === 'M' ? 'bg-primary' : 'bg-danger'}">${membre.sexe === 'M' ? '♂️ Masculin' : '♀️ Féminin'}</span></td>
                <td>${membre.date_naissance || '-'}</td>
                <td>${membre.adresse || '-'}</td>
                <td>${statut}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info" onclick="viewMember(${membre.id})">
                        👁️ Voir
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="editMember(${membre.id})">
                        ✏️ Modifier
                    </button>
                </td>
            `;
        });
    }
    
    populateParentSelect(membres) {
        const pereSelect = document.getElementById('pereSelect');
        const mereSelect = document.getElementById('mereSelect');
        const conjointSelect = document.getElementById('conjointSelect');
        
        pereSelect.innerHTML = '<option value="">Aucun père</option>';
        mereSelect.innerHTML = '<option value="">Aucune mère</option>';
        conjointSelect.innerHTML = '<option value="">Aucun conjoint</option>';
        
        membres.forEach(membre => {
            const nomComplet = `${membre.prenom} ${membre.postnom || ''} ${membre.nom}`.trim();
            
            if (membre.sexe === 'M') {
                const option = document.createElement('option');
                option.value = membre.id;
                option.textContent = nomComplet;
                pereSelect.appendChild(option);
            }
            
            if (membre.sexe === 'F') {
                const option = document.createElement('option');
                option.value = membre.id;
                option.textContent = nomComplet;
                mereSelect.appendChild(option);
            }
            
            const conjointOption = document.createElement('option');
            conjointOption.value = membre.id;
            conjointOption.textContent = nomComplet;
            conjointSelect.appendChild(conjointOption);
        });
    }
    
    setupEventListeners() {
        document.getElementById('addMemberForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            if (!data.pere_id) delete data.pere_id;
            if (!data.mere_id) delete data.mere_id;
            if (!data.conjoint_id) delete data.conjoint_id;
            if (!data.est_decede) data.est_decede = 0;
            
            try {
                const response = await fetch('/api/membres', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    e.target.reset();
                    this.loadMembers();
                    alert('Membre ajouté avec succès!');
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors de l\'ajout');
            }
        });
    }
}

function viewMember(id) {
    // Fonctionnalité pour voir les détails complets
    alert('Détails du membre ID: ' + id);
}

function editMember(id) {
    alert('Fonctionnalité de modification à implémenter pour ID: ' + id);
}

document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});