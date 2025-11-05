class FamilyTree {
    constructor() {
        this.svg = d3.select("#family-tree");
        this.width = 1200;
        this.height = 600;
        this.svg.attr("width", this.width).attr("height", this.height);
        
        this.g = this.svg.append("g");
        this.tree = d3.tree().size([this.width - 200, this.height - 200]);
        
        this.loadData();
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/membres');
            const membres = await response.json();
            this.renderTree(membres);
        } catch (error) {
            console.error('Erreur:', error);
        }
    }
    
    renderTree(membres) {
        const root = this.buildHierarchy(membres);
        if (!root) return;
        
        const treeData = d3.hierarchy(root);
        const treeLayout = this.tree(treeData);
        
        // Liens
        this.g.selectAll(".link")
            .data(treeLayout.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical()
                .x(d => d.x + 100)
                .y(d => d.y + 100));
        
        // Noeuds
        const node = this.g.selectAll(".node")
            .data(treeLayout.descendants())
            .enter().append("g")
            .attr("class", d => `node ${d.data.sexe === 'M' ? 'male' : 'female'}`)
            .attr("transform", d => `translate(${d.x + 100},${d.y + 100})`)
            .on("click", (event, d) => this.showMemberInfo(d.data));
        
        node.append("circle");
        
        node.append("text")
            .attr("dy", "0.35em")
            .attr("y", d => d.children ? -30 : 30)
            .style("text-anchor", "middle")
            .text(d => `${d.data.prenom} ${d.data.nom}`);
    }
    
    buildHierarchy(membres) {
        if (membres.length === 0) return null;
        
        const membresMap = new Map();
        membres.forEach(m => membresMap.set(m.id, {...m, children: []}));
        
        let root = null;
        membres.forEach(membre => {
            if (membre.parent_id) {
                const parent = membresMap.get(membre.parent_id);
                if (parent) {
                    parent.children.push(membresMap.get(membre.id));
                }
            } else {
                root = membresMap.get(membre.id);
            }
        });
        
        return root;
    }
    
    showMemberInfo(member) {
        const info = `
            <p><strong>Nom:</strong> ${member.nom}</p>
            <p><strong>Prénom:</strong> ${member.prenom}</p>
            <p><strong>Sexe:</strong> ${member.sexe === 'M' ? 'Masculin' : 'Féminin'}</p>
            ${member.date_naissance ? `<p><strong>Naissance:</strong> ${member.date_naissance}</p>` : ''}
            ${member.date_deces ? `<p><strong>Décès:</strong> ${member.date_deces}</p>` : ''}
        `;
        
        document.getElementById('memberInfo').innerHTML = info;
        new bootstrap.Modal(document.getElementById('memberModal')).show();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FamilyTree();
});