class FamilyTree {
    constructor() {
        this.svg = d3.select("#family-tree");
        this.width = window.innerWidth - 100;
        this.height = window.innerHeight - 200;
        this.svg.attr("width", this.width).attr("height", this.height);
        
        this.g = this.svg.append("g");
        this.currentMode = 'vertical';
        
        this.setupControls();
        this.loadData();
    }
    
    setupControls() {
        d3.select("#display-mode").on("change", (event) => {
            this.currentMode = event.target.value;
            this.renderTree(this.membres);
        });
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/membres');
            this.membres = await response.json();
            d3.select("#loading").style("display", "none");
            this.renderTree(this.membres);
        } catch (error) {
            console.error('Erreur:', error);
        }
    }
    
    renderTree(membres) {
        if (!membres || membres.length === 0) return;
        
        this.g.selectAll("*").remove();
        
        const root = this.buildHierarchy(membres);
        if (!root) return;
        
        const treeData = d3.hierarchy(root);
        const tree = d3.tree().size([this.width - 200, this.height - 200]);
        const treeLayout = tree(treeData);
        
        // Liens
        this.g.selectAll(".link")
            .data(treeLayout.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical()
                .x(d => d.x + 100)
                .y(d => d.y + 100));
        
        // Nœuds
        const node = this.g.selectAll(".node")
            .data(treeLayout.descendants())
            .enter().append("g")
            .attr("class", d => `node ${d.data.sexe === 'M' ? 'male' : 'female'}`)
            .attr("transform", d => `translate(${d.x + 100},${d.y + 100})`)
            .on("click", (event, d) => this.showMemberInfo(d.data));
        
        // Cercles
        node.append("circle")
            .attr("r", 20);
        
        // Texte
        node.append("text")
            .attr("dy", "0.35em")
            .attr("y", d => d.children ? -30 : 30)
            .style("text-anchor", "middle")
            .text(d => `${d.data.prenom} ${d.data.nom}`);
    }
    
    buildHierarchy(membres) {
        const membresMap = new Map();
        membres.forEach(m => {
            membresMap.set(m.id, {...m, children: []});
        });
        
        let root = null;
        membres.forEach(membre => {
            if (membre.prenom === 'Mwamba' && membre.nom === 'Kitapindu') {
                root = membresMap.get(membre.id);
            }
        });
        
        if (!root) {
            root = membresMap.get(membres[0].id);
        }
        
        membres.forEach(membre => {
            if (membre.pere_id) {
                const parent = membresMap.get(membre.pere_id);
                if (parent) {
                    parent.children.push(membresMap.get(membre.id));
                }
            }
        });
        
        return root;
    }
    
    showMemberInfo(member) {
        const info = `
            <h5>${member.prenom} ${member.nom}</h5>
            <p><strong>Sexe:</strong> ${member.sexe === 'M' ? 'Masculin' : 'Féminin'}</p>
            <p><strong>Naissance:</strong> ${member.date_naissance || 'Non renseignée'}</p>
            <p><strong>Adresse:</strong> ${member.adresse || 'Non renseignée'}</p>
        `;
        
        document.getElementById('memberInfo').innerHTML = info;
        new bootstrap.Modal(document.getElementById('memberModal')).show();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FamilyTree();
});