import { getAuthHeaders, requestJson } from "./api.js";
import { state } from "./state.js";
import { escapeHtml, showError } from "./ui.js";

export function updateCategoryFilters() {
    const select = document.getElementById("transactions-filter-category-id");
    const formSelect = document.getElementById("transaction-category-id");
    if (!select) return;

    const categories = Object.values(state.categories || {});
    const currentValue = select.value;
    const currentFormValue = formSelect?.value;
    const options = ['<option value="">Todas</option>'];
    const formOptions = ['<option value="">Sem categoria</option>'];

    categories
        .sort((a, b) => (a.name || "").localeCompare(b.name || ""))
        .forEach((category) => {
            const option = `<option value="${category.id}">${escapeHtml(category.name)}</option>`;
            options.push(option);
            formOptions.push(option);
        });

    select.innerHTML = options.join("");
    if (currentValue && categories.some((category) => String(category.id) === String(currentValue))) {
        select.value = currentValue;
    }

    if (formSelect) {
        formSelect.innerHTML = formOptions.join("");
        if (
            currentFormValue &&
            categories.some((category) => String(category.id) === String(currentFormValue))
        ) {
            formSelect.value = currentFormValue;
        }
    }
}

export async function fetchCategories() {
    try {
        const data = await requestJson("/categories/?skip=0&limit=200", {
            headers: { ...getAuthHeaders() },
        });
        const categories = data.items || [];
        const lookup = {};
        categories.forEach((category) => {
            lookup[category.id] = category;
        });
        state.categories = lookup;
        updateCategoryFilters();
        return lookup;
    } catch (error) {
        showError(error.message);
        return {};
    }
}

export async function createCategory({ name, parentId }) {
    if (!name) {
        showError("Informe o nome da categoria");
        return null;
    }

    try {
        const payload = {
            name: name.trim(),
            parent_id: parentId ? Number(parentId) : null,
        };

        const category = await requestJson("/categories/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders(),
            },
            body: JSON.stringify(payload),
        });

        await fetchCategories();
        return category;
    } catch (error) {
        showError(error.message);
        return null;
    }
}
