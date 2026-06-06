const forms = {
  studs: document.querySelector("#stud-form"),
  panels: document.querySelector("#panel-form"),
  flooring: document.querySelector("#floor-form"),
  paint: document.querySelector("#paint-form"),
  trim: document.querySelector("#trim-form"),
};

const defaults = new Map();

function rememberDefaults(form) {
  const state = Array.from(form.elements)
    .filter((field) => field.name)
    .map((field) => ({
      name: field.name,
      type: field.type,
      value: field.value,
      checked: field.checked,
    }));
  defaults.set(form.id, state);
}

function resetForm(form) {
  const state = defaults.get(form.id) || [];
  for (const item of state) {
    const field = form.elements.namedItem(item.name);
    if (!field) {
      continue;
    }
    if (item.type === "checkbox") {
      field.checked = item.checked;
    } else {
      field.value = item.value;
    }
  }
}

function serialize(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Calcul impossible.");
  }
  return data;
}

function text(id, value) {
  const node = document.querySelector(id);
  if (node) {
    node.textContent = value;
  }
}

function showError(totalId, costId, message) {
  text(totalId, "-");
  text(costId, message);
}

function showStructureError(message) {
  const container = document.querySelector("#stud-warnings");
  container.hidden = false;
  container.textContent = message;
}

function renderWarnings(containerId, warnings) {
  const container = document.querySelector(containerId);
  if (!container) {
    return;
  }
  container.hidden = !warnings.length;
  container.innerHTML = "";
  for (const warning of warnings) {
    const item = document.createElement("div");
    item.textContent = warning;
    container.append(item);
  }
}

async function calculateStuds() {
  try {
    const result = await postJson("/api/calculate/studs", serialize(forms.studs));
    text("#stud-total", result.totalStuds);
    text("#stud-stock-pieces", result.stockPieces || "-");
    text("#stud-cost", result.totalCostLabel);
    text("#stud-cut-length", result.cutLength);
    text("#studs-per-piece", result.studsPerStockPiece || "-");
    text("#stud-base", result.baseStuds);
    text("#stud-before-waste", result.studsBeforeWaste);
    text("#stud-used-linear", result.usedLinear);
    text("#stud-purchased-linear", result.purchasedLinear);
    text("#stud-waste-linear", result.wasteLinear);
    text("#stud-average-spacing", result.averageSpacing);
    renderWarnings("#stud-warnings", result.warnings || []);
  } catch (error) {
    showStructureError(error.message);
  }
}

async function calculatePanels() {
  try {
    const result = await postJson("/api/calculate/panels", serialize(forms.panels));
    text("#panel-total", result.panels);
    text("#panel-cost", result.totalCostLabel);
    text("#panel-net-area", result.netArea);
    text("#panel-area", result.panelArea);
    text("#panel-raw", result.rawPanels);
    text("#panel-gross-area", result.grossArea);
    text("#panel-purchased-area", result.purchasedArea);
    text("#panel-surplus-area", result.surplusArea);
  } catch (error) {
    showError("#panel-total", "#panel-cost", error.message);
  }
}

async function calculateFlooring() {
  try {
    const result = await postJson("/api/calculate/flooring", serialize(forms.flooring));
    text("#floor-total", result.boxes);
    text("#floor-cost", result.totalCostLabel);
    text("#floor-net-area", result.netArea);
    text("#floor-coverage", result.coverage);
    text("#floor-raw", result.rawBoxes);
    text("#floor-gross-area", result.grossArea);
    text("#floor-purchased-area", result.purchasedArea);
    text("#floor-surplus-area", result.surplusArea);
  } catch (error) {
    showError("#floor-total", "#floor-cost", error.message);
  }
}

async function calculatePaint() {
  try {
    const result = await postJson("/api/calculate/paint", serialize(forms.paint));
    text("#paint-total", result.containers);
    text("#paint-cost", result.totalCostLabel);
    text("#paint-net-area", result.netArea);
    text("#paint-coats", result.coats);
    text("#paint-coverage", result.coverage);
    text("#paint-wall-area", result.wallArea);
    text("#paint-ceiling-area", result.ceilingArea);
    text("#paint-area-with-coats", result.areaWithCoats);
  } catch (error) {
    showError("#paint-total", "#paint-cost", error.message);
  }
}

async function calculateTrim() {
  try {
    const result = await postJson("/api/calculate/trim", serialize(forms.trim));
    text("#trim-total", result.pieces);
    text("#trim-cost", result.totalCostLabel);
    text("#trim-net-length", result.netLength);
    text("#trim-piece-length", result.pieceLength);
    text("#trim-needed-length", result.neededLength);
    text("#trim-perimeter", result.perimeter);
    text("#trim-purchased-length", result.purchasedLength);
    text("#trim-surplus-length", result.surplusLength);
  } catch (error) {
    showError("#trim-total", "#trim-cost", error.message);
  }
}

const calculators = {
  "stud-form": calculateStuds,
  "panel-form": calculatePanels,
  "floor-form": calculateFlooring,
  "paint-form": calculatePaint,
  "trim-form": calculateTrim,
};

function activateTab(id) {
  document.querySelectorAll(".tab-button").forEach((button) => {
    const selected = button.dataset.tab === id;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", String(selected));
  });

  document.querySelectorAll(".tab-panel").forEach((panel) => {
    const selected = panel.id === id;
    panel.classList.toggle("active", selected);
    panel.hidden = !selected;
  });
}

for (const form of Object.values(forms)) {
  rememberDefaults(form);
  const recalculate = calculators[form.id];

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    recalculate();
  });

  form.addEventListener("input", recalculate);
  form.addEventListener("change", recalculate);
}

document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tab));
});

document.querySelectorAll("[data-reset]").forEach((button) => {
  button.addEventListener("click", () => {
    const form = document.querySelector(`#${button.dataset.reset}`);
    resetForm(form);
    calculators[form.id]();
  });
});

document.querySelectorAll("[data-panel-width]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-panel-width]").forEach((preset) => preset.classList.remove("active"));
    button.classList.add("active");
    forms.panels.elements.namedItem("panelWidth").value = button.dataset.panelWidth;
    forms.panels.elements.namedItem("panelHeight").value = button.dataset.panelHeight;
    forms.panels.elements.namedItem("panelWidthUnit").value = "ft";
    forms.panels.elements.namedItem("panelHeightUnit").value = "ft";
    calculatePanels();
  });
});

calculateStuds();
calculatePanels();
calculateFlooring();
calculatePaint();
calculateTrim();
