const API_URL = "";

export function getToken() {
    const tokenInput = document.getElementById("token-input");
    return (tokenInput?.value || "").trim();
}

export function getAuthHeaders() {
    const token = getToken();
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
}

export function persistToken() {
    const token = getToken();
    if (token) {
        localStorage.setItem("access_token", token);
    } else {
        localStorage.removeItem("access_token");
    }
}

export async function requestJson(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, options);
    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await response.json().catch(() => null) : null;

    if (!response.ok) {
        const message = data?.detail || data?.message || "Erro na requisicao";
        throw new Error(message);
    }
    return data;
}
