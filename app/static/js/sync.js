import { getAuthHeaders, requestJson } from "./api.js";
import { clearError, showError, setStatus } from "./ui.js";

export async function syncGmail() {
    clearError();
    const resultContainer = document.getElementById("sync-result");
    if (resultContainer) {
        resultContainer.innerHTML = '<div class="loading">Sincronizando...</div>';
    }

    try {
        const accountId = document.getElementById("sync-account-id")?.value;
        if (!accountId) {
            showError("Selecione uma conta para sincronizar");
            if (resultContainer) resultContainer.innerHTML = "";
            return;
        }

        const data = await requestJson(`/gmail/sync?account_id=${accountId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
        });

        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="card" style="background: #e8f5e9; border: 1px solid #4caf50;">
                    <div class="info-row">
                        <span class="label">Emails Encontrados</span>
                        <span class="value">${data.messages_found ?? 0}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Emails Parseados</span>
                        <span class="value">${data.messages_parsed ?? 0}</span>
                    </div>
                    <div class="info-row" style="border-bottom: none;">
                        <span class="label">Transacoes Criadas</span>
                        <span class="value" style="color: #1b5e20; font-weight: 700;">${
                            data.transactions_created ?? 0
                        }</span>
                    </div>
                </div>
            `;
        }
        setStatus("Sincronizacao concluida.", "success");
    } catch (error) {
        if (resultContainer) {
            resultContainer.innerHTML = `<div class="error">❌ ${error.message}</div>`;
        }
        showError(error.message);
    }
}

export async function startGmailAuth() {
    clearError();
    try {
        const data = await requestJson("/gmail/auth/init", {
            method: "POST",
            headers: { ...getAuthHeaders() },
        });

        if (!data?.auth_url) {
            showError("Nao foi possivel iniciar o OAuth do Gmail");
            return;
        }

        window.location.href = data.auth_url;
    } catch (error) {
        showError(error.message);
    }
}
