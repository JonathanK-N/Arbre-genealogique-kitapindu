// Test simple pour vérifier les clics
window.showFamilyDetails = function(type) {
    alert('Clic détecté sur: ' + type);
    
    if (!window.familyTreeInstance || !window.familyTreeInstance.membres) {
        alert('Données pas encore chargées');
        return;
    }
    
    const membres = window.familyTreeInstance.membres;
    alert('Nombre de membres: ' + membres.length);
    
    const modal = new bootstrap.Modal(document.getElementById('familyDetailsModal'));
    const title = document.getElementById('familyDetailsTitle');
    const content = document.getElementById('familyDetailsContent');
    
    title.textContent = 'Test - ' + type;
    content.innerHTML = '<p>Test réussi! Type: ' + type + '</p><p>Membres: ' + membres.length + '</p>';
    modal.show();
};