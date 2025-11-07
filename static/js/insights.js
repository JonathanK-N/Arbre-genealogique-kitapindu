// Fonctions globales pour les cartes cliquables
function getMembersData() {
    const app = window.familyTreeInstance;
    if (!app) return null;
    return app.membersList || app.membres || null;
}

function showFamilyDetails(type) {
    console.log('showFamilyDetails appelée avec:', type);
    
    // Attendre que les données soient chargées
    const membres = getMembersData();
    if (!membres) {
        console.log('Données pas encore chargées, attente...');
        setTimeout(() => showFamilyDetails(type), 500);
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('familyDetailsModal'));
    const title = document.getElementById('familyDetailsTitle');
    const content = document.getElementById('familyDetailsContent');
    
    let titleText = '';
    let contentHtml = '';
    
    console.log('Données disponibles:', membres.length, 'membres');
    
    switch(type) {
        case 'members':
            titleText = 'Tous les membres de la famille';
            contentHtml = generateMembersList(membres);
            break;
        case 'male':
            titleText = 'Lignées masculines';
            contentHtml = generateMaleLineages(membres);
            break;
        case 'female':
            titleText = 'Lignées féminines';
            contentHtml = generateFemaleLineages(membres);
            break;
        case 'generations':
            titleText = 'Générations par niveau';
            contentHtml = generateGenerationsList();
            break;
        case 'marriages':
            titleText = 'Unions et mariages';
            contentHtml = generateMarriagesList(membres);
            break;
        case 'deceased':
            titleText = 'Membres décédés';
            contentHtml = generateDeceasedList(membres);
            break;
    }
    
    title.textContent = titleText;
    content.innerHTML = contentHtml;
    modal.show();
}

function generateMembersList(membres) {
    if (!membres || membres.length === 0) {
        return '<p>Données en cours de chargement...</p>';
    }
    
    let html = '<div class="row g-3">';
    membres.forEach(membre => {
        html += `
            <div class="col-md-6">
                <div class="d-flex align-items-center gap-3 p-2 border rounded">
                    <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center" style="width:40px;height:40px;">
                        <span class="text-white fw-bold">${membre.prenom[0]}</span>
                    </div>
                    <div>
                        <h6 class="mb-0">${membre.prenom} ${membre.nom}</h6>
                        <small class="text-muted">${membre.sexe === 'M' ? '♂️ Masculin' : '♀️ Féminin'} • ${membre.est_decede ? '✝ Décédé(e)' : '❤️ Vivant(e)'}</small>
                    </div>
                </div>
            </div>`;
    });
    html += '</div>';
    return html;
}

function generateMaleLineages(membres) {
    if (!membres) return '<p>Données en cours de chargement...</p>';
    
    const males = membres.filter(m => m.sexe === 'M');
    let html = '<div class="list-group">';
    
    males.forEach(male => {
        const enfants = membres.filter(m => m.pere_id === male.id);
        html += `
            <div class="list-group-item">
                <h6 class="mb-1">♂️ ${male.prenom} ${male.nom}</h6>
                <p class="mb-1"><small>Descendants: ${enfants.length}</small></p>
                ${enfants.length > 0 ? `<small class="text-muted">Enfants: ${enfants.map(e => e.prenom).join(', ')}</small>` : ''}
            </div>`;
    });
    html += '</div>';
    return html;
}

function generateFemaleLineages(membres) {
    if (!membres) return '<p>Données en cours de chargement...</p>';
    
    const females = membres.filter(m => m.sexe === 'F');
    let html = '<div class="list-group">';
    
    females.forEach(female => {
        const enfants = membres.filter(m => m.mere_id === female.id);
        html += `
            <div class="list-group-item">
                <h6 class="mb-1">♀️ ${female.prenom} ${female.nom}</h6>
                <p class="mb-1"><small>Descendants: ${enfants.length}</small></p>
                ${enfants.length > 0 ? `<small class="text-muted">Enfants: ${enfants.map(e => e.prenom).join(', ')}</small>` : ''}
            </div>`;
    });
    html += '</div>';
    return html;
}

function generateGenerationsList() {
    return `
        <div class="row g-3">
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 1</h5><p class="mb-0">Fondateurs</p></div></div>
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 2</h5><p class="mb-0">Enfants</p></div></div>
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 3</h5><p class="mb-0">Petits-enfants</p></div></div>
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 4</h5><p class="mb-0">Arrière-petits-enfants</p></div></div>
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 5</h5><p class="mb-0">5ème génération</p></div></div>
            <div class="col-md-4"><div class="text-center p-3 border rounded"><h5>Génération 6</h5><p class="mb-0">6ème génération</p></div></div>
        </div>`;
}

function generateMarriagesList(membres) {
    if (!membres) return '<p>Données en cours de chargement...</p>';
    
    const mariages = [];
    membres.forEach(membre => {
        if (membre.conjoint_id) {
            const conjoint = membres.find(m => m.id === membre.conjoint_id);
            if (conjoint && membre.id < conjoint.id) {
                mariages.push({membre, conjoint});
            }
        }
    });
    
    let html = '<div class="list-group">';
    mariages.forEach(mariage => {
        html += `
            <div class="list-group-item">
                <h6 class="mb-1">💍 ${mariage.membre.prenom} ${mariage.membre.nom} ❤️ ${mariage.conjoint.prenom} ${mariage.conjoint.nom}</h6>
                <small class="text-muted">Union familiale</small>
            </div>`;
    });
    html += '</div>';
    return html;
}

function generateDeceasedList(membres) {
    if (!membres) return '<p>Données en cours de chargement...</p>';
    
    const deceased = membres.filter(m => m.est_decede);
    let html = '<div class="list-group">';
    
    deceased.forEach(membre => {
        html += `
            <div class="list-group-item">
                <h6 class="mb-1">✝ ${membre.prenom} ${membre.nom}</h6>
                <small class="text-muted">${membre.date_deces || 'Date non renseignée'}</small>
            </div>`;
    });
    html += '</div>';
    return html;
}

// Fonction pour mettre à jour les statistiques
function updateInsightCards(membres) {
    const data = membres || getMembersData();
    if (!data) return;
    
    const totalEl = document.getElementById('total-members-card');
    const maleEl = document.getElementById('male-count');
    const femaleEl = document.getElementById('female-count');
    const marriageEl = document.getElementById('marriage-count');
    const deceasedEl = document.getElementById('deceased-count');
    
    if (totalEl) totalEl.textContent = data.length;
    if (maleEl) maleEl.textContent = data.filter(m => m.sexe === 'M').length;
    if (femaleEl) femaleEl.textContent = data.filter(m => m.sexe === 'F').length;
    if (marriageEl) marriageEl.textContent = Math.floor(data.filter(m => m.conjoint_id).length / 2);
    if (deceasedEl) deceasedEl.textContent = data.filter(m => m.est_decede).length;
}

// Ajouter les événements de clic
document.addEventListener('DOMContentLoaded', () => {
    // Attendre que les éléments soient créés
    setTimeout(() => {
        const cards = document.querySelectorAll('.insight-card');
        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const type = card.getAttribute('data-type');
                if (type) {
                    console.log('Clic détecté sur:', type);
                    showFamilyDetails(type);
                }
            });
        });
    }, 1000);
});
