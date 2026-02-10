import { state } from "./state.js";
import { initializeNavigation, setStatus, showError, clearError } from "./ui.js";
import {
    checkAuthStatus,
    login,
    register,
    logout,
    fetchAccounts,
    createAccount,
    saveAccount,
    deleteAccount,
    cancelAccountEdit,
    showAccountDetail,
    renderDashboardSummary,
} from "./accounts.js";
import {
    fetchTransactions,
    saveTransaction,
    deleteTransaction,
    applyTransactionFilters,
    clearTransactionFilters,
    cancelTransactionEdit,
    startTransactionEdit,
    exportTransactionsCsv,
} from "./transactions.js";
import { createCategory, fetchCategories, updateCategoryFilters } from "./categories.js";
import { syncGmail, startGmailAuth } from "./sync.js";

function bindEventHandlers() {
    document.querySelectorAll(".tab[data-tab]").forEach((tab) => {
        tab.addEventListener("click", () => {
            const tabName = tab.getAttribute("data-tab");
            if (tabName === "accounts") {
                fetchAccounts();
            }
            if (tabName === "transactions") {
                fetchTransactions();
            }
        });
    });

    document.getElementById("login-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        login();
    });

    document.getElementById("register-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        register();
    });

    document.getElementById("logout-button")?.addEventListener("click", (event) => {
        event.preventDefault();
        logout();
    });

    document.getElementById("account-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        createAccount();
    });

    document.getElementById("account-detail-back")?.addEventListener("click", (event) => {
        event.preventDefault();
        cancelAccountEdit();
    });

    document.getElementById("account-detail")?.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const action = target.getAttribute("data-action");
        if (!action) return;

        event.preventDefault();
        if (action === "save-account") {
            saveAccount();
        }
        if (action === "delete-account") {
            deleteAccount();
        }
    });

    document.getElementById("dashboard-summary")?.addEventListener("click", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const action = target.getAttribute("data-action");
        if (action === "set-recent-window") {
            const days = Number(target.getAttribute("data-days"));
            if (!days) return;

            event.preventDefault();
            state.recentWindowDays = days;
            renderDashboardSummary(state.accounts);
            return;
        }

        if (action === "clear-dashboard-filters") {
            event.preventDefault();
            state.recentWindowDays = 30;

            const filterSelect = document.getElementById("transactions-filter-account-id");
            const dashboardSelect = document.getElementById("dashboard-account-filter");
            const startFilter = document.getElementById("transactions-filter-start");
            const endFilter = document.getElementById("transactions-filter-end");

            if (filterSelect) filterSelect.value = "";
            if (dashboardSelect) dashboardSelect.value = "";
            if (startFilter) startFilter.value = "";
            if (endFilter) endFilter.value = "";

            renderDashboardSummary(state.accounts);
            fetchTransactions();
        }

        if (action === "set-trend-mode") {
            const mode = target.getAttribute("data-mode");
            if (!mode) return;

            event.preventDefault();
            state.trendMode = mode;
            renderDashboardSummary(state.accounts);
        }

        if (action === "export-30d") {
            event.preventDefault();
            const now = new Date();
            const start = new Date();
            start.setDate(now.getDate() - 30);

            const startInput = document.getElementById("transactions-filter-start");
            const endInput = document.getElementById("transactions-filter-end");
            if (startInput) startInput.value = start.toISOString().slice(0, 10);
            if (endInput) endInput.value = now.toISOString().slice(0, 10);

            state.recentWindowDays = 30;
            renderDashboardSummary(state.accounts);
            await fetchTransactions();
            exportTransactionsCsv();
        }
    });

    document.getElementById("dashboard-summary")?.addEventListener("change", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLSelectElement)) return;

        if (target.getAttribute("data-action") !== "set-account-filter") return;

        const filterSelect = document.getElementById("transactions-filter-account-id");
        if (filterSelect) {
            filterSelect.value = target.value;
        }
        fetchTransactions();
    });

    document.getElementById("dashboard-summary")?.addEventListener("submit", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLFormElement)) return;

        if (target.id !== "quick-category-form") return;
        event.preventDefault();

        const nameInput = document.getElementById("quick-category-name");
        const parentSelect = document.getElementById("quick-category-parent");
        const name = nameInput?.value || "";
        const parentId = parentSelect?.value || "";

        const created = await createCategory({ name, parentId });
        if (created && nameInput) {
            nameInput.value = "";
        }

        updateCategoryFilters();
        renderDashboardSummary(state.accounts);
    });

    document.getElementById("accounts-list")?.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const card = target.closest(".account-card");
        if (!card) return;

        const accountId = card.getAttribute("data-account-id");
        if (!accountId) return;

        event.preventDefault();
        showAccountDetail(Number(accountId));
    });

    document.getElementById("transaction-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        saveTransaction();
    });

    document.getElementById("transaction-cancel-edit")?.addEventListener("click", (event) => {
        event.preventDefault();
        cancelTransactionEdit();
    });

    document.getElementById("transactions-filter")?.addEventListener("submit", (event) => {
        event.preventDefault();
        applyTransactionFilters();
    });

    document.getElementById("transactions-filter-clear")?.addEventListener("click", (event) => {
        event.preventDefault();
        clearTransactionFilters();
    });

    document.getElementById("accounts-refresh")?.addEventListener("click", (event) => {
        event.preventDefault();
        fetchAccounts();
    });

    document.getElementById("transactions-refresh")?.addEventListener("click", (event) => {
        event.preventDefault();
        fetchTransactions();
    });

    document.getElementById("transactions-export")?.addEventListener("click", (event) => {
        event.preventDefault();
        exportTransactionsCsv();
    });

    document.getElementById("gmail-start-sync")?.addEventListener("click", (event) => {
        event.preventDefault();
        syncGmail();
    });

    document.getElementById("gmail-start-auth")?.addEventListener("click", (event) => {
        event.preventDefault();
        startGmailAuth();
    });

    ["transactions-list", "account-transactions"].forEach((id) => {
        document.getElementById(id)?.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;

            const action = target.getAttribute("data-action");
            const transactionId = target.getAttribute("data-transaction-id");
            if (!action || !transactionId) return;

            event.preventDefault();
            if (action === "edit-transaction") {
                startTransactionEdit(Number(transactionId));
            }
            if (action === "delete-transaction") {
                deleteTransaction(Number(transactionId));
            }
        });
    });
}

function bindGlobalHandlers() {
    window.deleteAccount = deleteAccount;
    window.showAccountDetail = showAccountDetail;
    window.saveAccount = saveAccount;

    window.deleteTransaction = deleteTransaction;
    window.startTransactionEdit = startTransactionEdit;
}

async function initApp() {
    try {
        clearError();
        initializeNavigation();
        bindEventHandlers();
        bindGlobalHandlers();

        const authOk = await checkAuthStatus();
        if (!authOk) return;

        await Promise.all([fetchAccounts(), fetchTransactions(), fetchCategories()]);
        updateCategoryFilters();
        renderDashboardSummary(state.accounts);
        setStatus("Dashboard carregado.", "success");
    } catch (error) {
        showError(error.message);
    }
}

window.addEventListener("DOMContentLoaded", initApp);

window.addEventListener("auth:changed", async () => {
    if (!state.token) return;
    try {
        await Promise.all([fetchAccounts(), fetchTransactions(), fetchCategories()]);
        updateCategoryFilters();
        renderDashboardSummary(state.accounts);
        setStatus("Sessao atualizada.", "success");
    } catch (error) {
        showError(error.message);
    }
});

window.addEventListener("transactions:updated", () => {
    renderDashboardSummary(state.accounts);
});
