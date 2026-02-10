import { getAuthHeaders, getToken, persistToken, requestJson } from "./api.js";
import { state } from "./state.js";
import { clearError, clearStatus, formatDate, setActiveTab, setCurrentUser, showError, setStatus } from "./ui.js";
import { renderTransactions } from "./transactions.js";

function buildSparkline(transactions) {
    const ordered = [...transactions]
        .filter((t) => t.transaction_date)
        .sort((a, b) => new Date(a.transaction_date) - new Date(b.transaction_date))
        .slice(-12);

    if (ordered.length < 2) {
        return `
            <div class="sparkline sparkline-empty">
                <span>Sem dados suficientes</span>
            </div>
        `;
    }

    const values = ordered.map((t) => Math.abs(Number(t.amount) || 0));
    const maxValue = Math.max(...values, 1);
    const points = values
        .map((value, index) => {
            const x = (index / (values.length - 1)) * 120;
            const y = 36 - (value / maxValue) * 30;
            return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");

    return `
        <div class="sparkline">
            <svg viewBox="0 0 120 40" aria-hidden="true">
                <polyline points="${points}" />
            </svg>
        </div>
    `;
}

export async function fetchAccounts() {
    clearError();
    try {
        const data = await requestJson("/accounts/", {
            headers: { ...getAuthHeaders() },
        });
        const accounts = data.items || [];
        state.accounts = accounts;
        renderDashboardSummary(accounts);
        renderAccounts(accounts);
        updateSyncAccounts(accounts);
        updateTransactionAccountOptions(accounts);
    } catch (error) {
        showError(error.message);
    }
}

export function renderDashboardSummary(accounts) {
    const container = document.getElementById("dashboard-summary");
    if (!container) return;

    const windowDays = state.recentWindowDays || 30;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - windowDays);

    const currentFilter = document.getElementById("transactions-filter-account-id")?.value || "";
    const currentCategoryName = document.getElementById("quick-category-name")?.value || "";
    const currentCategoryParent = document.getElementById("quick-category-parent")?.value || "";

    const totalAccounts = accounts.length;
    const totalBalance = accounts.reduce((sum, acc) => sum + (acc.last_balance || 0), 0);
    const filteredTransactions = state.transactions.filter((t) => {
        if (!t.transaction_date) return false;
        return new Date(t.transaction_date) >= cutoff;
    });
    const recentTransactions = [...filteredTransactions]
        .sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date))
        .slice(0, 3);

    const accountLookup = new Map(
        accounts.map((acc) => [
            acc.id,
            acc.nickname ? `${acc.bank_name} (${acc.nickname})` : acc.bank_name,
        ])
    );

    const spendingByAccount = new Map();
    filteredTransactions.forEach((t) => {
        const amount = Number(t.amount) || 0;
        const current = spendingByAccount.get(t.account_id) || 0;
        spendingByAccount.set(t.account_id, current + amount);
    });

    const now = new Date();
    const monthBuckets = new Map();
    for (let i = 5; i >= 0; i -= 1) {
        const monthDate = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const key = `${monthDate.getFullYear()}-${String(monthDate.getMonth() + 1).padStart(2, "0")}`;
        monthBuckets.set(key, {
            label: monthDate.toLocaleString("pt-BR", { month: "short", year: "2-digit" }),
            total: 0,
        });
    }

    state.transactions.forEach((t) => {
        if (!t.transaction_date) return;
        const date = new Date(t.transaction_date);
        const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        if (!monthBuckets.has(key)) return;
        const bucket = monthBuckets.get(key);
        bucket.total += Number(t.amount) || 0;
    });

    const monthTotals = [...monthBuckets.values()];
    const trendMode = state.trendMode || "absolute";
    const trendValues = monthTotals.map((item) =>
        trendMode === "net" ? item.total : Math.abs(item.total)
    );
    const maxMonthValue = Math.max(...trendValues.map((value) => Math.abs(value)), 1);

    const merchantTotals = new Map();
    filteredTransactions.forEach((t) => {
        const label = (t.merchant || t.description || "Transacao").trim();
        const current = merchantTotals.get(label) || 0;
        merchantTotals.set(label, current + Math.abs(Number(t.amount) || 0));
    });

    const categoriesById = state.categories || {};
    const categoryList = Object.values(categoriesById).sort((a, b) =>
        (a.name || "").localeCompare(b.name || "")
    );
    const categoryTotals = new Map();
    filteredTransactions.forEach((t) => {
        const categoryId = t.category_id ? String(t.category_id) : "uncategorized";
        const current = categoryTotals.get(categoryId) || 0;
        categoryTotals.set(categoryId, current + Math.abs(Number(t.amount) || 0));
    });

    const formatCategoryLabel = (categoryId) => {
        if (categoryId === "uncategorized") return "Sem categoria";
        const category = categoriesById[categoryId];
        if (!category) return `Categoria ${categoryId}`;

        if (category.parent_id && categoriesById[String(category.parent_id)]) {
            const parent = categoriesById[String(category.parent_id)];
            return `${parent.name} / ${category.name}`;
        }
        return category.name || `Categoria ${categoryId}`;
    };

    const topMerchants = [...merchantTotals.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    const maxMerchantValue = Math.max(...topMerchants.map((item) => item[1]), 1);

    const topCategories = [...categoryTotals.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
    const maxCategoryValue = Math.max(...topCategories.map((item) => item[1]), 1);

    const incomeTotal = filteredTransactions
        .filter((t) => Number(t.amount) > 0)
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);
    const expenseTotal = filteredTransactions
        .filter((t) => Number(t.amount) < 0)
        .reduce((sum, t) => sum + Math.abs(Number(t.amount || 0)), 0);
    const totalFlow = incomeTotal + expenseTotal || 1;
    const incomeRatio = (incomeTotal / totalFlow) * 100;
    const netCashflow = incomeTotal - expenseTotal;

    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const startOfPrevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const endOfPrevMonth = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999);

    const monthToDateNet = state.transactions
        .filter((t) => t.transaction_date && new Date(t.transaction_date) >= startOfMonth)
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);

    const prevMonthNet = state.transactions
        .filter((t) => {
            if (!t.transaction_date) return false;
            const date = new Date(t.transaction_date);
            return date >= startOfPrevMonth && date <= endOfPrevMonth;
        })
        .reduce((sum, t) => sum + Number(t.amount || 0), 0);

    const netDelta = monthToDateNet - prevMonthNet;
    const netDeltaPct = prevMonthNet
        ? (netDelta / Math.abs(prevMonthNet)) * 100
        : null;

    const txCount = filteredTransactions.length;
    const avgAmount = txCount
        ? filteredTransactions.reduce((sum, t) => sum + Math.abs(Number(t.amount) || 0), 0) / txCount
        : 0;
    const maxIncomeTx = filteredTransactions
        .filter((t) => Number(t.amount) > 0)
        .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))[0];
    const maxExpenseTx = filteredTransactions
        .filter((t) => Number(t.amount) < 0)
        .sort((a, b) => Math.abs(Number(b.amount || 0)) - Math.abs(Number(a.amount || 0)))[0];

    const spendingRows = [...spendingByAccount.entries()]
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .slice(0, 4)
        .map(([accountId, amount]) => {
            const label = accountLookup.get(accountId) || `Conta ${accountId}`;
            return `
                <div class="info-row">
                    <span class="label">${label}</span>
                    <span class="value">R$ ${amount.toFixed(2)}</span>
                </div>
            `;
        })
        .join("");

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <span class="card-title">Resumo</span>
                <span class="badge">${totalAccounts} contas</span>
                <span class="badge ${netCashflow >= 0 ? "success" : "danger"}">
                    Net R$ ${netCashflow.toFixed(2)}
                </span>
            </div>
            <div class="info-row">
                <span class="label">Saldo total</span>
                <span class="value">R$ ${totalBalance.toFixed(2)}</span>
            </div>
            <div class="info-row" style="border-bottom: none;">
                <span class="label">Transacoes (${windowDays}d)</span>
                <span class="value">${filteredTransactions.length}</span>
            </div>
            <div class="field">
                <label class="label" for="dashboard-account-filter">Conta rapida</label>
                <select id="dashboard-account-filter" class="select" data-action="set-account-filter">
                    <option value="" ${currentFilter ? "" : "selected"}>Todas</option>
                    ${accounts
                        .map((acc) => {
                            const label = acc.nickname
                                ? `${acc.bank_name} (${acc.nickname})`
                                : acc.bank_name;
                            const selected = String(acc.id) === String(currentFilter) ? "selected" : "";
                            return `<option value="${acc.id}" ${selected}>${label}</option>`;
                        })
                        .join("")}
                </select>
            </div>
            <div class="filters" data-section="dashboard-filters">
                ${[7, 30, 90]
                    .map(
                        (days) => `
                        <button
                            class="filter-chip ${windowDays === days ? "active" : ""}"
                            data-action="set-recent-window"
                            data-days="${days}"
                            type="button"
                        >
                            ${days}d
                        </button>
                    `
                    )
                    .join("")}
                <button class="filter-chip" data-action="clear-dashboard-filters" type="button">
                    Limpar filtros
                </button>
                <button class="filter-chip" data-action="export-30d" type="button">
                    Exportar 30d CSV
                </button>
            </div>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Nova categoria</span>
            </div>
            <form id="quick-category-form" class="quick-form">
                <div class="field">
                    <label class="label" for="quick-category-name">Nome</label>
                    <input
                        id="quick-category-name"
                        class="input"
                        type="text"
                        value="${currentCategoryName}"
                        placeholder="Ex: Alimentacao"
                    />
                </div>
                <div class="field">
                    <label class="label" for="quick-category-parent">Categoria pai</label>
                    <select id="quick-category-parent" class="select">
                        <option value="" ${currentCategoryParent ? "" : "selected"}>Sem pai</option>
                        ${categoryList
                            .map((category) => {
                                const selected =
                                    String(category.id) === String(currentCategoryParent) ? "selected" : "";
                                return `<option value="${category.id}" ${selected}>${category.name}</option>`;
                            })
                            .join("")}
                    </select>
                </div>
                <button class="btn btn-small btn-success" type="submit">Criar categoria</button>
            </form>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Ultimas transacoes</span>
            </div>
            ${
                recentTransactions.length
                    ? recentTransactions
                          .map(
                              (t) => `
                        <div class="info-row">
                            <span class="label">${t.merchant || t.description || "Transacao"}</span>
                            <span class="value">R$ ${(t.amount || 0).toFixed(2)} · ${formatDate(t.transaction_date)}</span>
                        </div>
                    `
                          )
                          .join("")
                    : `
                    <div class="empty-state">
                        <p>Nenhuma transacao recente</p>
                    </div>
                `
            }
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Entradas x Saidas</span>
            </div>
            <div class="split-bar">
                <div class="split-bar-income" style="width: ${incomeRatio.toFixed(1)}%"></div>
            </div>
            <div class="info-row">
                <span class="label">Entradas</span>
                <span class="value">R$ ${incomeTotal.toFixed(2)}</span>
            </div>
            <div class="info-row" style="border-bottom: none;">
                <span class="label">Saidas</span>
                <span class="value">R$ ${expenseTotal.toFixed(2)}</span>
            </div>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">MTD vs mes anterior</span>
            </div>
            <div class="comparison-grid">
                <div>
                    <div class="label">MTD (net)</div>
                    <div class="value">R$ ${monthToDateNet.toFixed(2)}</div>
                </div>
                <div>
                    <div class="label">Mes anterior (net)</div>
                    <div class="value">R$ ${prevMonthNet.toFixed(2)}</div>
                </div>
                <div class="comparison-pill ${netDelta >= 0 ? "positive" : "negative"}">
                    ${netDelta >= 0 ? "+" : ""}R$ ${netDelta.toFixed(2)}
                    ${netDeltaPct !== null ? `(${netDeltaPct.toFixed(1)}%)` : ""}
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">KPIs rapidos</span>
            </div>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="label">Ticket medio</div>
                    <div class="value">R$ ${avgAmount.toFixed(2)}</div>
                </div>
                <div class="kpi-card">
                    <div class="label">Maior entrada</div>
                    <div class="value">R$ ${maxIncomeTx ? Number(maxIncomeTx.amount).toFixed(2) : "0.00"}</div>
                    <div class="helper">${maxIncomeTx ? maxIncomeTx.merchant || maxIncomeTx.description || "-" : "-"}</div>
                </div>
                <div class="kpi-card">
                    <div class="label">Maior saida</div>
                    <div class="value">R$ ${maxExpenseTx ? Math.abs(Number(maxExpenseTx.amount)).toFixed(2) : "0.00"}</div>
                    <div class="helper">${maxExpenseTx ? maxExpenseTx.merchant || maxExpenseTx.description || "-" : "-"}</div>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Tendencia mensal</span>
                <div class="filters">
                    <button
                        class="filter-chip ${trendMode === "absolute" ? "active" : ""}"
                        data-action="set-trend-mode"
                        data-mode="absolute"
                        type="button"
                    >
                        Absoluto
                    </button>
                    <button
                        class="filter-chip ${trendMode === "net" ? "active" : ""}"
                        data-action="set-trend-mode"
                        data-mode="net"
                        type="button"
                    >
                        Net
                    </button>
                </div>
            </div>
            <div class="trend-list">
                ${monthTotals
                    .map(
                        (item) => `
                    <div class="trend-row">
                        <span class="label">${item.label}</span>
                        <div class="trend-bar">
                            <span
                                class="trend-bar-fill ${
                                    trendMode === "net" && item.total < 0 ? "negative" : "positive"
                                }"
                                style="width: ${(Math.abs(
                                    trendMode === "net" ? item.total : Math.abs(item.total)
                                ) / maxMonthValue) * 100}%"
                            ></span>
                        </div>
                        <span class="value">R$ ${item.total.toFixed(2)}</span>
                    </div>
                `
                    )
                    .join("")}
            </div>
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Movimentacao por conta</span>
            </div>
            ${
                spendingRows
                    ? spendingRows
                    : `
                    <div class="empty-state">
                        <p>Nenhuma movimentacao no periodo</p>
                    </div>
                `
            }
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Top estabelecimentos</span>
            </div>
            ${
                topMerchants.length
                    ? `
                    <div class="merchant-list">
                        ${topMerchants
                            .map(
                                ([label, total]) => `
                            <div class="merchant-row">
                                <span class="label">${label}</span>
                                <div class="mini-bar">
                                    <span class="mini-bar-fill" style="width: ${(total / maxMerchantValue) * 100}%"></span>
                                </div>
                                <span class="value">R$ ${total.toFixed(2)}</span>
                            </div>
                        `
                            )
                            .join("")}
                    </div>
                `
                    : `
                    <div class="empty-state">
                        <p>Nenhuma transacao no periodo</p>
                    </div>
                `
            }
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Top categorias</span>
            </div>
            ${
                topCategories.length
                    ? `
                    <div class="category-list">
                        ${topCategories
                            .map(
                                ([categoryId, total]) => `
                            <div class="category-row">
                                <span class="label">${formatCategoryLabel(categoryId)}</span>
                                <div class="mini-bar">
                                    <span class="mini-bar-fill" style="width: ${(total / maxCategoryValue) * 100}%"></span>
                                </div>
                                <span class="value">R$ ${total.toFixed(2)}</span>
                            </div>
                        `
                            )
                            .join("")}
                    </div>
                `
                    : `
                    <div class="empty-state">
                        <p>Nenhuma transacao no periodo</p>
                    </div>
                `
            }
        </div>
        <div class="card">
            <div class="card-header">
                <span class="card-title">Tendencia rapida</span>
            </div>
            ${buildSparkline(filteredTransactions)}
        </div>
    `;
}

export function renderAccounts(accounts) {
    const list = document.getElementById("accounts-list");
    if (!list) return;

    if (accounts.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <p>Nenhuma conta cadastrada</p>
                <p style="font-size: 14px; margin-top: 8px;">
                    Use o formulario acima para criar sua primeira conta
                </p>
            </div>
        `;
        return;
    }

    list.innerHTML = accounts
        .map(
            (acc) => `
            <div class="card account-card" data-account-id="${acc.id}">
                <div class="card-header">
                    <span class="card-title">${acc.bank_name}</span>
                    <span class="badge">${getAccountTypeLabel(acc.account_type)}</span>
                </div>
                <div class="info-row">
                    <span class="label">Apelido</span>
                    <span class="value">${acc.nickname || "-"}</span>
                </div>
                <div class="info-row">
                    <span class="label">Ultimo Saldo</span>
                    <span class="value">${acc.last_balance ? `R$ ${acc.last_balance.toFixed(2)}` : "-"}</span>
                </div>
            </div>
        `
        )
        .join("");
}

export function getAccountTypeLabel(type) {
    const labels = {
        checking: "Conta Corrente",
        savings: "Poupanca",
        credit_card: "Cartao Credito",
        investment: "Investimento",
    };
    return labels[type] || type;
}

export async function showAccountDetail(accountId) {
    clearError();
    try {
        const [account, transactionsData] = await Promise.all([
            requestJson(`/accounts/${accountId}`, {
                headers: { ...getAuthHeaders() },
            }),
            requestJson(`/transactions/?account_id=${accountId}`, {
                headers: { ...getAuthHeaders() },
            }),
        ]);

        const transactions = transactionsData.items || [];
        state.editingAccountId = account.id;

        const detail = document.getElementById("account-detail");
        if (detail) {
            detail.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${account.bank_name}</span>
                        <span class="badge">${getAccountTypeLabel(account.account_type)}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Apelido</span>
                        <span class="value">${account.nickname || "-"}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Ultimo Saldo</span>
                        <span class="value">${account.last_balance ? `R$ ${account.last_balance.toFixed(2)}` : "-"}</span>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Editar Conta</span>
                    </div>
                    <div class="field">
                        <label class="label" for="account-edit-bank-name">Banco</label>
                        <input id="account-edit-bank-name" class="input" type="text" value="${account.bank_name}" />
                    </div>
                    <div class="field">
                        <label class="label" for="account-edit-type">Tipo</label>
                        <select id="account-edit-type" class="select">
                            <option value="checking" ${account.account_type === "checking" ? "selected" : ""}>Conta Corrente</option>
                            <option value="savings" ${account.account_type === "savings" ? "selected" : ""}>Poupanca</option>
                            <option value="credit_card" ${account.account_type === "credit_card" ? "selected" : ""}>Cartao Credito</option>
                            <option value="investment" ${account.account_type === "investment" ? "selected" : ""}>Investimento</option>
                        </select>
                    </div>
                    <div class="field">
                        <label class="label" for="account-edit-nickname">Apelido</label>
                        <input id="account-edit-nickname" class="input" type="text" value="${account.nickname || ""}" />
                    </div>
                    <div class="actions-row">
                        <button class="btn btn-small btn-success" data-action="save-account">Salvar</button>
                        <button class="btn btn-small btn-danger" data-action="delete-account">Excluir</button>
                    </div>
                </div>
            `;
        }

        renderTransactions(transactions, "account-transactions");

        document.querySelectorAll(".section").forEach((section) => section.classList.remove("active"));
        const accountSection = document.getElementById("account-detail-section");
        if (accountSection) {
            accountSection.classList.add("active");
        }
    } catch (error) {
        showError(error.message);
    }
}

export async function createAccount() {
    clearError();
    try {
        const bankName = document.getElementById("bank-name")?.value.trim();
        const accountType = document.getElementById("account-type")?.value;
        const nickname = document.getElementById("nickname")?.value.trim();

        if (!bankName) {
            showError("Informe o nome do banco");
            return;
        }

        await requestJson("/accounts/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
            body: JSON.stringify({
                bank_name: bankName,
                account_type: accountType,
                nickname: nickname || null,
            }),
        });

        const bankInput = document.getElementById("bank-name");
        const nicknameInput = document.getElementById("nickname");
        if (bankInput) bankInput.value = "";
        if (nicknameInput) nicknameInput.value = "";
        setStatus("Conta criada com sucesso.", "success");
        await fetchAccounts();
    } catch (error) {
        showError(error.message);
    }
}

export async function saveAccount() {
    clearError();
    if (!state.editingAccountId) {
        showError("Nenhuma conta selecionada");
        return;
    }

    try {
        const bankName = document.getElementById("account-edit-bank-name")?.value.trim();
        const accountType = document.getElementById("account-edit-type")?.value;
        const nickname = document.getElementById("account-edit-nickname")?.value.trim();

        await requestJson(`/accounts/${state.editingAccountId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
            body: JSON.stringify({
                bank_name: bankName,
                account_type: accountType,
                nickname: nickname || null,
            }),
        });

        setStatus("Conta atualizada.", "success");
        await fetchAccounts();
        await showAccountDetail(state.editingAccountId);
    } catch (error) {
        showError(error.message);
    }
}

export async function deleteAccount() {
    clearError();
    if (!state.editingAccountId) {
        showError("Nenhuma conta selecionada");
        return;
    }

    if (!confirm("Excluir esta conta? Esta acao nao pode ser desfeita.")) {
        return;
    }

    try {
        await requestJson(`/accounts/${state.editingAccountId}`, {
            method: "DELETE",
            headers: { ...getAuthHeaders() },
        });

        setStatus("Conta excluida.", "success");
        state.editingAccountId = null;
        setActiveTab("accounts");
        await fetchAccounts();
    } catch (error) {
        showError(error.message);
    }
}

async function loginWithCredentials(email, password) {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);

    const response = await fetch("/auth/token", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || "Erro ao autenticar");
    }

    const tokenInput = document.getElementById("token-input");
    if (tokenInput) {
        tokenInput.value = data.access_token || "";
    }
    persistToken();
}

async function fetchCurrentUser() {
    const token = getToken();
    if (!token) {
        setCurrentUser("-");
        return false;
    }

    try {
        const data = await requestJson("/auth/me", {
            headers: { ...getAuthHeaders() },
        });
        setCurrentUser(data.email || "-");
        return true;
    } catch (error) {
        setCurrentUser("-");
        return false;
    }
}

export async function login() {
    clearError();
    clearStatus();
    try {
        const email = document.getElementById("login-email")?.value.trim();
        const password = document.getElementById("login-password")?.value;

        if (!email || !password) {
            showError("Informe email e senha");
            return;
        }

        await loginWithCredentials(email, password);
        setStatus("Login realizado com sucesso.", "success");

        const passwordInput = document.getElementById("login-password");
        if (passwordInput) passwordInput.value = "";

        await fetchCurrentUser();
        await fetchAccounts();
        setActiveTab("accounts");
        window.dispatchEvent(new Event("auth:changed"));
    } catch (error) {
        showError(error.message);
    }
}

export async function register() {
    clearError();
    clearStatus();
    try {
        const email = document.getElementById("register-email")?.value.trim();
        const password = document.getElementById("register-password")?.value;

        if (!email || !password) {
            showError("Informe email e senha");
            return;
        }

        await requestJson("/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
        });

        const registerPassword = document.getElementById("register-password");
        if (registerPassword) registerPassword.value = "";

        const loginEmail = document.getElementById("login-email");
        const loginPassword = document.getElementById("login-password");
        if (loginEmail) loginEmail.value = email;
        if (loginPassword) loginPassword.value = password;

        await login();
        setStatus("Usuario criado e autenticado.", "success");
    } catch (error) {
        showError(error.message);
    }
}

export function logout() {
    clearError();
    clearStatus();
    const tokenInput = document.getElementById("token-input");
    if (tokenInput) tokenInput.value = "";
    persistToken();
    setCurrentUser("-");
    setStatus("Token removido.", "info");
    state.accounts = [];
    state.transactions = [];
    state.categories = {};
    updateSyncAccounts([]);
    updateTransactionAccountOptions([]);

    const accountsList = document.getElementById("accounts-list");
    if (accountsList) {
        accountsList.innerHTML = `
            <div class="empty-state">
                <p>Informe o token para carregar contas</p>
            </div>
        `;
    }
    setActiveTab("accounts");
}

export async function checkAuthStatus() {
    const tokenInput = document.getElementById("token-input");
    const savedToken = localStorage.getItem("access_token");
    if (tokenInput && savedToken) {
        tokenInput.value = savedToken;
    }

    if (tokenInput) {
        tokenInput.addEventListener("input", persistToken);
        tokenInput.addEventListener("change", () => {
            persistToken();
            fetchCurrentUser();
        });
    }

    return fetchCurrentUser();
}

export function cancelAccountEdit() {
    setActiveTab("accounts");
}

export function updateSyncAccounts(accounts) {
    const select = document.getElementById("sync-account-id");
    if (!select) return;

    if (!accounts || accounts.length === 0) {
        select.innerHTML = '<option value="">Sem contas</option>';
        return;
    }

    const currentValue = select.value;
    select.innerHTML = accounts
        .map((acc) => {
            const label = acc.nickname ? `${acc.bank_name} (${acc.nickname})` : acc.bank_name;
            return `<option value="${acc.id}">${label}</option>`;
        })
        .join("");

    if (currentValue && accounts.some((acc) => String(acc.id) === String(currentValue))) {
        select.value = currentValue;
    }
}

export function updateTransactionAccountOptions(accounts) {
    const selects = [
        document.getElementById("transaction-account-id"),
        document.getElementById("transactions-filter-account-id"),
    ];

    selects.forEach((select, index) => {
        if (!select) return;

        const currentValue = select.value;
        const options = [
            index === 1 ? '<option value="">Todas</option>' : '<option value="">Selecione</option>',
        ];

        accounts.forEach((acc) => {
            const label = acc.nickname ? `${acc.bank_name} (${acc.nickname})` : acc.bank_name;
            options.push(`<option value="${acc.id}">${label}</option>`);
        });

        select.innerHTML = options.join("");

        if (currentValue && accounts.some((acc) => String(acc.id) === String(currentValue))) {
            select.value = currentValue;
        }
    });
}
