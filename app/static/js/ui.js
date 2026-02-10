export function showError(message) {
    const el = document.getElementById("error");
    if (el) {
        el.innerHTML = `<div class="error">❌ ${message}</div>`;
    }
}

export function clearError() {
    const el = document.getElementById("error");
    if (el) {
        el.innerHTML = "";
    }
}

export function setStatus(message, type = "info") {
    const status = document.getElementById("status");
    if (status) {
        status.innerHTML = `<div class="notice ${type}">${message}</div>`;
    }
}

export function clearStatus() {
    const status = document.getElementById("status");
    if (status) {
        status.innerHTML = "";
    }
}

export function setCurrentUser(email) {
    const el = document.getElementById("current-user-email");
    if (el) {
        el.textContent = email || "-";
    }
}

export function setActiveTab(tabName) {
    document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
    document.querySelectorAll(".section").forEach((section) => section.classList.remove("active"));

    const activeTab = document.querySelector(`.tab[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.add("active");
    }

    const activeSection = document.getElementById(`${tabName}-section`);
    if (activeSection) {
        activeSection.classList.add("active");
    }
}

export function initializeNavigation() {
    const tabs = document.querySelectorAll(".tab[data-tab]");
    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabName = tab.getAttribute("data-tab");
            if (tabName) {
                setActiveTab(tabName);
            }
        });
    });
}

export function formatDate(dateStr) {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("pt-BR");
}
