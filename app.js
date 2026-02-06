const storageKey = "controle-gastos.entries.v1";
const filterKey = "controle-gastos.filters.v1";

const categories = {
  expense: [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Educação",
    "Lazer",
    "Assinaturas",
    "Impostos",
    "Outros",
  ],
  income: ["Salário", "Freelance", "Investimentos", "Vendas", "Outros"],
};

const entryForm = document.getElementById("entry-form");
const descriptionInput = document.getElementById("description");
const amountInput = document.getElementById("amount");
const categorySelect = document.getElementById("category");
const dateInput = document.getElementById("date");
const submitButton = document.getElementById("submit-entry");
const clearFormButton = document.getElementById("clear-form");
const cancelEditButton = document.getElementById("cancel-edit");

const filterMonth = document.getElementById("filter-month");
const filterCategory = document.getElementById("filter-category");
const filterText = document.getElementById("filter-text");
const clearFiltersButton = document.getElementById("clear-filters");
const exportButton = document.getElementById("export-data");
const importInput = document.getElementById("import-data");

const summaryLabel = document.getElementById("summary-label");
const incomeTotal = document.getElementById("income-total");
const expenseTotal = document.getElementById("expense-total");
const balanceTotal = document.getElementById("balance-total");

const entriesBody = document.getElementById("entries-body");
const listMeta = document.getElementById("list-meta");
const emptyState = document.getElementById("empty-state");

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});
const dateFormatter = new Intl.DateTimeFormat("pt-BR");
const monthFormatter = new Intl.DateTimeFormat("pt-BR", {
  month: "long",
  year: "numeric",
});

const state = {
  entries: [],
  filters: {
    month: "",
    category: "",
    text: "",
  },
  editingId: null,
};

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

const toCurrency = (value) => currencyFormatter.format(value);

const parseLocalDate = (value) => {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
};

const createId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const normalizeText = (value) =>
  value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const getEntryType = () =>
  entryForm.querySelector('input[name="type"]:checked').value;

const resetForm = () => {
  entryForm.reset();
  entryForm.querySelector("#type-expense").checked = true;
  updateCategoryOptions();
  dateInput.value = new Date().toISOString().slice(0, 10);
  state.editingId = null;
  submitButton.textContent = "Adicionar lançamento";
  cancelEditButton.classList.add("hidden");
  descriptionInput.focus();
};

const parseAmount = (value) => {
  if (value === null || value === undefined) {
    return NaN;
  }
  const trimmed = String(value).trim();
  if (!trimmed) {
    return NaN;
  }
  let normalized = trimmed.replace(/\s/g, "");
  if (normalized.includes(",")) {
    normalized = normalized.replace(/\./g, "").replace(",", ".");
  }
  return Number(normalized);
};

const readStorage = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    const parsed = JSON.parse(raw);
    return parsed ?? fallback;
  } catch (error) {
    return fallback;
  }
};

const saveStorage = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value));
};

const loadEntries = () => {
  const stored = readStorage(storageKey, []);
  if (Array.isArray(stored)) {
    return stored;
  }
  if (stored && Array.isArray(stored.entries)) {
    return stored.entries;
  }
  return [];
};

const getAmountValue = (value) => {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    return parseAmount(value);
  }
  return NaN;
};

const isValidEntry = (entry) => {
  if (!entry || typeof entry !== "object") return false;
  if (!["expense", "income"].includes(entry.type)) return false;
  if (
    typeof entry.description !== "string" ||
    typeof entry.category !== "string" ||
    typeof entry.date !== "string"
  ) {
    return false;
  }
  const amount = getAmountValue(entry.amount);
  if (Number.isNaN(amount)) return false;
  return true;
};

const normalizeEntry = (entry) => ({
  id: entry.id || createId(),
  type: entry.type,
  description: String(entry.description || "").trim(),
  amount: getAmountValue(entry.amount),
  category: String(entry.category || "").trim(),
  date: entry.date,
  createdAt: entry.createdAt || new Date().toISOString(),
});

const updateCategoryOptions = (selectedCategory) => {
  const type = getEntryType();
  const options = [...categories[type]];
  if (selectedCategory && !options.includes(selectedCategory)) {
    options.unshift(selectedCategory);
  }
  categorySelect.innerHTML = options
    .map((category) => `<option value="${category}">${category}</option>`)
    .join("");

  if (selectedCategory && options.includes(selectedCategory)) {
    categorySelect.value = selectedCategory;
  }
};

const updateFilterOptions = () => {
  const selected = filterCategory.value;
  const allCategories = new Set();
  Object.values(categories).forEach((list) =>
    list.forEach((category) => allCategories.add(category))
  );
  state.entries.forEach((entry) => allCategories.add(entry.category));

  const options = [
    `<option value="">Todas</option>`,
    ...Array.from(allCategories)
      .sort((a, b) => a.localeCompare(b))
      .map((category) => `<option value="${category}">${category}</option>`),
  ];
  filterCategory.innerHTML = options.join("");

  if (selected) {
    filterCategory.value = selected;
  }
};

const applyFilters = (entries) => {
  const textFilter = normalizeText(state.filters.text);
  return entries.filter((entry) => {
    if (state.filters.month && entry.date.slice(0, 7) !== state.filters.month) {
      return false;
    }
    if (state.filters.category && entry.category !== state.filters.category) {
      return false;
    }
    if (textFilter) {
      const haystack = normalizeText(
        `${entry.description} ${entry.category} ${entry.type}`
      );
      if (!haystack.includes(textFilter)) {
        return false;
      }
    }
    return true;
  });
};

const updateSummary = (entries) => {
  const income = entries
    .filter((entry) => entry.type === "income")
    .reduce((sum, entry) => sum + entry.amount, 0);
  const expense = entries
    .filter((entry) => entry.type === "expense")
    .reduce((sum, entry) => sum + entry.amount, 0);
  const balance = income - expense;

  incomeTotal.textContent = toCurrency(income);
  expenseTotal.textContent = toCurrency(expense);
  balanceTotal.textContent = toCurrency(balance);
  balanceTotal.classList.toggle("negative", balance < 0);
};

const updateSummaryLabel = () => {
  const parts = [];
  if (!state.filters.month) {
    parts.push("Todos os lançamentos");
  } else {
    const [year, month] = state.filters.month.split("-");
    const date = new Date(Number(year), Number(month) - 1, 1);
    const label = monthFormatter.format(date);
    parts.push(
      `Mês de ${label.charAt(0).toUpperCase()}${label.slice(1)}`
    );
  }

  if (state.filters.category) {
    parts.push(`Categoria: ${state.filters.category}`);
  }
  if (state.filters.text) {
    parts.push(`Busca: "${state.filters.text}"`);
  }

  summaryLabel.textContent = parts.join(" • ");
};

const renderEntries = (entries) => {
  entriesBody.innerHTML = "";

  if (entries.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");

  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = `table-row ${entry.type}`;
    row.dataset.id = entry.id;
    row.innerHTML = `
      <span data-label="Data">${dateFormatter.format(
        parseLocalDate(entry.date)
      )}</span>
      <span data-label="Descrição">${entry.description}</span>
      <span data-label="Categoria">${entry.category}</span>
      <span data-label="Tipo">${entry.type === "expense" ? "Despesa" : "Receita"}</span>
      <span class="value" data-label="Valor">${toCurrency(entry.amount)}</span>
      <div class="row-actions" data-label="Ações">
        <button class="ghost" data-action="edit">Editar</button>
        <button class="ghost" data-action="delete">Excluir</button>
      </div>
    `;
    entriesBody.appendChild(row);
  });
};

const updateMeta = (filteredCount, totalCount) => {
  if (totalCount === 0) {
    listMeta.textContent = "Nenhum lançamento encontrado.";
    return;
  }
  listMeta.textContent = `Mostrando ${filteredCount} de ${totalCount} lançamentos`;
};

const render = () => {
  updateFilterOptions();
  updateSummaryLabel();
  const sorted = [...state.entries].sort((a, b) => {
    if (a.date === b.date) {
      return new Date(b.createdAt) - new Date(a.createdAt);
    }
    return b.date.localeCompare(a.date);
  });
  const filtered = applyFilters(sorted);
  updateSummary(filtered);
  renderEntries(filtered);
  updateMeta(filtered.length, state.entries.length);
};

const startEdit = (entry) => {
  state.editingId = entry.id;
  entryForm.querySelector(
    `input[name="type"][value="${entry.type}"]`
  ).checked = true;
  updateCategoryOptions(entry.category);
  descriptionInput.value = entry.description;
  amountInput.value = entry.amount.toFixed(2);
  dateInput.value = entry.date;
  submitButton.textContent = "Salvar alterações";
  cancelEditButton.classList.remove("hidden");
  descriptionInput.focus();
};

const upsertEntry = (entry) => {
  const index = state.entries.findIndex((item) => item.id === entry.id);
  if (index >= 0) {
    state.entries[index] = entry;
  } else {
    state.entries.push(entry);
  }
};

const handleSubmit = (event) => {
  event.preventDefault();
  const amount = parseAmount(amountInput.value);

  if (Number.isNaN(amount) || amount <= 0) {
    window.alert("Informe um valor válido.");
    amountInput.focus();
    return;
  }

  const existingEntry = state.entries.find(
    (item) => item.id === state.editingId
  );
  const baseEntry = {
    id: state.editingId || createId(),
    type: getEntryType(),
    description: descriptionInput.value.trim(),
    amount,
    category: categorySelect.value,
    date: dateInput.value,
    createdAt: existingEntry?.createdAt || new Date().toISOString(),
  };

  if (!baseEntry.description || !baseEntry.date) {
    window.alert("Preencha descrição e data.");
    return;
  }

  upsertEntry(baseEntry);
  saveStorage(storageKey, state.entries);
  resetForm();
  render();
};

const handleDelete = (entryId) => {
  const entry = state.entries.find((item) => item.id === entryId);
  if (!entry) {
    return;
  }
  const confirmed = window.confirm(
    `Excluir o lançamento "${entry.description}"?`
  );
  if (!confirmed) {
    return;
  }
  state.entries = state.entries.filter((item) => item.id !== entryId);
  saveStorage(storageKey, state.entries);
  render();
};

const handleImport = async (file) => {
  try {
    const content = await file.text();
    const parsed = JSON.parse(content);
    const entries = Array.isArray(parsed) ? parsed : parsed.entries;
    if (!Array.isArray(entries)) {
      throw new Error("Formato inválido");
    }

    const cleaned = entries
      .filter(isValidEntry)
      .map((entry) => normalizeEntry(entry));

    if (cleaned.length === 0) {
      window.alert("Nenhum lançamento válido encontrado.");
      return;
    }

    const shouldReplace = window.confirm(
      "Deseja substituir seus dados atuais? Ok para substituir, Cancelar para mesclar."
    );

    if (shouldReplace) {
      state.entries = cleaned;
    } else {
      const existing = new Set(state.entries.map((entry) => entry.id));
      cleaned.forEach((entry) => {
        if (!existing.has(entry.id)) {
          state.entries.push(entry);
        }
      });
    }

    saveStorage(storageKey, state.entries);
    render();
  } catch (error) {
    window.alert("Não foi possível importar o arquivo.");
  } finally {
    importInput.value = "";
  }
};

const exportData = () => {
  const payload = {
    version: 1,
    exportedAt: new Date().toISOString(),
    entries: state.entries,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `controle-gastos-${getCurrentMonth()}.json`;
  link.click();
  URL.revokeObjectURL(url);
};

const applyFiltersToState = () => {
  state.filters.month = filterMonth.value;
  state.filters.category = filterCategory.value;
  state.filters.text = filterText.value.trim();
  saveStorage(filterKey, state.filters);
  render();
};

const restoreFilters = () => {
  const stored = readStorage(filterKey, null);
  if (stored) {
    state.filters = {
      month: stored.month || "",
      category: stored.category || "",
      text: stored.text || "",
    };
  } else {
    state.filters.month = getCurrentMonth();
  }
  filterMonth.value = state.filters.month;
  filterCategory.value = state.filters.category;
  filterText.value = state.filters.text;
};

const init = () => {
  state.entries = loadEntries();
  resetForm();
  restoreFilters();
  render();
};

entryForm.addEventListener("submit", handleSubmit);
clearFormButton.addEventListener("click", resetForm);
cancelEditButton.addEventListener("click", resetForm);

entryForm.addEventListener("change", (event) => {
  if (event.target.name === "type") {
    updateCategoryOptions();
  }
});

entriesBody.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const row = event.target.closest(".table-row");
  if (!row) return;
  const entryId = row.dataset.id;
  const entry = state.entries.find((item) => item.id === entryId);
  if (!entry) return;

  if (button.dataset.action === "edit") {
    startEdit(entry);
  }
  if (button.dataset.action === "delete") {
    handleDelete(entryId);
  }
});

filterMonth.addEventListener("change", applyFiltersToState);
filterCategory.addEventListener("change", applyFiltersToState);
filterText.addEventListener("input", applyFiltersToState);

clearFiltersButton.addEventListener("click", () => {
  filterMonth.value = "";
  filterCategory.value = "";
  filterText.value = "";
  applyFiltersToState();
});

exportButton.addEventListener("click", exportData);
importInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) {
    handleImport(file);
  }
});

init();
