class AdminPanel {
    constructor() {
        this.tableBody = document.querySelector("#membersTable tbody");
        this.form = document.getElementById("addMemberForm");
        this.searchInput = document.getElementById("admin-search");
        this.selects = {
            father: document.getElementById("pereSelect"),
            mother: document.getElementById("mereSelect"),
            spouse: document.getElementById("conjointSelect"),
        };
        this.members = [];

        this.bindEvents();
        this.loadMembers();
    }

    bindEvents() {
        if (this.form) {
            this.form.addEventListener("submit", (event) => this.handleSubmit(event));
        }

        if (this.searchInput) {
            this.searchInput.addEventListener("input", () => this.renderTable());
        }
    }

    async loadMembers() {
        try {
            const response = await fetch("/api/v1/members");
            this.members = await response.json();
            this.populateSelects();
            this.renderTable();
        } catch (error) {
            console.error("Erreur de chargement des membres:", error);
            this.showMessage("Impossible de charger les membres.", "danger");
        }
    }

    populateSelects() {
        const fathers = this.members.filter((member) => member.sexe === "M");
        const mothers = this.members.filter((member) => member.sexe === "F");

        this.fillSelect(this.selects.father, fathers, "Aucun père");
        this.fillSelect(this.selects.mother, mothers, "Aucune mère");
        this.fillSelect(this.selects.spouse, this.members, "Aucun conjoint");
    }

    fillSelect(select, members, emptyLabel) {
        if (!select) return;

        select.innerHTML = `<option value="">${emptyLabel}</option>`;
        members
            .sort((a, b) => a.full_name.localeCompare(b.full_name))
            .forEach((member) => {
                const option = document.createElement("option");
                option.value = member.id;
                option.textContent = member.full_name;
                select.appendChild(option);
            });
    }

    renderTable() {
        if (!this.tableBody) return;

        const filter = (this.searchInput?.value || "").toLowerCase();
        const filteredMembers = this.members.filter((member) =>
            member.full_name.toLowerCase().includes(filter)
        );

        this.tableBody.innerHTML = "";
        filteredMembers.forEach((member) => {
            const row = this.tableBody.insertRow();
            row.innerHTML = `
                <td><strong>${member.full_name}</strong></td>
                <td>
                    <span class="badge ${member.sexe === "M" ? "bg-primary" : "bg-danger"}">
                        ${member.sexe === "M" ? "Masculin" : "Féminin"}
                    </span>
                </td>
                <td>${member.date_naissance ?? "—"}</td>
                <td>${member.adresse ?? "—"}</td>
                <td>${member.est_decede ? "Décédé(e)" : "Vivant(e)"}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-info me-2" data-action="view" data-id="${member.id}">
                        Voir
                    </button>
                    <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${member.id}">
                        Supprimer
                    </button>
                </td>
            `;
        });

        this.tableBody.querySelectorAll("button[data-action]").forEach((button) => {
            const action = button.getAttribute("data-action");
            const memberId = Number.parseInt(button.getAttribute("data-id"), 10);
            if (action === "view") {
                button.addEventListener("click", () => this.displayMember(memberId));
            } else if (action === "delete") {
                button.addEventListener("click", () => this.deleteMember(memberId));
            }
        });
    }

    async handleSubmit(event) {
        event.preventDefault();
        const formData = new FormData(this.form);
        const payload = Object.fromEntries(formData.entries());

        payload.est_decede = payload.est_decede === "1";

        ["pere_id", "mere_id", "conjoint_id"].forEach((key) => {
            if (!payload[key]) {
                payload[key] = null;
            } else {
                payload[key] = Number.parseInt(payload[key], 10);
            }
        });

        ["date_naissance", "date_deces", "postnom", "adresse", "notes"].forEach((key) => {
            if (payload[key] === "") {
                payload[key] = null;
            }
        });

        if (!payload.nom || !payload.prenom || !payload.sexe) {
            this.showMessage("Veuillez renseigner les informations obligatoires.", "warning");
            return;
        }

        try {
            const response = await fetch("/api/v1/members", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error(`Erreur serveur: ${response.status}`);
            }

            this.form.reset();
            this.showMessage("Membre ajouté avec succès.", "success");
            await this.loadMembers();
        } catch (error) {
            console.error("Erreur lors de l’ajout:", error);
            this.showMessage("Échec de l’ajout du membre.", "danger");
        }
    }

    displayMember(memberId) {
        const member = this.members.find((item) => item.id === memberId);
        if (!member) return;

        const modalContent = `
            <div class="text-center mb-3">
                <h5>${member.full_name}</h5>
                <p class="text-muted mb-0">${member.sexe === "M" ? "Masculin" : "Féminin"}</p>
            </div>
            <p><strong>Naissance :</strong> ${member.date_naissance ?? "Non renseignée"}</p>
            <p><strong>Décès :</strong> ${member.date_deces ?? "Non renseigné"}</p>
            <p><strong>Adresse :</strong> ${member.adresse ?? "Non renseignée"}</p>
            <p><strong>Statut :</strong> ${member.est_decede ? "Décédé(e)" : "Vivant(e)"}</p>
            <p><strong>Notes :</strong> ${member.notes ?? "Aucune note disponible."}</p>
        `;

        document.getElementById("memberInfo").innerHTML = modalContent;
        const modalElement = document.getElementById("memberModal");
        bootstrap.Modal.getOrCreateInstance(modalElement).show();
    }

    async deleteMember(memberId) {
        if (!confirm("Confirmer la suppression de ce membre ?")) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/members/${memberId}`, {
                method: "DELETE",
            });

            if (response.status !== 204) {
                throw new Error(`Suppression refusée (${response.status})`);
            }

            this.showMessage("Membre supprimé.", "success");
            await this.loadMembers();
        } catch (error) {
            console.error("Erreur suppression:", error);
            this.showMessage("Impossible de supprimer ce membre.", "danger");
        }
    }

    showMessage(message, variant = "info") {
        const alert = document.createElement("div");
        alert.className = `alert alert-${variant} fade position-fixed top-0 end-0 m-3 shadow`;
        alert.setAttribute("role", "alert");
        alert.style.zIndex = 1080;
        alert.textContent = message;
        document.body.appendChild(alert);

        setTimeout(() => {
            alert.classList.add("show");
        }, 10);

        setTimeout(() => {
            alert.classList.remove("show");
            setTimeout(() => alert.remove(), 200);
        }, 2800);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("membersTable")) {
        new AdminPanel();
    }
});
