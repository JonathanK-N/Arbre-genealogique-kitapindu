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
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${membre.nom}</td>
                <td>${membre.prenom}</td>
                <td>${membre.sexe === 'M' ? 'Masculin' : 'Féminin'}</td>
                <td>${membre.date_naissance || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editMember(${membre.id})">
                        Modifier
                    </button>
                </td>
            `;
        });
    }
    
    populateParentSelect(membres) {
        const select = document.getElementById('parentSelect');
        select.innerHTML = '<option value="">Aucun parent</option>';
        
        membres.forEach(membre => {
            const option = document.createElement('option');
            option.value = membre.id;
            option.textContent = `${membre.prenom} ${membre.nom}`;
            select.appendChild(option);
        });
    }
    
    setupEventListeners() {
        document.getElementById('addMemberForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            if (!data.parent_id) delete data.parent_id;
            
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

function editMember(id) {
    alert('Fonctionnalité de modification à implémenter');
}

document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});