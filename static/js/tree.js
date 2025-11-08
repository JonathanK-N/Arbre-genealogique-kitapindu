class FamilyTreeApp {
    constructor() {
        this.svg = d3.select("#family-tree");
        this.container = document.getElementById("tree-container");
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;

        this.svg.attr("width", this.width).attr("height", this.height);

        this.currentMode = "vertical";
        this.maxDepth = Number(document.getElementById("depth-range")?.value || 5);
        this.totalGenerations = null;
        this.depthInitialized = false;
        this.baseHierarchy = null;
        this.hierarchyRoot = null;
        this.membersList = [];
        this.memberToNode = new Map();
        this.highlightedNode = null;

        this.defs = this.svg.append("defs");
        this.createStaticGradients();

        this.rootGroup = this.svg.append("g").attr("class", "tree-group vertical");
        this.linksGroup = this.rootGroup.append("g").attr("class", "links");
        this.nodesGroup = this.rootGroup.append("g").attr("class", "nodes");

        this.zoomBehavior = d3
            .zoom()
            .scaleExtent([0.35, 3])
            .on("zoom", (event) => this.rootGroup.attr("transform", event.transform));
        this.svg.call(this.zoomBehavior);

        this.setupControls();
        this.registerResizeHandler();
        this.loadData();
    }

    registerResizeHandler() {
        window.addEventListener("resize", () => {
            this.width = this.container.clientWidth;
            this.height = this.container.clientHeight;
            this.svg.attr("width", this.width).attr("height", this.height);
            if (this.baseHierarchy) {
                this.renderTree();
            }
        });
    }

    setupControls() {
        const modeSelect = document.getElementById("display-mode");
        modeSelect.addEventListener("change", (event) => {
            this.currentMode = event.target.value;
            this.rootGroup.attr("class", `tree-group ${this.currentMode}`);
            if (this.baseHierarchy) {
                this.renderTree();
            }
        });

        document.getElementById("zoom-in").addEventListener("click", () => {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 1.2);
        });
        document.getElementById("zoom-out").addEventListener("click", () => {
            this.svg.transition().duration(300).call(this.zoomBehavior.scaleBy, 0.8);
        });
        document.getElementById("reset-view").addEventListener("click", () => {
            this.resetZoom();
        });
        document.getElementById("fullscreen").addEventListener("click", () => {
            if (!document.fullscreenElement) {
                this.container.requestFullscreen?.();
            } else {
                document.exitFullscreen?.();
            }
        });

        const depthRange = document.getElementById("depth-range");
        const depthValue = document.getElementById("depth-value");
        depthValue.textContent = this.maxDepth;
        depthRange.addEventListener("input", (event) => {
            this.maxDepth = Number(event.target.value);
            if (!Number.isFinite(this.maxDepth) || this.maxDepth <= 0) {
                this.maxDepth = this.totalGenerations || 5;
            }
            depthValue.textContent = this.maxDepth;
            if (this.baseHierarchy) {
                this.renderTree();
            }
        });

        document.getElementById("search-member").addEventListener("input", (event) => {
            const term = event.target.value.trim().toLowerCase();
            if (!term) {
                this.clearHighlight();
                return;
            }

            const entry = this.membersList.find((member) =>
                `${member.full_name}`.toLowerCase().includes(term)
            );
            if (entry) {
                this.highlightMember(entry.id);
            }
        });
    }

    async loadData() {
        try {
            const [treeResponse, membersResponse] = await Promise.all([
                fetch("/api/v1/tree"),
                fetch("/api/v1/members"),
            ]);

            const treeData = await treeResponse.json();
            this.membersList = await membersResponse.json();
            document.getElementById("total-members").textContent = this.membersList.length;

            if (!treeData || Object.keys(treeData).length === 0) {
                d3.select("#loading").html("<p>Aucune donnée disponible.</p>");
                return;
            }

            this.baseHierarchy = d3.hierarchy(treeData);
            this.totalGenerations =
                (d3.max(this.baseHierarchy.descendants(), (d) => d.depth) || 0) + 1;
            this.updateDepthControl();
            this.renderStats();

            d3.select("#loading").style("display", "none");
            this.renderTree();
        } catch (error) {
            console.error("Erreur de chargement des données:", error);
            d3.select("#loading").html("<p>Erreur lors du chargement des données</p>");
        }
    }

    renderTree() {
        if (!this.baseHierarchy) return;

        const rootCopy = this.baseHierarchy.copy();
        this.applyDepthLimit(rootCopy, this.maxDepth);
        this.hierarchyRoot = rootCopy;
        this.memberToNode.clear();

        const layout = this.getLayout();
        layout(this.hierarchyRoot);
        this.adjustLayoutForMode();

        this.hierarchyRoot.descendants().forEach((node) => {
            (node.data.members || []).forEach((member) => {
                this.memberToNode.set(member.id, node);
            });
        });

        this.drawLinks();
        this.drawNodes();
        this.centerView();
        this.renderStats();
    }

    applyDepthLimit(node, maxDepth) {
        if (!node.children) return;
        if (node.depth >= maxDepth - 1) {
            node.children = null;
            return;
        }
        node.children.forEach((child) => this.applyDepthLimit(child, maxDepth));
    }

    getLayout() {
        switch (this.currentMode) {
            case "horizontal":
                return d3
                    .tree()
                    .nodeSize([75, 220])
                    .separation((a, b) => (a.parent === b.parent ? 1.3 : 1.8));
            case "radial":
                return d3
                    .tree()
                    .size([2 * Math.PI, 1])
                    .separation((a, b) => (a.parent === b.parent ? 1 : 1.3));
            case "compact":
                return d3
                    .tree()
                    .nodeSize([60, 160])
                    .separation((a, b) => (a.parent === b.parent ? 1 : 1.3));
            default:
                return d3
                    .tree()
                    .nodeSize([95, 200])
                    .separation((a, b) => (a.parent === b.parent ? 1.4 : 2));
        }
    }

    adjustLayoutForMode() {
        const nodes = this.hierarchyRoot.descendants();
        const maxDepth = d3.max(nodes, (d) => d.depth) || 1;

        if (this.currentMode === "radial") {
            const radius = Math.min(this.width, this.height) / 2 - 120;
            nodes.forEach((node) => {
                node.y = (node.depth / maxDepth) * radius;
            });
        }
    }

    drawLinks() {
        const linkGenerator = this.getLinkGenerator();
        const links = this.linksGroup
            .selectAll("path.link")
            .data(this.hierarchyRoot.links(), (d) => `${d.source.data.unitId}-${d.target.data.unitId}`);

        links
            .join(
                (enter) => enter.append("path").attr("class", "link").attr("d", linkGenerator),
                (update) => update.attr("d", linkGenerator),
                (exit) => exit.remove()
            );
    }

    getLinkGenerator() {
        switch (this.currentMode) {
            case "horizontal":
                return d3.linkHorizontal().x((d) => d.y).y((d) => d.x);
            case "radial":
                return d3.linkRadial().angle((d) => d.x).radius((d) => d.y);
            default:
                return d3.linkVertical().x((d) => d.x).y((d) => d.y);
        }
    }

    drawNodes() {
        const nodes = this.nodesGroup
            .selectAll("g.node")
            .data(this.hierarchyRoot.descendants(), (d) => d.data.unitId);

        const nodeEnter = nodes
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", (d) => this.nodeTransform(d))
            .on("click", (event, d) => this.showMemberModal(d));

        nodeEnter
            .append("circle")
            .attr("r", (d) => this.nodeRadius(d))
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 3)
            .each((d, i, elements) => this.applyCircleFill(d3.select(elements[i]), d));

        nodeEnter
            .append("text")
            .attr("class", "node-initials")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .each((d, i, elements) => this.configureInitials(d3.select(elements[i]), d));

        nodeEnter
            .append("text")
            .attr("class", "node-label")
            .each((d, i, elements) => this.configureLabel(d3.select(elements[i]), d));

        nodeEnter
            .append("text")
            .attr("class", "node-meta")
            .each((d, i, elements) => this.configureMeta(d3.select(elements[i]), d));

        nodes
            .merge(nodeEnter)
            .transition()
            .duration(350)
            .attr("transform", (d) => this.nodeTransform(d))
            .select("circle")
            .attr("r", (d) => this.nodeRadius(d))
            .each((d, i, elements) => this.applyCircleFill(d3.select(elements[i]), d));

        nodes
            .merge(nodeEnter)
            .select("text.node-initials")
            .each((d, i, elements) => this.configureInitials(d3.select(elements[i]), d));

        nodes
            .merge(nodeEnter)
            .select("text.node-label")
            .each((d, i, elements) => this.configureLabel(d3.select(elements[i]), d));

        nodes
            .merge(nodeEnter)
            .select("text.node-meta")
            .each((d, i, elements) => this.configureMeta(d3.select(elements[i]), d));

        nodes.exit().remove();
    }

    applyCircleFill(circleSelection, node) {
        const radius = this.nodeRadius(node);
        const photoUrl = node.data.primaryPhoto;

        if (photoUrl) {
            const patternId = this.ensurePhotoPattern(node.data.unitId, photoUrl);
            circleSelection.attr("fill", `url(#${patternId})`);
        } else {
            circleSelection.attr("fill", this.nodeColor(node));
        }
    }

    ensurePhotoPattern(unitId, photoUrl) {
        const patternId = `unit-photo-${unitId}`;
        let pattern = this.defs.select(`#${patternId}`);
        if (pattern.empty()) {
            pattern = this.defs
                .append("pattern")
                .attr("id", patternId)
                .attr("patternUnits", "objectBoundingBox")
                .attr("patternContentUnits", "objectBoundingBox")
                .attr("width", 1)
                .attr("height", 1);
            pattern
                .append("image")
                .attr("preserveAspectRatio", "xMidYMid slice")
                .attr("width", 1)
                .attr("height", 1);
        }

        pattern.select("image").attr("href", photoUrl);
        return patternId;
    }

    nodeColor(node) {
        const sex = node.data.sex || "U";
        switch (sex) {
            case "M":
                return "#4f70ff";
            case "F":
                return "#ff6ea9";
            case "MX":
                return "url(#mixed-gradient)";
            default:
                return "#f9c95b";
        }
    }

    configureLabel(textSelection, node) {
        const lines = this.getLabelLines(node);
        textSelection.selectAll("tspan").remove();
        lines.forEach((line, index) => {
            textSelection
                .append("tspan")
                .attr("x", 0)
                .attr("dy", index === 0 ? 0 : 16)
                .text(line);
        });

        if (this.currentMode === "horizontal") {
            const alignRight = Boolean(node.children);
            const offset = this.nodeRadius(node) + 20;
            textSelection
                .attr("text-anchor", alignRight ? "end" : "start")
                .attr("x", alignRight ? -offset : offset)
                .attr("y", 4)
                .attr("transform", null);
        } else if (this.currentMode === "radial") {
            const angle = node.x - Math.PI / 2;
            const anchor = Math.cos(angle) >= 0 ? "start" : "end";
            const rotation = (angle * 180) / Math.PI;
            const distance = this.nodeRadius(node) + 24;
            textSelection
                .attr("text-anchor", anchor)
                .attr(
                    "transform",
                    `rotate(${rotation}) translate(${distance},${anchor === "start" ? 4 : -4})`
                );
        } else {
            textSelection
                .attr("text-anchor", "middle")
                .attr("x", 0)
                .attr("y", this.nodeRadius(node) + 26)
                .attr("transform", null);
        }
    }

    configureMeta(textSelection, node) {
        const detail = this.getMetaLine(node);
        textSelection.text(detail);

        if (this.currentMode === "horizontal") {
            const alignRight = Boolean(node.children);
            const offset = this.nodeRadius(node) + 20;
            textSelection
                .attr("text-anchor", alignRight ? "end" : "start")
                .attr("x", alignRight ? -offset : offset)
                .attr("y", 22)
                .attr("transform", null);
        } else if (this.currentMode === "radial") {
            const angle = node.x - Math.PI / 2;
            const anchor = Math.cos(angle) >= 0 ? "start" : "end";
            const rotation = (angle * 180) / Math.PI;
            const distance = this.nodeRadius(node) + 24;
            textSelection
                .attr("text-anchor", anchor)
                .attr(
                    "transform",
                    `rotate(${rotation}) translate(${distance},${anchor === "start" ? 22 : -22})`
                );
        } else {
            textSelection
                .attr("text-anchor", "middle")
                .attr("x", 0)
                .attr("y", this.nodeRadius(node) + 44)
                .attr("transform", null);
        }
    }

    configureInitials(textSelection, node) {
        if (node.data.primaryPhoto) {
            textSelection.text("").style("display", "none");
            return;
        }
        const initials = node.data.initials || this.deriveInitials(node);
        textSelection
            .text(initials)
            .style("display", initials ? "block" : "none")
            .attr("font-size", `${this.nodeRadius(node) * 0.8}`)
            .attr("dominant-baseline", "middle");
    }

    deriveInitials(node) {
        if (!node.data.members || node.data.members.length === 0) {
            return "";
        }
        return node.data.members
            .map((member) => member.initials || (member.firstName ? member.firstName[0] : ""))
            .join("")
            .slice(0, 3)
            .toUpperCase();
    }

    getLabelLines(node) {
        if (!node.data.members || node.data.members.length === 0) {
            return [node.data.label || "Sans nom"];
        }
        const firstNames = node.data.members.map((member) => member.firstName || "").join(" & ");
        const lastNames = Array.from(
            new Set(node.data.members.map((member) => member.lastName).filter(Boolean))
        ).join(" • ");
        return lastNames ? [firstNames, lastNames] : [firstNames];
    }

    getMetaLine(node) {
        if (!node.data.members || node.data.members.length === 0) {
            return "";
        }
        const periods = node.data.members
            .map((member) => {
                const birth = member.birthDate ? this.formatYear(member.birthDate) : null;
                const death = member.deathDate ? this.formatYear(member.deathDate) : null;
                if (birth && death) return `${birth} – ${death}`;
                if (birth) return `Né(e) ${birth}`;
                return null;
            })
            .filter(Boolean);
        return periods.slice(0, 2).join(" · ");
    }

    nodeRadius(node) {
        switch (this.currentMode) {
            case "compact":
                return 18;
            case "radial":
                return 20;
            case "horizontal":
                return 24;
            default:
                return 26;
        }
    }

    nodeTransform(node) {
        const [x, y] = this.nodeCoordinates(node);
        return `translate(${x},${y})`;
    }

    nodeCoordinates(node) {
        switch (this.currentMode) {
            case "horizontal":
                return [node.y, node.x];
            case "radial": {
                const angle = node.x - Math.PI / 2;
                return [
                    this.width / 2 + Math.cos(angle) * node.y,
                    this.height / 2 + Math.sin(angle) * node.y,
                ];
            }
            default:
                return [node.x, node.y];
        }
    }

    centerView() {
        const nodes = this.hierarchyRoot.descendants();
        const positions = nodes.map((node) => this.nodeCoordinates(node));

        const minX = d3.min(positions, (point) => point[0]);
        const maxX = d3.max(positions, (point) => point[0]);
        const minY = d3.min(positions, (point) => point[1]);
        const maxY = d3.max(positions, (point) => point[1]);

        const contentWidth = maxX - minX;
        const contentHeight = maxY - minY;
        const padding = 140;

        const scale = Math.min(
            (this.width - padding) / contentWidth || 1,
            (this.height - padding) / contentHeight || 1,
            1.35
        );

        const translateX = this.width / 2 - ((minX + maxX) / 2) * scale;
        const translateY = this.height / 2 - ((minY + maxY) / 2) * scale;

        const transform = d3.zoomIdentity.translate(translateX, translateY).scale(scale);
        this.svg.transition().duration(500).call(this.zoomBehavior.transform, transform);
    }

    resetZoom() {
        this.svg.transition().duration(400).call(this.zoomBehavior.transform, d3.zoomIdentity);
    }

    highlightMember(memberId) {
        this.clearHighlight();
        const node = this.memberToNode.get(memberId);
        if (!node) return;

        const selection = this.nodesGroup
            .selectAll("g.node")
            .filter((d) => d === node);
        if (selection.empty()) return;

        selection.classed("node--highlight", true);
        this.highlightedNode = selection;
        this.focusOnNode(node, 1.2);
    }

    clearHighlight() {
        if (this.highlightedNode) {
            this.highlightedNode.classed("node--highlight", false);
            this.highlightedNode = null;
        }
    }

    focusOnNode(node, scale = 1) {
        const [x, y] = this.nodeCoordinates(node);
        const transform = d3.zoomIdentity
            .translate(this.width / 2 - x * scale, this.height / 2 - y * scale)
            .scale(scale);
        this.svg.transition().duration(500).call(this.zoomBehavior.transform, transform);
    }

    showMemberModal(node) {
        const members = node.data.members || [];
        if (members.length === 0) return;

        const body = members
            .map((member) => {
                const naissance = member.birthDate ? this.formatDate(member.birthDate) : "Non renseignée";
                const deces = member.deathDate ? this.formatDate(member.deathDate) : "Non renseigné";
                const statut = member.isDeceased ? "Décédé(e)" : "Vivant(e)";
                const sexeLabel =
                    member.sex === "M" ? "Masculin" : member.sex === "F" ? "Féminin" : "—";
                return `
                    <div class="member-block">
                        <h5 class="mb-1">${member.fullName}</h5>
                        <p class="text-muted mb-2">${sexeLabel}</p>
                        <p><strong>Naissance :</strong> ${naissance}</p>
                        <p><strong>Décès :</strong> ${deces}</p>
                        <p><strong>Adresse :</strong> ${member.address || "Non renseignée"}</p>
                        <p><strong>Statut :</strong> ${statut}</p>
                        <p><strong>Notes :</strong> ${member.notes || "Aucune note enregistrée."}</p>
                    </div>
                `;
            })
            .join('<hr class="my-3">');

        document.getElementById("memberInfo").innerHTML = body;
        bootstrap.Modal.getOrCreateInstance(document.getElementById("memberModal")).show();
    }

    formatDate(isoDate) {
        try {
            const [year, month, day] = isoDate.split("-");
            return `${day}/${month}/${year}`;
        } catch {
            return isoDate;
        }
    }

    formatYear(isoDate) {
        return isoDate ? isoDate.slice(0, 4) : "";
    }

    renderStats() {
        const badgesContainer = document.getElementById("lineage-badges");
        const insightsContainer = document.getElementById("insights-cards");
        if (!badgesContainer || !insightsContainer) return;

        const totalMembers = this.membersList.length;
        const maleCount = this.membersList.filter((m) => m.sexe === "M").length;
        const femaleCount = this.membersList.filter((m) => m.sexe === "F").length;
        const livingCount = this.membersList.filter((m) => !m.est_decede).length;
        const deceasedCount = totalMembers - livingCount;

        const familyUnits = this.baseHierarchy ? this.baseHierarchy.descendants().length : 0;
        const generations = this.totalGenerations || 0;
        const depthDisplayed = Math.min(this.maxDepth, generations || this.maxDepth);

        const badgeData = [
            { label: "Branches", value: familyUnits, url: "/analytics/depth" },
            { label: "Générations", value: generations, url: "/analytics/depth" },
            { label: "Vivants", value: livingCount, url: "/analytics/living" },
            { label: "Décédés", value: deceasedCount, url: "/analytics/deceased" },
        ];

        badgesContainer.innerHTML = badgeData
            .map(
                (item) => `
                <a class="lineage-badge" href="${item.url}">
                    <strong>${item.value}</strong>
                    <span>${item.label}</span>
                </a>`
            )
            .join("");

        insightsContainer.innerHTML = `
            <a class="insight-card" href="/analytics/members">
                <div class="insight-value">${totalMembers}</div>
                <div class="insight-label">Membres recensés</div>
                <p class="mt-3 mb-0 text-muted small">Base consolidée incluant six générations du clan.</p>
            </a>
            <a class="insight-card" href="/analytics/male-lines">
                <div class="insight-value">${maleCount}</div>
                <div class="insight-label">Lignées masculines</div>
                <p class="mt-3 mb-0 text-muted small">Branches portées par les descendants Kitapindu.</p>
            </a>
            <a class="insight-card" href="/analytics/female-lines">
                <div class="insight-value">${femaleCount}</div>
                <div class="insight-label">Lignées féminines</div>
                <p class="mt-3 mb-0 text-muted small">Transmission assurée par les filles et alliances.</p>
            </a>
            <a class="insight-card" href="/analytics/depth">
                <div class="insight-value">${depthDisplayed}</div>
                <div class="insight-label">Profondeur actuelle</div>
                <p class="mt-3 mb-0 text-muted small">Ajustez la molette de génération pour explorer plus loin.</p>
            </a>
        `;
    }

    updateDepthControl() {
        const depthRange = document.getElementById("depth-range");
        const depthValue = document.getElementById("depth-value");
        if (!depthRange || !depthValue) return;

        const generations = this.totalGenerations || 1;
        const maxRange = Math.max(2, generations);
        depthRange.max = maxRange;

        if (!this.depthInitialized) {
            depthRange.value = maxRange;
            this.maxDepth = maxRange;
            this.depthInitialized = true;
        } else if (Number(depthRange.value) > maxRange) {
            depthRange.value = maxRange;
            this.maxDepth = maxRange;
        }

        depthValue.textContent = this.maxDepth;
    }

    createStaticGradients() {
        const gradient = this.defs
            .append("linearGradient")
            .attr("id", "mixed-gradient")
            .attr("x1", "0%")
            .attr("x2", "100%")
            .attr("y1", "0%")
            .attr("y2", "100%");

        gradient
            .selectAll("stop")
            .data([
                { offset: "0%", color: "#4f70ff" },
                { offset: "50%", color: "#8b5cf6" },
                { offset: "100%", color: "#ff6ea9" },
            ])
            .enter()
            .append("stop")
            .attr("offset", (d) => d.offset)
            .attr("stop-color", (d) => d.color);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.familyTreeInstance = new FamilyTreeApp();
    
    // Mise à jour des statistiques après chargement
    setTimeout(() => {
        const data = window.familyTreeInstance?.membersList;
        if (data) {
            updateInsightCards(data);
        }
    }, 1000);
});
