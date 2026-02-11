import { getAuthHeaders, requestJson } from "./api.js";
import { state } from "./state.js";
import { clearError, showError, setStatus, formatDate, escapeHtml } from "./ui.js";

export async function fetchTransactions() {
    clearError();
    try {
        const params = new URLSearchParams();
        const accountId = document.getElementById("transactions-filter-account-id")?.value;
        const categoryId = document.getElementById("transactions-filter-category-id")?.value;
        const startDate = document.getElementById("transactions-filter-start")?.value;
        const endDate = document.getElementById("transactions-filter-end")?.value;

        if (accountId) params.set("account_id", accountId);
        if (categoryId) params.set("category_id", categoryId);
        if (startDate) params.set("start_date", new Date(startDate).toISOString());
        if (endDate) params.set("end_date", new Date(endDate).toISOString());

        const url = params.toString() ? `/transactions/?${params.toString()}` : "/transactions/";

        const data = await requestJson(url, {
            headers: { ...getAuthHeaders() },
        });
        const transactions = data.items || [];
        renderTransactions(transactions, "transactions-list");
    } catch (error) {
        showError(error.message);
    }
}

export function renderTransactions(transactions, elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;

    if (transactions.length === 0) {
        state.transactions = [];
        window.dispatchEvent(new Event("transactions:updated"));
        container.innerHTML = `
            <div class="empty-state">
                <p>Nenhuma transacao encontrada</p>
            </div>
        `;
        return;
    }

    state.transactions = transactions;
    window.dispatchEvent(new Event("transactions:updated"));
    const total = transactions.reduce((sum, t) => sum + (t.amount || 0), 0);
    const categories = state.categories || {};
    const formatCategory = (categoryId) => {
        if (!categoryId) return "Sem categoria";
        const category = categories[String(categoryId)] || categories[categoryId];
        return category?.name || `Categoria ${categoryId}`;
    };

    container.innerHTML = `
        <div class="card" style="margin-bottom: 16px;">
            <div class="info-row" style="border-bottom: none;">
                <span class="label">Total em Transacoes</span>
                <span class="amount">R$ ${total.toFixed(2)}</span>
            </div>
        </div>
        ${transactions
            .map(
                (t) => `
            <div class="transaction">
                <div class="transaction-header">
                    <div>
                        <div class="merchant">${escapeHtml(t.merchant || t.description || "Transacao")}</div>
                        <div class="date">${formatDate(t.transaction_date)}</div>
                    </div>
                    <span class="amount">R$ ${(t.amount || 0).toFixed(2)}</span>
                </div>
                <div class="category-row">
                    <span class="category-badge">${escapeHtml(formatCategory(t.category_id))}</span>
                </div>
                <div class="actions-row" style="margin-top: 8px;">
                    <button class="btn btn-small btn-secondary" data-action="edit-transaction" data-transaction-id="${t.id}">Editar</button>
                    <button class="btn btn-small btn-danger" data-action="delete-transaction" data-transaction-id="${t.id}">Excluir</button>
                </div>
                ${
                    t.installments_total
                        ? `
                    <div style="margin-top: 8px; font-size: 12px; color: #666;">
                        Parcela ${t.installments_current}/${t.installments_total}
                    </div>
                `
                        : ""
                }
            </div>
        `
            )
            .join("")}
    `;
}

export function applyTransactionFilters() {
    fetchTransactions();
}

export function clearTransactionFilters() {
    const accountFilter = document.getElementById("transactions-filter-account-id");
    const categoryFilter = document.getElementById("transactions-filter-category-id");
    const startFilter = document.getElementById("transactions-filter-start");
    const endFilter = document.getElementById("transactions-filter-end");

    if (accountFilter) accountFilter.value = "";
    if (categoryFilter) categoryFilter.value = "";
    if (startFilter) startFilter.value = "";
    if (endFilter) endFilter.value = "";
    fetchTransactions();
}

export function fillTransactionForm(transaction) {
    const accountInput = document.getElementById("transaction-account-id");
    const amountInput = document.getElementById("transaction-amount");
    const merchantInput = document.getElementById("transaction-merchant");
    const descriptionInput = document.getElementById("transaction-description");
    const categoryInput = document.getElementById("transaction-category-id");
    const dateInput = document.getElementById("transaction-date");
    const typeInput = document.getElementById("transaction-type");
    const methodInput = document.getElementById("transaction-method");

    if (accountInput) accountInput.value = transaction.account_id || "";
    if (amountInput) amountInput.value = transaction.amount || "";
    if (merchantInput) merchantInput.value = transaction.merchant || "";
    if (descriptionInput) descriptionInput.value = transaction.description || "";
    if (categoryInput) categoryInput.value = transaction.category_id || "";
    if (dateInput) {
        dateInput.value = transaction.transaction_date
            ? new Date(transaction.transaction_date).toISOString().slice(0, 16)
            : "";
    }
    if (typeInput) typeInput.value = transaction.transaction_type || "";
    if (methodInput) methodInput.value = transaction.payment_method || "";
}

export function resetTransactionForm() {
    [
        "transaction-account-id",
        "transaction-amount",
        "transaction-merchant",
        "transaction-description",
        "transaction-category-id",
        "transaction-date",
        "transaction-type",
        "transaction-method",
    ].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
}

export function startTransactionEdit(transactionId) {
    const transaction = state.transactions.find((item) => item.id === transactionId);
    if (!transaction) {
        showError("Transacao nao encontrada");
        return;
    }

    state.editingTransactionId = transaction.id;
    const title = document.getElementById("transaction-form-title");
    if (title) title.textContent = "Editar Transacao";
    fillTransactionForm(transaction);
    setStatus("Edicao de transacao ativa.", "info");
}

export function cancelTransactionEdit() {
    state.editingTransactionId = null;
    const title = document.getElementById("transaction-form-title");
    if (title) title.textContent = "Nova Transacao";
    resetTransactionForm();
    setStatus("Edicao cancelada.", "info");
}

function csvEscape(value) {
    if (value === null || value === undefined) return "";
    const stringValue = String(value);
    if (stringValue.includes("\"") || stringValue.includes(",") || stringValue.includes("\n")) {
        return `"${stringValue.replace(/"/g, '""')}"`;
    }
    return stringValue;
}

export function exportTransactionsCsv() {
    if (!state.transactions.length) {
        showError("Nenhuma transacao para exportar");
        return;
    }

    const headers = [
        "id",
        "account_id",
        "amount",
        "merchant",
        "description",
        "transaction_date",
        "transaction_type",
        "payment_method",
        "category_id",
    ];

    const rows = state.transactions.map((t) => [
        t.id,
        t.account_id,
        t.amount,
        t.merchant,
        t.description,
        t.transaction_date,
        t.transaction_type,
        t.payment_method,
        t.category_id,
    ]);

    const csv = [headers, ...rows]
        .map((row) => row.map(csvEscape).join(","))
        .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `transacoes_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

export async function saveTransaction() {
    clearError();

    try {
        const accountId = document.getElementById("transaction-account-id")?.value;
        const amount = document.getElementById("transaction-amount")?.value;

        if (!accountId || !amount) {
            showError("Informe conta e valor");
            return;
        }

        const payload = {
            account_id: Number(accountId),
            amount: Number(amount),
            merchant: document.getElementById("transaction-merchant")?.value.trim() || null,
            description: document.getElementById("transaction-description")?.value.trim() || null,
            category_id: document.getElementById("transaction-category-id")?.value
                ? Number(document.getElementById("transaction-category-id").value)
                : null,
            transaction_date: document.getElementById("transaction-date")?.value
                ? new Date(document.getElementById("transaction-date").value).toISOString()
                : null,
            transaction_type: document.getElementById("transaction-type")?.value || null,
            payment_method: document.getElementById("transaction-method")?.value || null,
        };

        const isEdit = Boolean(state.editingTransactionId);
        const url = isEdit ? `/transactions/${state.editingTransactionId}` : "/transactions/";
        const method = isEdit ? "PUT" : "POST";

        await requestJson(url, {
            method,
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
            body: JSON.stringify(payload),
        });

        setStatus(isEdit ? "Transacao atualizada." : "Transacao criada.", "success");
        cancelTransactionEdit();
        await fetchTransactions();
    } catch (error) {
        showError(error.message);
    }
}

export async function deleteTransaction(transactionId) {
    clearError();
    if (!confirm("Excluir esta transacao?")) return;

    try {
        await requestJson(`/transactions/${transactionId}`, {
            method: "DELETE",
            headers: { ...getAuthHeaders() },
        });
        setStatus("Transacao excluida.", "success");
        await fetchTransactions();
    } catch (error) {
        showError(error.message);
    }
}
