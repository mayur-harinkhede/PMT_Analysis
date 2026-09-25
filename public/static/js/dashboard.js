// ==========================================================================
// PMT Analysis — Plant Maintenance & Equipment Analytics Dashboard
// Live Controller, Cascading Hierarchical Filters, Visuals & Compact Grid
// ==========================================================================

let allTickets = [];
let filteredTickets = [];

// 4-Level Cascading Hierarchy & Filter States
let currentKitchen = "All Kitchens";
let currentZone = "All Zones";
let currentArea = "All Areas";
let currentEquipment = "All Equipment";
let currentTimeFilter = "All Time";
let currentPriority = "All Priorities";
let currentStatus = "All Statuses";
let currentCategory = "All Categories";
let currentSearch = "";

// View State (all, charts, data)
let currentMainView = "all";

// Table Sorting & Pagination
let currentSortColumn = "ticket_no";
let sortAscending = false; // newest first by default
let currentPage = 1;
let pageSize = 50;

// ==========================================================================
// Equipment Resolver Helper (Categorizes custom & unregistered equipment)
// ==========================================================================
function resolveEquipment(t) {
  if (!t) return "General Facility";
  let eq = (t.equipment_name || "").trim();
  if (eq && eq !== "—" && eq !== "nan" && eq !== "None" && eq !== "Unregistered Asset" && eq !== "Unregistered" && eq !== "null") {
    return eq;
  }
  let custom = (t.custom_equipment || "").trim();
  if (custom && custom !== "—" && custom !== "nan" && custom !== "None" && custom !== "Unregistered Asset" && custom !== "Unregistered" && custom !== "null") {
    return custom;
  }
  const title = (t.title || "").toLowerCase();
  if (title.includes("rice washing")) return "RICE WASHING MACHINE";
  if (title.includes("rice steamer") || title.includes("steamer")) {
    const m = title.match(/steamer\s*(?:no\.?|#)?\s*(\d+)/i);
    return m ? `RICE STEAMER ${m[1]}` : "RICE STEAMER";
  }
  if (title.includes("conveyor")) {
    if (title.includes("chain")) return "CHAIN CONVEYOR";
    return "RICE / DAL CONVEYOR";
  }
  if (title.includes("blower") || title.includes("mbr") || title.includes("settling tank") || title.includes("collection tank")) return "ETP PLANT / BLOWER";
  if (title.includes("grind") || title.includes("grinder")) return "WET GRINDER";
  if (title.includes("cauldron")) {
    const m = title.match(/(\d+)(?:st|nd|rd|th)?\s*cauldron/i);
    return m ? `CAULDRON ${m[1]}` : "CAULDRON";
  }
  if (title.includes("flame") || title.includes("burner")) return "BURNER / STOVE FLAME";
  if (title.includes("lift")) return "LIFT / ELEVATOR";
  if (title.includes("exhaust") || title.includes("exaust")) return "EXHAUST FAN";
  if (title.includes("tube light") || title.includes("light") || title.includes("lighting")) return "LIGHTING / ELECTRICAL";
  if (title.includes("water leak") || title.includes("tap") || title.includes("pipe") || title.includes("ro water") || title.includes("jet gun")) return "PLUMBING & PIPELINE";
  if (title.includes("strip curtain")) return "STRIP CURTAINS";
  if (title.includes("solar")) return "SOLAR INVERTER & PANEL";
  if (title.includes("shed") || title.includes("rain water")) return "CIVIL & SHED STRUCTURE";
  if (title.includes("mcb") || title.includes("charging")) return "ELECTRICAL INFRASTRUCTURE";
  if (title.includes("safety guard") || title.includes("l angle")) return "SAFETY GUARDS & FIXTURES";
  
  if (t.title && t.title.trim().length > 3) {
    const cleanT = t.title.trim().replace(/\n/g, ' ');
    return cleanT.length <= 25 ? cleanT : cleanT.slice(0, 22) + "...";
  }
  return (t.area_name && t.area_name !== "—") ? t.area_name : "General Facility";
}

// ==========================================================================
// Master Column Definitions & Layout Schema (20 Columns)
// ==========================================================================
const DEFAULT_COLUMN_DEFS = [
  { id: "col-index", label: "#", width: "38px", align: "center", sortable: false },
  { id: "col-ticket_no", label: "Ticket #", width: "125px", sortKey: "ticket_no" },
  { id: "col-kitchen_name", label: "Kitchen", width: "95px", sortKey: "kitchen_name" },
  { id: "col-zone_name", label: "Zone", width: "85px", sortKey: "zone_name" },
  { id: "col-area_name", label: "Area / Section", width: "125px", sortKey: "area_name" },
  { id: "col-equipment_name", label: "Machine / Asset", width: "145px", sortKey: "equipment_name" },
  { id: "col-title", label: "Issue Description", minWidth: "190px", sortKey: "title" },
  { id: "col-status", label: "Status", width: "90px", sortKey: "status" },
  { id: "col-priority", label: "Priority", width: "80px", sortKey: "priority" },
  { id: "col-raised_time", label: "Raised Time", width: "120px", sortKey: "ticket_raised_time" },
  { id: "col-assigned_time", label: "Assign Time", width: "120px", sortKey: "assigned_time" },
  { id: "col-start_delay", label: "Start Delay", width: "85px", sortKey: "response_delay_dhm" },
  { id: "col-start_time", label: "Start Time", width: "120px", sortKey: "repair_start_time" },
  { id: "col-mttr", label: "Time to Fix (MTTR)", width: "95px", sortKey: "mttr_dhm" },
  { id: "col-completed_time", label: "Completed Time", width: "120px", sortKey: "ticket_completion_time" },
  { id: "col-action_taken", label: "Action Taken", minWidth: "170px", sortKey: "action_taken" },
  { id: "col-assigned_to", label: "Assigned Tech", width: "135px", sortKey: "assigned_to" },
  { id: "col-raised_by", label: "Raised By", width: "135px", sortKey: "raised_by" },
  { id: "col-dual_signed", label: "Dual Signed", width: "95px", align: "center", sortable: false },
  { id: "col-action", label: "Action", width: "45px", align: "center", sortable: false }
];

const DEFAULT_COLUMN_ORDER = DEFAULT_COLUMN_DEFS.map(c => c.id);

let columnOrder = [...DEFAULT_COLUMN_ORDER];
let hiddenColumns = [];
let draggedColId = null;

// Chart Instances
let chartTopMachinesInstance = null;
let chartStatusInstance = null;
let chartTechsInstance = null;
let chartHotspotsInstance = null;
let chartCategoryBreakdownInstance = null;
let chartMttrPriorityInstance = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  loadColumnOrderState();
  loadHiddenColumnsState();
  initColumnManager();
  renderTableHeader();
  loadDashboardData();
  
  // Close modals or popover on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeTicketModal();
      closeImageLightbox();
      closeColumnMenu();
    }
  });

  // Close column popover on outside click
  document.addEventListener("click", (e) => {
    const popover = document.getElementById("columnManagerPopover");
    const toggleBtn = document.getElementById("btnColumnToggle");
    if (popover && popover.classList.contains("open")) {
      if (!popover.contains(e.target) && !toggleBtn.contains(e.target)) {
        popover.classList.remove("open");
      }
    }
  });
});

// ==========================================================================
// 1. COLUMN POSITION & VISIBILITY MANAGER (Reorder, Hide, Persist & Reset)
// ==========================================================================
function loadColumnOrderState() {
  try {
    const saved = localStorage.getItem("pmt_column_order");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) {
        const validSaved = parsed.filter(id => DEFAULT_COLUMN_ORDER.includes(id));
        DEFAULT_COLUMN_ORDER.forEach(id => {
          if (!validSaved.includes(id)) validSaved.push(id);
        });
        columnOrder = validSaved;
        return;
      }
    }
  } catch (e) {}
  columnOrder = [...DEFAULT_COLUMN_ORDER];
}

function saveColumnOrderState() {
  try {
    localStorage.setItem("pmt_column_order", JSON.stringify(columnOrder));
  } catch (e) {}
}

function loadHiddenColumnsState() {
  try {
    const saved = localStorage.getItem("pmt_hidden_columns");
    hiddenColumns = saved ? JSON.parse(saved) : [];
  } catch (e) {
    hiddenColumns = [];
  }
}

function saveHiddenColumnsState() {
  try {
    localStorage.setItem("pmt_hidden_columns", JSON.stringify(hiddenColumns));
  } catch (e) {}
}

function initColumnManager() {
  const container = document.getElementById("columnCheckboxList");
  if (!container) return;

  const defMap = {};
  DEFAULT_COLUMN_DEFS.forEach(c => { defMap[c.id] = c; });

  container.innerHTML = columnOrder.map((colId, idx) => {
    const col = defMap[colId] || { id: colId, label: colId };
    const isChecked = !hiddenColumns.includes(colId);
    const isFirst = idx === 0;
    const isLast = idx === columnOrder.length - 1;

    return `
      <div class="column-checkbox-item" data-col-id="${colId}">
        <label class="column-item-main">
          <span class="column-order-badge">${idx + 1}</span>
          <input type="checkbox" data-col="${colId}" ${isChecked ? 'checked' : ''} onchange="toggleColumn('${colId}', this.checked)">
          <span>${col.label}</span>
        </label>
        <div class="column-item-actions">
          <button class="btn-col-move" onclick="moveColumn('${colId}', -1)" ${isFirst ? 'disabled' : ''} title="Move left/up">▲</button>
          <button class="btn-col-move" onclick="moveColumn('${colId}', 1)" ${isLast ? 'disabled' : ''} title="Move right/down">▼</button>
        </div>
      </div>
    `;
  }).join("");

  updateColumnCounter();
}

function toggleColumnMenu(event) {
  if (event) event.stopPropagation();
  const popover = document.getElementById("columnManagerPopover");
  if (popover) popover.classList.toggle("open");
}

function closeColumnMenu() {
  const popover = document.getElementById("columnManagerPopover");
  if (popover) popover.classList.remove("open");
}

function hideColumn(colId) {
  if (!hiddenColumns.includes(colId)) {
    hiddenColumns.push(colId);
    saveHiddenColumnsState();
    
    const chk = document.querySelector(`input[data-col="${colId}"]`);
    if (chk) chk.checked = false;

    updateColumnCounter();
    applyColumnVisibility();
  }
}

function toggleColumn(colId, isVisible) {
  if (isVisible) {
    hiddenColumns = hiddenColumns.filter(id => id !== colId);
  } else {
    if (!hiddenColumns.includes(colId)) hiddenColumns.push(colId);
  }
  saveHiddenColumnsState();
  updateColumnCounter();
  applyColumnVisibility();
}

function moveColumn(colId, direction) {
  const index = columnOrder.indexOf(colId);
  if (index === -1) return;
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= columnOrder.length) return;

  const [moved] = columnOrder.splice(index, 1);
  columnOrder.splice(targetIndex, 0, moved);

  saveColumnOrderState();
  initColumnManager();
  renderTableHeader();
  renderTable();
  applyColumnVisibility();
}

function resetColumns() {
  hiddenColumns = [];
  columnOrder = [...DEFAULT_COLUMN_ORDER];
  try {
    localStorage.removeItem("pmt_hidden_columns");
    localStorage.removeItem("pmt_column_order");
  } catch (e) {}

  initColumnManager();
  renderTableHeader();
  renderTable();
  applyColumnVisibility();
}

function updateColumnCounter() {
  const counterEl = document.getElementById("visibleColumnCounter");
  if (counterEl) {
    const visibleCount = DEFAULT_COLUMN_DEFS.length - hiddenColumns.length;
    counterEl.textContent = `${visibleCount}`;
  }
}

function applyColumnVisibility() {
  DEFAULT_COLUMN_DEFS.forEach(col => {
    const isHidden = hiddenColumns.includes(col.id);
    const elements = document.querySelectorAll(`.${col.id}`);
    elements.forEach(el => {
      if (isHidden) {
        el.classList.add("col-hidden");
      } else {
        el.classList.remove("col-hidden");
      }
    });
  });
}

// ==========================================================================
// 2. DYNAMIC TABLE HEADER RENDERING & DRAG-AND-DROP REORDERING
// ==========================================================================
function renderTableHeader() {
  const theadRow = document.getElementById("ticketsTheadRow");
  if (!theadRow) return;

  const defMap = {};
  DEFAULT_COLUMN_DEFS.forEach(c => { defMap[c.id] = c; });

  theadRow.innerHTML = columnOrder.map(colId => {
    const col = defMap[colId] || { id: colId, label: colId };
    const isSortable = col.sortable !== false && col.sortKey;
    const sortIndicator = isSortable 
      ? (currentSortColumn === col.sortKey ? (sortAscending ? " ▲" : " ▼") : " ⬍") 
      : "";

    const styleStr = [
      col.width ? `width: ${col.width};` : '',
      col.minWidth ? `min-width: ${col.minWidth};` : '',
      col.align ? `text-align: ${col.align};` : ''
    ].filter(Boolean).join(" ");

    const clickAttr = isSortable ? `onclick="sortTable('${col.sortKey}')"` : '';

    return `
      <th class="${col.id}" 
          style="${styleStr}" 
          draggable="true" 
          ondragstart="handleColDragStart(event, '${col.id}')"
          ondragover="handleColDragOver(event, '${col.id}')"
          ondragleave="handleColDragLeave(event)"
          ondrop="handleColDrop(event, '${col.id}')"
          ondragend="handleColDragEnd(event)"
          ${clickAttr}
          title="${isSortable ? 'Click to sort. ' : ''}Drag header left/right to reorder.">
        <div class="col-header-inner" style="${col.align === 'center' ? 'justify-content: center; padding-right: 0;' : ''}">
          <span class="col-drag-indicator">⋮⋮</span>
          <span>${col.label}${sortIndicator}</span>
        </div>
        <button class="col-hide-btn" onclick="event.stopPropagation(); hideColumn('${col.id}')" title="Hide ${col.label}">✕</button>
      </th>
    `;
  }).join("");

  applyColumnVisibility();
}

function handleColDragStart(e, colId) {
  draggedColId = colId;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", colId);
  const th = e.target.closest("th");
  if (th) th.classList.add("col-dragging");
}

function handleColDragOver(e, targetColId) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  if (!draggedColId || draggedColId === targetColId) return;

  const targetTh = e.target.closest("th");
  if (!targetTh) return;

  const rect = targetTh.getBoundingClientRect();
  const relX = e.clientX - rect.left;
  if (relX < rect.width / 2) {
    targetTh.classList.add("drag-over-left");
    targetTh.classList.remove("drag-over-right");
  } else {
    targetTh.classList.add("drag-over-right");
    targetTh.classList.remove("drag-over-left");
  }
}

function handleColDragLeave(e) {
  const targetTh = e.target.closest("th");
  if (targetTh) {
    targetTh.classList.remove("drag-over-left", "drag-over-right");
  }
}

function handleColDrop(e, targetColId) {
  e.preventDefault();
  if (!draggedColId || draggedColId === targetColId) return;

  const fromIndex = columnOrder.indexOf(draggedColId);
  let toIndex = columnOrder.indexOf(targetColId);
  if (fromIndex === -1 || toIndex === -1) return;

  const targetTh = e.target.closest("th");
  if (targetTh) {
    const rect = targetTh.getBoundingClientRect();
    const relX = e.clientX - rect.left;
    if (relX >= rect.width / 2) {
      toIndex = toIndex + 1;
    }
  }
  if (fromIndex < toIndex) {
    toIndex = toIndex - 1;
  }

  const [moved] = columnOrder.splice(fromIndex, 1);
  columnOrder.splice(toIndex, 0, moved);

  saveColumnOrderState();
  initColumnManager();
  renderTableHeader();
  renderTable();
  applyColumnVisibility();
}

function handleColDragEnd(e) {
  document.querySelectorAll(".excel-table thead th").forEach(th => {
    th.classList.remove("col-dragging", "drag-over-left", "drag-over-right");
  });
  draggedColId = null;
}

// ==========================================================================
// 3. DATA FETCHING FROM FLASK API
// ==========================================================================
async function loadDashboardData() {
  const refreshBtn = document.getElementById("btnRefresh");
  if (refreshBtn) {
    refreshBtn.innerHTML = `<svg class="animate-spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Syncing...`;
    refreshBtn.disabled = true;
  }

  try {
    const res = await fetch("/api/data");
    const data = await res.json();

    if (data.error) {
      console.error("API Error:", data.error);
      alert("Error loading live data: " + data.error);
      return;
    }

    allTickets = data.tickets || [];

    // Populate Kitchens dropdown with all 4 kitchens + dynamic
    const defaultKitchens = ["All Kitchens", "Kandi", "Narsingi", "Nellore", "Testing Kitchen"];
    const apiKitchens = data.kitchens || [];
    const combinedKitchens = [...defaultKitchens];
    apiKitchens.forEach(k => {
      if (k && !combinedKitchens.includes(k)) combinedKitchens.push(k);
    });
    populateFilterDropdown("filterKitchen", combinedKitchens);

    // Categories
    populateFilterDropdown("filterCategory", data.categories || ["All Categories"]);

    // Update 4-level cascading hierarchy starting from top
    updateCascadeDropdowns("kitchen");

    // Update Live Sync Badge
    const badge = document.getElementById("liveSyncBadge");
    if (badge) {
      badge.textContent = `🟢 Live Sync (${allTickets.length} Tickets)`;
    }

    // Apply Filters & Render Everything
    applyFilters();

  } catch (err) {
    console.error("Failed to fetch dashboard data:", err);
  } finally {
    if (refreshBtn) {
      refreshBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Refresh Data`;
      refreshBtn.disabled = false;
    }
  }
}

function populateFilterDropdown(elementId, items) {
  const sel = document.getElementById(elementId);
  if (!sel) return;
  const currentVal = sel.value;
  sel.innerHTML = "";

  items.forEach(item => {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    if (item === currentVal) opt.selected = true;
    sel.appendChild(opt);
  });
}

// ==========================================================================
// 4. 4-LEVEL CASCADING HIERARCHICAL DROPDOWN LOGIC
// (Kitchen -> Zone -> Area -> Equipment)
// ==========================================================================
function updateCascadeDropdowns(changedLevel) {
  const kSel = document.getElementById("filterKitchen");
  const zSel = document.getElementById("filterZone");
  const aSel = document.getElementById("filterArea");
  const eqSel = document.getElementById("filterEquipment");

  const selectedKitchen = kSel ? kSel.value : "All Kitchens";

  // Filter pool based on selected Kitchen
  let kitchenTickets = allTickets;
  if (selectedKitchen && selectedKitchen !== "All Kitchens") {
    kitchenTickets = allTickets.filter(t => {
      const k = String(t.kitchen_name || "").trim();
      const z = String(t.zone_name || "").trim();
      if (selectedKitchen === "Nellore") {
        return k === "Nellore" || z === "Nellore";
      } else if (selectedKitchen === "Narsingi") {
        return k === "Narsingi" || z === "Narsingi";
      } else if (selectedKitchen === "Kandi") {
        return k === "Kandi" && z !== "Nellore";
      }
      return k === selectedKitchen.trim();
    });
  }

  // 1. UPDATE ZONES (Level 2)
  if (changedLevel === "kitchen") {
    const zoneSet = new Set();
    kitchenTickets.forEach(t => {
      const z = String(t.zone_name || "").trim();
      if (z && z !== "—" && z !== "nan" && z !== "None" && z !== "null") {
        if (selectedKitchen === "Kandi" && z === "Nellore") return; // exclude Nellore from Kandi zones
        zoneSet.add(z);
      }
    });

    // If Kandi selected, ensure Zone 01, Zone 02, Zone 03 are present
    if (selectedKitchen === "Kandi") {
      ["Zone 01", "Zone 02", "Zone 03"].forEach(z => zoneSet.add(z));
    }

    const sortedZones = Array.from(zoneSet).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const zoneOptions = ["All Zones", ...sortedZones];
    const prevZone = zSel ? zSel.value : "All Zones";
    
    if (zSel) {
      zSel.innerHTML = zoneOptions.map(z => `<option value="${escapeHtml(z)}">${escapeHtml(z)}</option>`).join("");
      if (zoneOptions.includes(prevZone)) {
        zSel.value = prevZone;
        currentZone = prevZone;
      } else {
        zSel.value = "All Zones";
        currentZone = "All Zones";
      }
    }
  }

  const selectedZone = zSel ? zSel.value : "All Zones";

  // Filter pool based on Kitchen + Zone
  let zoneTickets = kitchenTickets;
  if (selectedZone && selectedZone !== "All Zones") {
    zoneTickets = kitchenTickets.filter(t => String(t.zone_name).trim() === selectedZone.trim());
  }

  // 2. UPDATE AREAS (Level 3)
  if (changedLevel === "kitchen" || changedLevel === "zone") {
    const areaSet = new Set();
    zoneTickets.forEach(t => {
      const a = String(t.area_name || "").trim();
      if (a && a !== "—" && a !== "nan" && a !== "None" && a !== "null") {
        areaSet.add(a);
      }
    });
    const sortedAreas = Array.from(areaSet).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const areaOptions = ["All Areas", ...sortedAreas];
    const prevArea = aSel ? aSel.value : "All Areas";

    if (aSel) {
      aSel.innerHTML = areaOptions.map(a => `<option value="${escapeHtml(a)}">${escapeHtml(a)}</option>`).join("");
      if (areaOptions.includes(prevArea)) {
        aSel.value = prevArea;
        currentArea = prevArea;
      } else {
        aSel.value = "All Areas";
        currentArea = "All Areas";
      }
    }
  }

  const selectedArea = aSel ? aSel.value : "All Areas";

  // Filter pool based on Kitchen + Zone + Area
  let areaTickets = zoneTickets;
  if (selectedArea && selectedArea !== "All Areas") {
    areaTickets = zoneTickets.filter(t => String(t.area_name).trim() === selectedArea.trim());
  }

  // 3. UPDATE EQUIPMENT (Level 4 - Resolving custom/unregistered assets cleanly)
  if (changedLevel === "kitchen" || changedLevel === "zone" || changedLevel === "area") {
    const eqSet = new Set();
    areaTickets.forEach(t => {
      const eq = resolveEquipment(t);
      if (eq && eq !== "—" && eq !== "nan" && eq !== "None" && eq !== "null") {
        eqSet.add(eq);
      }
    });
    const sortedEq = Array.from(eqSet).sort();
    const eqOptions = ["All Equipment", ...sortedEq];
    const prevEq = eqSel ? eqSel.value : "All Equipment";

    if (eqSel) {
      eqSel.innerHTML = eqOptions.map(e => `<option value="${escapeHtml(e)}">${escapeHtml(e)}</option>`).join("");
      if (eqOptions.includes(prevEq)) {
        eqSel.value = prevEq;
        currentEquipment = prevEq;
      } else {
        eqSel.value = "All Equipment";
        currentEquipment = "All Equipment";
      }
    }
  }
}

// ==========================================================================
// 5. VIEW SWITCHER (Differentiate Charts vs. Data vs. All)
// ==========================================================================
function switchMainView(viewName) {
  currentMainView = viewName;

  const tabAll = document.getElementById("tabBtnAll");
  const tabCharts = document.getElementById("tabBtnCharts");
  const tabData = document.getElementById("tabBtnData");
  const secCharts = document.getElementById("sectionCharts");
  const secData = document.getElementById("sectionData");
  const extCharts = document.getElementById("extendedChartsRow");
  const caption = document.getElementById("viewSwitchCaption");

  [tabAll, tabCharts, tabData].forEach(btn => {
    if (btn) btn.classList.remove("active");
  });

  if (viewName === "all") {
    if (tabAll) tabAll.classList.add("active");
    if (secCharts) secCharts.style.display = "block";
    if (extCharts) extCharts.style.display = "none";
    if (secData) secData.style.display = "block";
    if (caption) caption.textContent = "Showing complete operational intelligence & breakdown register";
  } else if (viewName === "charts") {
    if (tabCharts) tabCharts.classList.add("active");
    if (secCharts) secCharts.style.display = "block";
    if (extCharts) extCharts.style.display = "grid";
    if (secData) secData.style.display = "none";
    if (caption) caption.textContent = "Focusing exclusively on complete visual equipment failure analytics & team metrics";
  } else if (viewName === "data") {
    if (tabData) tabData.classList.add("active");
    if (secCharts) secCharts.style.display = "none";
    if (extCharts) extCharts.style.display = "none";
    if (secData) secData.style.display = "block";
    if (caption) caption.textContent = "Focusing exclusively on high-density spreadsheet breakdown register & audit records";
  }

  // Trigger Chart.js resize
  if (viewName === "all" || viewName === "charts") {
    setTimeout(() => {
      if (chartTopMachinesInstance) chartTopMachinesInstance.resize();
      if (chartStatusInstance) chartStatusInstance.resize();
      if (chartTechsInstance) chartTechsInstance.resize();
      if (chartHotspotsInstance) chartHotspotsInstance.resize();
      if (chartCategoryBreakdownInstance) chartCategoryBreakdownInstance.resize();
      if (chartMttrPriorityInstance) chartMttrPriorityInstance.resize();
    }, 60);
  }
}

// ==========================================================================
// 6. FILTERING LOGIC & CASCADE
// ==========================================================================
function handleFilterChange(changedType) {
  const kSel = document.getElementById("filterKitchen");
  const zSel = document.getElementById("filterZone");
  const aSel = document.getElementById("filterArea");
  const eqSel = document.getElementById("filterEquipment");
  const tSel = document.getElementById("filterTime");
  const pSel = document.getElementById("filterPriority");
  const sSel = document.getElementById("filterStatus");
  const cSel = document.getElementById("filterCategory");
  const searchInput = document.getElementById("filterSearch");

  if (changedType === "kitchen") {
    currentKitchen = kSel ? kSel.value : "All Kitchens";
    updateCascadeDropdowns("kitchen");
  } else if (changedType === "zone") {
    currentZone = zSel ? zSel.value : "All Zones";
    updateCascadeDropdowns("zone");
  } else if (changedType === "area") {
    currentArea = aSel ? aSel.value : "All Areas";
    updateCascadeDropdowns("area");
  } else if (changedType === "equipment") {
    currentEquipment = eqSel ? eqSel.value : "All Equipment";
  }

  currentKitchen = kSel ? kSel.value : "All Kitchens";
  currentZone = zSel ? zSel.value : "All Zones";
  currentArea = aSel ? aSel.value : "All Areas";
  currentEquipment = eqSel ? eqSel.value : "All Equipment";
  currentTimeFilter = tSel ? tSel.value : "All Time";
  currentPriority = pSel ? pSel.value : "All Priorities";
  currentStatus = sSel ? sSel.value : "All Statuses";
  currentCategory = cSel ? cSel.value : "All Categories";
  currentSearch = searchInput ? searchInput.value.trim().toLowerCase() : "";

  // Reset pagination to first page
  currentPage = 1;
  applyFilters();
}

function filterByKpi(kpiType) {
  const sSel = document.getElementById("filterStatus");
  if (!sSel) return;

  if (kpiType === "ALL") {
    sSel.value = "All Statuses";
  } else if (kpiType === "PENDING") {
    sSel.value = "PENDING";
  } else if (kpiType === "COMPLETED") {
    sSel.value = "COMPLETED";
  } else if (kpiType === "VERIFIED") {
    sSel.value = "VERIFIED";
  }

  currentStatus = sSel.value;
  currentPage = 1;
  applyFilters();
}

// Resets ONLY filters (does not reset custom column orders or hidden columns)
function resetOnlyFilters() {
  const kSel = document.getElementById("filterKitchen");
  const zSel = document.getElementById("filterZone");
  const aSel = document.getElementById("filterArea");
  const eqSel = document.getElementById("filterEquipment");
  const tSel = document.getElementById("filterTime");
  const pSel = document.getElementById("filterPriority");
  const sSel = document.getElementById("filterStatus");
  const cSel = document.getElementById("filterCategory");
  const searchInput = document.getElementById("filterSearch");

  if (kSel) kSel.value = "All Kitchens";
  if (tSel) tSel.value = "All Time";
  if (pSel) pSel.value = "All Priorities";
  if (sSel) sSel.value = "All Statuses";
  if (cSel) cSel.value = "All Categories";
  if (searchInput) searchInput.value = "";

  currentKitchen = "All Kitchens";
  currentZone = "All Zones";
  currentArea = "All Areas";
  currentEquipment = "All Equipment";
  currentTimeFilter = "All Time";
  currentPriority = "All Priorities";
  currentStatus = "All Statuses";
  currentCategory = "All Categories";
  currentSearch = "";

  // Restore all dropdown options cleanly
  updateCascadeDropdowns("kitchen");

  if (zSel) zSel.value = "All Zones";
  if (aSel) aSel.value = "All Areas";
  if (eqSel) eqSel.value = "All Equipment";

  currentPage = 1;
  applyFilters();
}

// Master filter application
function applyFilters() {
  let list = allTickets;

  // 1. Kitchen Filter
  if (currentKitchen && currentKitchen !== "All Kitchens") {
    list = list.filter(t => {
      const k = String(t.kitchen_name || "").trim();
      const z = String(t.zone_name || "").trim();
      if (currentKitchen === "Nellore") {
        return k === "Nellore" || z === "Nellore";
      } else if (currentKitchen === "Narsingi") {
        return k === "Narsingi" || z === "Narsingi";
      } else if (currentKitchen === "Kandi") {
        return k === "Kandi" && z !== "Nellore";
      }
      return k === currentKitchen.trim();
    });
  }

  // 2. Zone Filter
  if (currentZone && currentZone !== "All Zones") {
    list = list.filter(t => String(t.zone_name).trim() === currentZone.trim());
  }

  // 3. Area Filter
  if (currentArea && currentArea !== "All Areas") {
    list = list.filter(t => String(t.area_name).trim() === currentArea.trim());
  }

  // 4. Equipment Filter
  if (currentEquipment && currentEquipment !== "All Equipment") {
    list = list.filter(t => {
      const resEq = resolveEquipment(t);
      const rawEq = String(t.equipment_name || "").trim();
      return resEq === currentEquipment.trim() || rawEq === currentEquipment.trim();
    });
  }

  // 5. Time Window Filter
  if (currentTimeFilter && currentTimeFilter !== "All Time") {
    const now = new Date();
    list = list.filter(t => {
      // Pending Signoff filter: Completed but not dual verified
      if (currentTimeFilter === "Pending Signoff") {
        return (t.status === "COMPLETED" && !t.is_dual_verified);
      }

      // Check dates
      const raisedDate = t.ticket_raised_time && t.ticket_raised_time !== "—" ? new Date(t.ticket_raised_time) : null;
      const compDate = t.ticket_completion_time && t.ticket_completion_time !== "—" ? new Date(t.ticket_completion_time) : null;

      const raisedDiffHours = raisedDate && !isNaN(raisedDate.getTime()) ? (now - raisedDate) / (1000 * 60 * 60) : null;
      const compDiffHours = compDate && !isNaN(compDate.getTime()) ? (now - compDate) / (1000 * 60 * 60) : null;

      if (currentTimeFilter === "Today") {
        if (t.is_today === true) return true;

        if (raisedDate && !isNaN(raisedDate.getTime())) {
          if (now.toDateString() === raisedDate.toDateString() || (raisedDiffHours !== null && raisedDiffHours <= 24)) return true;
        }
        if (compDate && !isNaN(compDate.getTime())) {
          if (now.toDateString() === compDate.toDateString() || (compDiffHours !== null && compDiffHours <= 24)) return true;
        }
        if (t.raiser_verified_at && t.raiser_verified_at !== "—") {
          const rv = new Date(t.raiser_verified_at);
          if (!isNaN(rv.getTime()) && (now.toDateString() === rv.toDateString() || (now - rv) / (1000 * 60 * 60) <= 24)) return true;
        }
        if (t.admin_verified_at && t.admin_verified_at !== "—") {
          const av = new Date(t.admin_verified_at);
          if (!isNaN(av.getTime()) && (now.toDateString() === av.toDateString() || (now - av) / (1000 * 60 * 60) <= 24)) return true;
        }
        return false;
      } else if (currentTimeFilter === "Yesterday") {
        return (
          (raisedDiffHours !== null && raisedDiffHours > 24 && raisedDiffHours <= 48) ||
          (compDiffHours !== null && compDiffHours > 24 && compDiffHours <= 48)
        );
      } else if (currentTimeFilter === "Last 7 Days") {
        return (
          (raisedDiffHours !== null && raisedDiffHours <= (7 * 24)) ||
          (compDiffHours !== null && compDiffHours <= (7 * 24))
        );
      } else if (currentTimeFilter === "Last 30 Days") {
        return (
          (raisedDiffHours !== null && raisedDiffHours <= (30 * 24)) ||
          (compDiffHours !== null && compDiffHours <= (30 * 24))
        );
      }
      return true;
    });
  }

  // 6. Priority Filter
  if (currentPriority && currentPriority !== "All Priorities") {
    list = list.filter(t => String(t.priority).toUpperCase() === currentPriority.toUpperCase());
  }

  // 7. Status Filter
  if (currentStatus && currentStatus !== "All Statuses") {
    if (currentStatus === "PENDING") {
      list = list.filter(t => ["RAISED", "ASSIGNED", "IN_PROGRESS", "PENDING_SPARES"].includes(String(t.status).toUpperCase()));
    } else {
      list = list.filter(t => String(t.status).toUpperCase() === currentStatus.toUpperCase());
    }
  }

  // 8. Category Filter
  if (currentCategory && currentCategory !== "All Categories") {
    list = list.filter(t => String(t.category).trim() === currentCategory.trim());
  }

  // 9. Search Filter
  if (currentSearch) {
    const q = currentSearch;
    list = list.filter(t => {
      const resEq = resolveEquipment(t).toLowerCase();
      return (
        String(t.ticket_no || "").toLowerCase().includes(q) ||
        String(t.title || "").toLowerCase().includes(q) ||
        String(t.equipment_name || "").toLowerCase().includes(q) ||
        resEq.includes(q) ||
        String(t.kitchen_name || "").toLowerCase().includes(q) ||
        String(t.zone_name || "").toLowerCase().includes(q) ||
        String(t.area_name || "").toLowerCase().includes(q) ||
        String(t.assigned_to || "").toLowerCase().includes(q) ||
        String(t.raised_by || "").toLowerCase().includes(q) ||
        String(t.cause_of_issue || "").toLowerCase().includes(q) ||
        String(t.action_taken || "").toLowerCase().includes(q) ||
        String(t.category || "").toLowerCase().includes(q)
      );
    });
  }

  // Sort Tickets
  list = sortTicketList(list, currentSortColumn, sortAscending);

  filteredTickets = list;

  // Update Dynamic KPIs & Charts
  updateExecutiveKPIs(filteredTickets);
  updateCharts(filteredTickets);

  // Render Table & Pagination
  renderTable();
  renderPagination();
}

// ==========================================================================
// 7. EXECUTIVE KPI CARDS & TIME CALCULATIONS
// ==========================================================================
function updateExecutiveKPIs(tickets) {
  const total = tickets.length;
  
  const raisedCount = tickets.filter(t => t.status === "RAISED").length;
  const assignedCount = tickets.filter(t => t.status === "ASSIGNED").length;
  const inProgCount = tickets.filter(t => ["IN_PROGRESS", "PENDING_SPARES"].includes(t.status)).length;
  const pendingTotal = raisedCount + assignedCount + inProgCount;
  
  const completedCount = tickets.filter(t => t.status === "COMPLETED").length;
  const verifiedCount = tickets.filter(t => t.status === "VERIFIED" || t.is_dual_verified).length;

  let totalMttrMinutes = 0;
  let countMttr = 0;
  let totalDelayMinutes = 0;
  let countDelay = 0;

  tickets.forEach(t => {
    // Parse MTTR
    if (t.ticket_completion_time && t.repair_start_time && t.ticket_completion_time !== "—" && t.repair_start_time !== "—") {
      const start = new Date(t.repair_start_time);
      const end = new Date(t.ticket_completion_time);
      if (!isNaN(start) && !isNaN(end) && end >= start) {
        const mins = (end - start) / (1000 * 60);
        totalMttrMinutes += mins;
        countMttr++;
      }
    }
    // Parse Response Delay
    if (t.repair_start_time && t.ticket_raised_time && t.repair_start_time !== "—" && t.ticket_raised_time !== "—") {
      const raised = new Date(t.ticket_raised_time);
      const start = new Date(t.repair_start_time);
      if (!isNaN(raised) && !isNaN(start) && start >= raised) {
        const mins = (start - raised) / (1000 * 60);
        totalDelayMinutes += mins;
        countDelay++;
      }
    }
  });

  const avgMttrStr = countMttr > 0 ? formatMinutesToDHM(totalMttrMinutes / countMttr) : "—";
  const avgDelayStr = countDelay > 0 ? formatMinutesToDHM(totalDelayMinutes / countDelay) : "—";

  // Set card values
  setElemText("valTotal", total);
  setElemText("valPending", pendingTotal);
  setElemText("tagRaised", `${raisedCount} Raised`);
  setElemText("tagAssigned", `${assignedCount} Assigned`);
  setElemText("tagInProg", `${inProgCount} In Repair`);
  setElemText("valCompleted", completedCount);
  setElemText("valVerified", verifiedCount);
  setElemText("valMttr", avgMttrStr);
  setElemText("valDelay", avgDelayStr);

  highlightActiveKpiCard(currentStatus);
}

function highlightActiveKpiCard(status) {
  const cards = ["kpiCardTotal", "kpiCardPending", "kpiCardCompleted", "kpiCardVerified"];
  cards.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active-kpi");
  });

  if (status === "All Statuses") {
    const el = document.getElementById("kpiCardTotal");
    if (el) el.classList.add("active-kpi");
  } else if (status === "PENDING" || status === "RAISED" || status === "ASSIGNED" || status === "IN_PROGRESS") {
    const el = document.getElementById("kpiCardPending");
    if (el) el.classList.add("active-kpi");
  } else if (status === "COMPLETED") {
    const el = document.getElementById("kpiCardCompleted");
    if (el) el.classList.add("active-kpi");
  } else if (status === "VERIFIED") {
    const el = document.getElementById("kpiCardVerified");
    if (el) el.classList.add("active-kpi");
  }
}

function formatMinutesToDHM(totalMinutes) {
  if (!totalMinutes || isNaN(totalMinutes) || totalMinutes <= 0) return "0m";
  
  const mins = Math.round(totalMinutes);
  const days = Math.floor(mins / 1440);
  const hours = Math.floor((mins % 1440) / 60);
  const remainingMins = mins % 60;

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (remainingMins > 0 || parts.length === 0) parts.push(`${remainingMins}m`);

  return parts.join(" ");
}

function formatDateTimeStr(isoStr) {
  if (!isoStr || isoStr === "—" || isoStr === "None" || isoStr === "null" || isoStr === "NaT") return "—";
  try {
    let cleanStr = String(isoStr).trim();
    if (cleanStr.includes(" ") && !cleanStr.includes("T")) {
      cleanStr = cleanStr.replace(" ", "T");
    }
    const d = new Date(cleanStr);
    if (isNaN(d.getTime())) return isoStr;
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const day = d.getDate();
    const month = months[d.getMonth()];
    let hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${day} ${month}, ${hours}:${minutes} ${ampm}`;
  } catch (e) {
    return isoStr;
  }
}

function setElemText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ==========================================================================
// 8. SPREADSHEET TABLE RENDERING & REORDERABLE CELL MAPPING
// ==========================================================================
function sortTicketList(tickets, col, asc) {
  return [...tickets].sort((a, b) => {
    let valA = a[col] ?? "";
    let valB = b[col] ?? "";

    if (col === "ticket_no") {
      return asc ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(valA));
    }

    if (col === "ticket_raised_time" || col === "assigned_time" || col === "assigned_to_time" || col === "repair_start_time" || col === "ticket_completion_time") {
      const timeA = valA && valA !== "—" ? new Date(valA).getTime() : 0;
      const timeB = valB && valB !== "—" ? new Date(valB).getTime() : 0;
      return asc ? timeA - timeB : timeB - timeA;
    }

    if (typeof valA === "string") valA = valA.toLowerCase();
    if (typeof valB === "string") valB = valB.toLowerCase();

    if (valA < valB) return asc ? -1 : 1;
    if (valA > valB) return asc ? 1 : -1;
    return 0;
  });
}

function sortTable(columnKey) {
  if (currentSortColumn === columnKey) {
    sortAscending = !sortAscending;
  } else {
    currentSortColumn = columnKey;
    sortAscending = true;
  }
  renderTableHeader();
  applyFilters();
}

function handlePageSizeChange() {
  const sel = document.getElementById("pageSizeSelect");
  if (!sel) return;
  pageSize = sel.value === "all" ? 999999 : parseInt(sel.value, 10);
  currentPage = 1;
  renderTable();
  renderPagination();
}

function renderCellHtml(colId, t, rowIndex) {
  const prio = String(t.priority || "MEDIUM").toUpperCase();
  let pillPrioClass = "medium";
  if (prio === "HIGH" || prio === "URGENT" || prio === "CRITICAL") pillPrioClass = "high";
  else if (prio === "LOW") pillPrioClass = "low";

  const st = String(t.status || "RAISED").toUpperCase();
  let statusClass = "status-raised";
  if (st === "IN_PROGRESS") statusClass = "status-in_progress";
  else if (st === "ASSIGNED") statusClass = "status-assigned";
  else if (st === "COMPLETED") statusClass = "status-completed";
  else if (st === "VERIFIED") statusClass = "status-verified";

  const isDual = t.is_dual_verified || (t.is_admin_verified && t.is_raiser_verified);
  let dualBadge = `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
  if (isDual) {
    dualBadge = `<span class="badge badge-success" title="Dual Verified by Kitchen In-Charge & Maintenance Admin">🛡️ Verified</span>`;
  } else if (t.is_raiser_verified && !t.is_admin_verified) {
    dualBadge = `<span class="badge badge-warning" title="Signed by In-Charge, waiting for Admin verification">⏳ In-Charge</span>`;
  } else if (!t.is_raiser_verified && t.is_admin_verified) {
    dualBadge = `<span class="badge badge-warning" title="Verified by Admin, waiting for In-Charge sign-off">⏳ Admin</span>`;
  } else if (st === "COMPLETED") {
    dualBadge = `<span class="badge" style="background:#fef2f2; color:#dc2626; border:1px solid #fee2e2; font-size:0.68rem;" title="Repair completed! Waiting for sign-off">⚠️ Sign-off</span>`;
  }

  const raisedInit = t.raised_by_initials || "MK";
  const assignedInit = t.assigned_to_initials || "U";
  const isUnassigned = assignedInit === "U" || t.assigned_to === "Unassigned";

  const raisedTimeFormatted = formatDateTimeStr(t.ticket_raised_time);
  const rawAssignTime = t.assigned_to_time || t.assigned_time;
  const assignedTimeFormatted = rawAssignTime && rawAssignTime !== "—"
    ? formatDateTimeStr(rawAssignTime)
    : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
  const startTimeFormatted = t.repair_start_time && t.repair_start_time !== "—"
    ? formatDateTimeStr(t.repair_start_time)
    : `<span class="text-muted" style="font-size: 0.72rem;">—</span>`;
  const completedTimeFormatted = t.ticket_completion_time && t.ticket_completion_time !== "—" 
    ? formatDateTimeStr(t.ticket_completion_time) 
    : `<span class="text-muted" style="font-size: 0.72rem;">— (Open)</span>`;

  switch (colId) {
    case "col-index":
      return `<td class="col-index" style="text-align: center; color: #94a3b8; font-size: 0.72rem; font-weight: 500;">${rowIndex}</td>`;
    case "col-ticket_no":
      return `<td class="col-ticket_no col-ticket-no">${escapeHtml(t.ticket_no)}</td>`;
    case "col-kitchen_name":
      return `<td class="col-kitchen_name col-kitchen" title="${escapeHtml(t.kitchen_name)}">${escapeHtml(t.kitchen_name)}</td>`;
    case "col-zone_name":
      return `<td class="col-zone_name col-zone" title="${escapeHtml(t.zone_name)}"><span class="badge badge-neutral" style="font-size: 0.68rem;">${escapeHtml(t.zone_name)}</span></td>`;
    case "col-area_name":
      return `<td class="col-area_name" title="${escapeHtml(t.area_name || '—')}">${escapeHtml(t.area_name || '—')}</td>`;
    case "col-equipment_name":
      return `<td class="col-equipment_name col-equipment" title="${escapeHtml(t.equipment_name)}"><strong>${escapeHtml(t.equipment_name)}</strong></td>`;
    case "col-title":
      return `<td class="col-title" title="${escapeHtml(t.title)}">${escapeHtml(t.title)}</td>`;
    case "col-status":
      return `<td class="col-status"><span class="status-pill ${statusClass}">${st}</span></td>`;
    case "col-priority":
      return `<td class="col-priority"><span class="priority-pill ${pillPrioClass}"><span class="priority-dot ${pillPrioClass}"></span>${prio}</span></td>`;
    case "col-raised_time":
      return `<td class="col-raised_time col-time-cell" title="Complaint Raised: ${escapeHtml(t.ticket_raised_time)}">${raisedTimeFormatted}</td>`;
    case "col-assigned_time":
      return `<td class="col-assigned_time col-time-cell" title="Technician Assigned: ${escapeHtml(rawAssignTime || '—')}">${assignedTimeFormatted}</td>`;
    case "col-start_delay":
      return `<td class="col-start_delay col-duration" title="Time taken from raised to technician start: ${t.response_delay_dhm}">${t.response_delay_dhm || '—'}</td>`;
    case "col-start_time":
      return `<td class="col-start_time col-time-cell" title="Work Started: ${escapeHtml(t.repair_start_time)}">${startTimeFormatted}</td>`;
    case "col-mttr":
      return `<td class="col-mttr col-duration" style="font-weight: 700; color: #0284c7;" title="Hands-on repair duration: ${t.mttr_dhm}">${t.mttr_dhm || '—'}</td>`;
    case "col-completed_time":
      return `<td class="col-completed_time col-time-cell" title="Repair Completed: ${escapeHtml(t.ticket_completion_time)}">${completedTimeFormatted}</td>`;
    case "col-action_taken":
      return `<td class="col-action_taken col-action-taken" title="${escapeHtml(t.action_taken)}">${escapeHtml(t.action_taken)}</td>`;
    case "col-assigned_to":
      return `<td class="col-assigned_to"><div class="user-cell"><span class="avatar-circle ${isUnassigned ? 'avatar-unassigned' : ''}">${assignedInit}</span><span class="user-name-text" title="${escapeHtml(t.assigned_to)}">${escapeHtml(t.assigned_to)}</span></div></td>`;
    case "col-raised_by":
      return `<td class="col-raised_by"><div class="user-cell"><span class="avatar-circle">${raisedInit}</span><span class="user-name-text" title="${escapeHtml(t.raised_by)}">${escapeHtml(t.raised_by)}</span></div></td>`;
    case "col-dual_signed":
      return `<td class="col-dual_signed" style="text-align: center;">${dualBadge}</td>`;
    case "col-action":
      return `<td class="col-action" style="text-align: center;" onclick="event.stopPropagation(); openTicketModal('${escapeHtml(t.ticket_no)}')"><button class="btn-icon" title="View Ticket Details"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button></td>`;
    default:
      return `<td>—</td>`;
  }
}

function renderTable() {
  const tbody = document.getElementById("ticketsTbody");
  const visibleCountEl = document.getElementById("visibleCount");
  const totalCountEl = document.getElementById("totalDatasetCount");

  if (visibleCountEl) visibleCountEl.textContent = filteredTickets.length;
  if (totalCountEl) totalCountEl.textContent = allTickets.length;

  if (!tbody) return;

  if (filteredTickets.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="${columnOrder.length}" style="text-align: center; padding: 40px; color: #64748b;">
          <div style="font-size: 1.6rem; margin-bottom: 6px;">🔍</div>
          <div style="font-weight: 600; font-size: 0.9rem; color: #334155;">No tickets found matching current filters</div>
          <div style="font-size: 0.78rem; margin-top: 3px;">Try resetting your filters or selecting 'All Time'.</div>
          <button class="btn btn-outline" style="margin-top: 10px;" onclick="resetOnlyFilters()">Reset Filters</button>
        </td>
      </tr>
    `;
    return;
  }

  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = startIdx + pageSize;
  const pageTickets = filteredTickets.slice(startIdx, endIdx);

  tbody.innerHTML = pageTickets.map((t, index) => {
    const rowIndex = startIdx + index + 1;

    const prio = String(t.priority || "MEDIUM").toUpperCase();
    let rowPrioClass = "priority-medium";
    if (prio === "HIGH" || prio === "URGENT" || prio === "CRITICAL") rowPrioClass = "priority-high";
    else if (prio === "LOW") rowPrioClass = "priority-low";

    const cellsHtml = columnOrder.map(colId => renderCellHtml(colId, t, rowIndex)).join("");

    return `
      <tr class="${rowPrioClass}" onclick="openTicketModal('${escapeHtml(t.ticket_no)}')">
        ${cellsHtml}
      </tr>
    `;
  }).join("");

  applyColumnVisibility();
}

function renderPagination() {
  const totalPages = Math.ceil(filteredTickets.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;

  const infoEl = document.getElementById("paginationInfo");
  const pageNumEl = document.getElementById("pageNumber");
  const prevBtn = document.getElementById("btnPrevPage");
  const nextBtn = document.getElementById("btnNextPage");

  if (infoEl) infoEl.textContent = `Page ${currentPage} of ${totalPages} (${filteredTickets.length} items)`;
  if (pageNumEl) pageNumEl.textContent = `${currentPage}`;

  if (prevBtn) prevBtn.disabled = (currentPage <= 1);
  if (nextBtn) nextBtn.disabled = (currentPage >= totalPages);
}

function prevPage() {
  if (currentPage > 1) {
    currentPage--;
    renderTable();
    renderPagination();
    scrollTableToTop();
  }
}

function nextPage() {
  const totalPages = Math.ceil(filteredTickets.length / pageSize) || 1;
  if (currentPage < totalPages) {
    currentPage++;
    renderTable();
    renderPagination();
    scrollTableToTop();
  }
}

function scrollTableToTop() {
  const wrapper = document.querySelector(".excel-table-wrapper");
  if (wrapper) wrapper.scrollTop = 0;
}

// ==========================================================================
// 9. FILTERED CSV EXPORT
// ==========================================================================
function exportFilteredCSV() {
  if (!filteredTickets || filteredTickets.length === 0) {
    alert("No tickets match the current filter selection to export.");
    return;
  }

  const headers = [
    "Ticket #",
    "Kitchen",
    "Zone",
    "Area / Section",
    "Machine / Asset",
    "Issue Description",
    "Status",
    "Priority",
    "Complaint Raised Time",
    "Technician Assigned Time",
    "Start Delay",
    "Work Started Time",
    "Time to Fix (Hands-on MTTR)",
    "Completion Time",
    "Action Taken by Tech",
    "Assigned Technician",
    "Raised By",
    "Dual Verified Status",
    "Root Cause of Issue"
  ];

  const rows = filteredTickets.map(t => {
    const isDual = t.is_dual_verified || (t.is_admin_verified && t.is_raiser_verified);
    let dualStatus = "Pending";
    if (isDual) dualStatus = "Dual Verified";
    else if (t.is_raiser_verified) dualStatus = "In-Charge Signed";
    else if (t.is_admin_verified) dualStatus = "Admin Signed";
    else if (t.status === "COMPLETED") dualStatus = "Awaiting Verification";

    const cleanField = (str) => `"${String(str || "").replace(/"/g, '""')}"`;

    return [
      cleanField(t.ticket_no),
      cleanField(t.kitchen_name),
      cleanField(t.zone_name || "—"),
      cleanField(t.area_name || "—"),
      cleanField(t.equipment_name),
      cleanField(t.title),
      cleanField(t.status),
      cleanField(t.priority),
      cleanField(formatDateTimeStr(t.ticket_raised_time)),
      cleanField(formatDateTimeStr(t.assigned_to_time || t.assigned_time)),
      cleanField(t.response_delay_dhm || "—"),
      cleanField(formatDateTimeStr(t.repair_start_time)),
      cleanField(t.mttr_dhm || "—"),
      cleanField(formatDateTimeStr(t.ticket_completion_time)),
      cleanField(t.action_taken || "Under diagnostics"),
      cleanField(t.assigned_to || "Unassigned"),
      cleanField(t.raised_by || "Staff"),
      cleanField(dualStatus),
      cleanField(t.cause_of_issue || "Under diagnostics")
    ];
  });

  const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\r\n");
  const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  
  const kitchenTag = currentKitchen !== "All Kitchens" ? `_${currentKitchen.replace(/\s+/g, '_')}` : "";
  const zoneTag = currentZone !== "All Zones" ? `_${currentZone.replace(/\s+/g, '_')}` : "";
  const statusTag = currentStatus !== "All Statuses" ? `_${currentStatus}` : "";
  const dateStr = new Date().toISOString().slice(0, 10);
  
  link.setAttribute("href", url);
  link.setAttribute("download", `PMT_Report${kitchenTag}${zoneTag}${statusTag}_${dateStr}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ==========================================================================
// 10. CENTER ANIMATED TICKET DETAIL POPUP MODAL
// ==========================================================================
function openTicketModal(ticketNo) {
  const t = allTickets.find(item => item.ticket_no === ticketNo);
  if (!t) return;

  const resolvedEq = resolveEquipment(t);

  // Header Info
  setElemText("modalTicketNo", t.ticket_no);
  setElemText("modalTitle", t.title);

  // Status Badge
  const stBadge = document.getElementById("modalStatusBadge");
  if (stBadge) {
    stBadge.textContent = t.status;
    stBadge.className = `status-pill status-${t.status.toLowerCase()}`;
  }

  // Priority Badge
  const prioBadge = document.getElementById("modalPriorityBadge");
  if (prioBadge) {
    prioBadge.textContent = `• ${t.priority}`;
    prioBadge.className = `priority-pill ${t.priority.toLowerCase()}`;
  }

  // Category Badge
  const catBadge = document.getElementById("modalCategoryBadge");
  if (catBadge) {
    catBadge.textContent = t.category || "General";
  }

  // Facility & Location Banner
  setElemText("modalKitchen", t.kitchen_name || "—");
  setElemText("modalZone", t.zone_name || "General");
  setElemText("modalArea", t.area_name || "—");
  setElemText("modalEquipment", resolvedEq);

  // Problem & Action
  setElemText("modalCause", t.cause_of_issue || "Under diagnostics");
  setElemText("modalAction", t.action_taken || "Work in progress");

  // People
  setElemText("modalRaiser", t.raised_by || "Staff");
  setElemText("modalRaiserAvatar", t.raised_by_initials || "R");
  setElemText("modalTech", t.assigned_to || "Unassigned");
  setElemText("modalTechAvatar", t.assigned_to_initials || "T");

  // Milestone Timestamps & Clean Fallbacks
  const raisedStr = formatDateTimeStr(t.ticket_raised_time);
  const assignRaw = t.assigned_to_time || t.assigned_time;
  const hasAssigned = assignRaw && assignRaw !== "—" && !String(assignRaw).toLowerCase().includes("nan") && !String(assignRaw).toLowerCase().includes("none") && !String(assignRaw).toLowerCase().includes("null");
  const assignStr = hasAssigned 
    ? formatDateTimeStr(assignRaw) 
    : `<span class="badge-unassigned">⏳ Unassigned</span>`;

  const startRaw = t.repair_start_time;
  const hasStarted = startRaw && startRaw !== "—" && !String(startRaw).toLowerCase().includes("nan") && !String(startRaw).toLowerCase().includes("none") && !String(startRaw).toLowerCase().includes("null");
  const startStr = hasStarted 
    ? formatDateTimeStr(startRaw) 
    : `<span class="badge-waiting-start">⏳ Work Not Started</span>`;

  const endRaw = t.ticket_completion_time;
  const hasCompleted = endRaw && endRaw !== "—" && !String(endRaw).toLowerCase().includes("nan") && !String(endRaw).toLowerCase().includes("none") && !String(endRaw).toLowerCase().includes("null");
  const endStr = hasCompleted 
    ? formatDateTimeStr(endRaw) 
    : `<span class="badge-in-progress">⏳ Open / In Progress</span>`;

  const elRaised = document.getElementById("modalTimeRaised");
  if (elRaised) elRaised.innerHTML = raisedStr;

  const elAssign = document.getElementById("modalTimeAssign");
  if (elAssign) elAssign.innerHTML = assignStr;

  const elStart = document.getElementById("modalTimeStart");
  if (elStart) elStart.innerHTML = startStr;

  const elEnd = document.getElementById("modalTimeEnd");
  if (elEnd) elEnd.innerHTML = endStr;

  // Prominent Highlight Delay Banner
  const valResp = document.getElementById("valResponseDelay");
  const labelResp = document.getElementById("labelResponseDelay");
  const badgeResp = document.getElementById("badgeResponseDelay");
  const cardResp = document.getElementById("cardResponseDelay");

  const valMttr = document.getElementById("valMttrDuration");
  const badgeMttr = document.getElementById("badgeMttr");
  const cardMttr = document.getElementById("cardMttr");

  const valDt = document.getElementById("valTotalDowntime");
  const badgeDt = document.getElementById("badgeDowntime");

  if (valResp) {
    const respDelay = t.response_delay_dhm || "—";
    valResp.textContent = respDelay;

    if (!hasStarted) {
      if (labelResp) labelResp.textContent = "Start Delay (Waiting to Start)";
      if (badgeResp) {
        badgeResp.textContent = "🚨 Awaiting Start";
        badgeResp.className = "delay-metric-badge delay-badge-waiting";
      }
      if (cardResp) cardResp.className = "delay-metric-card delay-card-waiting";
    } else {
      if (labelResp) labelResp.textContent = "Response Delay (Before Start)";
      if (badgeResp) {
        badgeResp.textContent = "✅ Started";
        badgeResp.className = "delay-metric-badge delay-badge-done";
      }
      if (cardResp) cardResp.className = "delay-metric-card delay-card-done";
    }
  }

  if (valMttr) {
    if (hasCompleted) {
      valMttr.textContent = t.mttr_dhm || "—";
      if (badgeMttr) {
        badgeMttr.textContent = "✅ Fixed";
        badgeMttr.className = "delay-metric-badge delay-badge-done";
      }
      if (cardMttr) cardMttr.className = "delay-metric-card delay-card-done";
    } else if (hasStarted) {
      valMttr.textContent = "Active in Repair";
      if (badgeMttr) {
        badgeMttr.textContent = "🔧 In Progress";
        badgeMttr.className = "delay-metric-badge delay-badge-waiting";
      }
      if (cardMttr) cardMttr.className = "delay-metric-card delay-card-waiting";
    } else {
      valMttr.textContent = "—";
      if (badgeMttr) {
        badgeMttr.textContent = "⏳ Not Started";
        badgeMttr.className = "delay-metric-badge";
      }
      if (cardMttr) cardMttr.className = "delay-metric-card";
    }
  }

  if (valDt) {
    valDt.textContent = t.downtime_dhm || "—";
    if (badgeDt) {
      badgeDt.textContent = hasCompleted ? "Total Downtime" : "Active Breakdown";
    }
  }

  const raiserSignText = t.is_raiser_verified 
    ? `✅ Signed (${t.raiser_verified_at && t.raiser_verified_at !== "—" ? formatDateTimeStr(t.raiser_verified_at) : "Approved"})`
    : "⏳ Pending Sign-off";
    
  const adminSignText = t.is_admin_verified 
    ? `✅ Verified (${t.admin_verified_at && t.admin_verified_at !== "—" ? formatDateTimeStr(t.admin_verified_at) : "Verified"})`
    : "⏳ Pending Sign-off";

  setElemText("modalRaiserSign", raiserSignText);
  setElemText("modalAdminSign", adminSignText);

  // Spares Tab
  const spares = Array.isArray(t.spares) ? t.spares : [];
  setElemText("modalSparesCount", spares.length);
  const sparesBox = document.getElementById("modalSparesList");
  if (sparesBox) {
    if (spares.length > 0) {
      sparesBox.innerHTML = `
        <table class="drawer-mini-table">
          <thead>
            <tr>
              <th>Part Name / Code</th>
              <th style="width: 60px; text-align: center;">Qty</th>
              <th style="width: 70px;">UOM</th>
            </tr>
          </thead>
          <tbody>
            ${spares.map(s => `
              <tr>
                <td style="font-weight: 600; color: #1e293b;">${escapeHtml(s.spare_name || s.spare_code || 'Spare Part')}</td>
                <td style="text-align: center; font-weight: 700;">${s.used_qty || 1}</td>
                <td>${s.uom || 'PCS'}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    } else {
      sparesBox.innerHTML = `<div class="empty-tab-state">📦 No spare parts consumed for this repair.</div>`;
    }
  }

  // Tools Tab
  const tools = Array.isArray(t.tools) ? t.tools : [];
  setElemText("modalToolsCount", tools.length);
  const toolsBox = document.getElementById("modalToolsList");
  if (toolsBox) {
    if (tools.length > 0) {
      toolsBox.innerHTML = `
        <table class="drawer-mini-table">
          <thead>
            <tr>
              <th>Tool Name / Code</th>
              <th style="width: 80px;">Status</th>
            </tr>
          </thead>
          <tbody>
            ${tools.map(tool => `
              <tr>
                <td style="font-weight: 600; color: #1e293b;">${escapeHtml(tool.tool_name || tool.tool_code || 'Maintenance Tool')}</td>
                <td><span class="badge badge-neutral">${escapeHtml(tool.return_status || 'Issued')}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    } else {
      toolsBox.innerHTML = `<div class="empty-tab-state">🔧 No special workshop tools issued.</div>`;
    }
  }

  // Photos Tab
  const media = Array.isArray(t.media) ? t.media : [];
  setElemText("modalPhotosCount", media.length);
  const photosBox = document.getElementById("modalPhotosList");
  if (photosBox) {
    if (media.length > 0) {
      photosBox.innerHTML = `
        <div class="modal-photo-grid">
          ${media.map(m => {
            const url = m.media_url || m.file_url || m.url || '';
            const stage = m.upload_stage || 'Maintenance Proof';
            return `
            <div class="photo-card" onclick="openImageLightbox('${escapeHtml(url)}', '${escapeHtml(t.ticket_no)} • ${escapeHtml(stage)}')">
              <a href="${escapeHtml(url)}" target="_blank" rel="noopener" onclick="event.preventDefault(); openImageLightbox('${escapeHtml(url)}', '${escapeHtml(t.ticket_no)} • ${escapeHtml(stage)}')">
                <img src="${escapeHtml(url)}" alt="Ticket Proof (${escapeHtml(stage)})" loading="lazy" />
              </a>
              <div class="photo-caption">
                <span class="photo-stage-tag stage-${stage.toLowerCase()}">${escapeHtml(stage)}</span>
                <span class="photo-view-hint">🔍 Fullscreen</span>
              </div>
            </div>
          `}).join("")}
        </div>
      `;
    } else {
      photosBox.innerHTML = `<div class="empty-tab-state">📷 No photo proofs uploaded.</div>`;
    }
  }

  // Default to photos tab
  switchModalSubTab("photos");

  const dialog = document.getElementById("ticketModalDialog");
  const backdrop = document.getElementById("ticketModalBackdrop");
  if (dialog) dialog.classList.add("active");
  if (backdrop) backdrop.classList.add("active");
}

function closeTicketModal() {
  const dialog = document.getElementById("ticketModalDialog");
  const backdrop = document.getElementById("ticketModalBackdrop");
  if (dialog) dialog.classList.remove("active");
  if (backdrop) backdrop.classList.remove("active");
}

function switchModalSubTab(tabName) {
  ["photos", "spares", "tools"].forEach(t => {
    const btn = document.getElementById(`modalTabBtn${t.charAt(0).toUpperCase() + t.slice(1)}`);
    const pane = document.getElementById(`modalTab${t.charAt(0).toUpperCase() + t.slice(1)}`);
    if (btn) btn.classList.remove("active");
    if (pane) pane.classList.remove("active");
  });

  const activeBtn = document.getElementById(`modalTabBtn${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
  const activePane = document.getElementById(`modalTab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
  if (activeBtn) activeBtn.classList.add("active");
  if (activePane) activePane.classList.add("active");
}

function openImageLightbox(imgUrl, caption) {
  const modal = document.getElementById("imageLightbox");
  const img = document.getElementById("lightboxImg");
  const cap = document.getElementById("lightboxCaption");
  if (modal && img) {
    img.src = imgUrl;
    if (cap) cap.textContent = caption || "Ticket Proof Image";
    modal.classList.add("open");
  }
}

function closeImageLightbox() {
  const modal = document.getElementById("imageLightbox");
  if (modal) modal.classList.remove("open");
}

// ==========================================================================
// 11. DYNAMIC CHARTS (CHART.JS - CORE + EXTENDED)
// ==========================================================================
function updateCharts(tickets) {
  // --- 1. Top Problem Machines (Horizontal Bar - Resolved Custom Assets) ---
  const eqCounts = {};
  tickets.forEach(t => {
    const eq = resolveEquipment(t);
    eqCounts[eq] = (eqCounts[eq] || 0) + 1;
  });

  const sortedMachines = Object.entries(eqCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 7);

  const machineLabels = sortedMachines.map(m => m[0]);
  const machineValues = sortedMachines.map(m => m[1]);

  const ctxMachines = document.getElementById("chartTopMachines");
  if (ctxMachines) {
    if (chartTopMachinesInstance) chartTopMachinesInstance.destroy();
    chartTopMachinesInstance = new Chart(ctxMachines, {
      type: "bar",
      data: {
        labels: machineLabels,
        datasets: [{
          label: "Breakdowns Logged",
          data: machineValues,
          backgroundColor: "#ea580c",
          borderRadius: 4,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#0f172a",
            titleFont: { family: 'Inter', size: 11 },
            bodyFont: { family: 'Inter', size: 11 },
            padding: 8,
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            grid: { color: "#f1f5f9" },
            ticks: { font: { family: 'Inter', size: 10 }, precision: 0 }
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { family: 'Inter', size: 10, weight: '500' },
              callback: function(val) {
                const label = this.getLabelForValue(val);
                return label.length > 18 ? label.substr(0, 16) + "..." : label;
              }
            }
          }
        }
      }
    });
  }

  // --- 2. Status Distribution Donut ---
  const stCounts = {
    "Dual Verified": 0,
    "Completed": 0,
    "In Repair": 0,
    "Assigned": 0,
    "Raised": 0
  };

  tickets.forEach(t => {
    const st = String(t.status || "").toUpperCase();
    if (st === "VERIFIED" || t.is_dual_verified) stCounts["Dual Verified"]++;
    else if (st === "COMPLETED") stCounts["Completed"]++;
    else if (st === "IN_PROGRESS" || st === "PENDING_SPARES") stCounts["In Repair"]++;
    else if (st === "ASSIGNED") stCounts["Assigned"]++;
    else if (st === "RAISED") stCounts["Raised"]++;
  });

  const ctxStatus = document.getElementById("chartStatus");
  if (ctxStatus) {
    if (chartStatusInstance) chartStatusInstance.destroy();
    chartStatusInstance = new Chart(ctxStatus, {
      type: "doughnut",
      data: {
        labels: Object.keys(stCounts),
        datasets: [{
          data: Object.values(stCounts),
          backgroundColor: ["#10b981", "#0284c7", "#f59e0b", "#8b5cf6", "#ef4444"],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "66%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              boxWidth: 9,
              boxHeight: 9,
              font: { family: 'Inter', size: 10, weight: '500' },
              padding: 8
            }
          }
        }
      }
    });
  }

  // --- 3. Technician Team Leaderboard (Stacked Bar) ---
  const techCounts = {};
  tickets.forEach(t => {
    const tech = t.assigned_to || "Unassigned";
    if (tech === "Unassigned" || tech === "⏳ Unassigned") return;
    if (!techCounts[tech]) techCounts[tech] = { resolved: 0, pending: 0 };

    const st = String(t.status || "").toUpperCase();
    if (st === "COMPLETED" || st === "VERIFIED" || t.is_dual_verified) {
      techCounts[tech].resolved++;
    } else {
      techCounts[tech].pending++;
    }
  });

  const sortedTechs = Object.entries(techCounts)
    .sort((a, b) => b[1].resolved - a[1].resolved)
    .slice(0, 7);

  const techNames = sortedTechs.map(t => t[0]);
  const techResolved = sortedTechs.map(t => t[1].resolved);
  const techPending = sortedTechs.map(t => t[1].pending);

  const ctxTechs = document.getElementById("chartTechs");
  if (ctxTechs) {
    if (chartTechsInstance) chartTechsInstance.destroy();
    chartTechsInstance = new Chart(ctxTechs, {
      type: "bar",
      data: {
        labels: techNames,
        datasets: [
          {
            label: "Resolved",
            data: techResolved,
            backgroundColor: "#0284c7",
            borderRadius: 4
          },
          {
            label: "Pending",
            data: techPending,
            backgroundColor: "#cbd5e1",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            align: "end",
            labels: { boxWidth: 9, font: { family: 'Inter', size: 10 } }
          }
        },
        scales: {
          x: {
            stacked: true,
            grid: { display: false },
            ticks: {
              font: { family: 'Inter', size: 9 },
              callback: function(val) {
                const label = this.getLabelForValue(val);
                const parts = label.split(" ");
                return parts[0];
              }
            }
          },
          y: {
            stacked: true,
            grid: { color: "#f1f5f9" },
            ticks: { precision: 0, font: { size: 9 } }
          }
        }
      }
    });
  }

  // --- 4. Problem Hotspots by Zone & Area (Extended Chart) ---
  const hotspotCounts = {};
  tickets.forEach(t => {
    const loc = t.area_name && t.area_name !== "—" 
      ? `${t.zone_name || 'Zone'} - ${t.area_name}`
      : (t.zone_name || "General Facility");
    hotspotCounts[loc] = (hotspotCounts[loc] || 0) + 1;
  });

  const sortedHotspots = Object.entries(hotspotCounts)
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const hotspotLabels = sortedHotspots.length > 0 ? sortedHotspots.map(h => h[0]) : ["No Breakdowns in Filter"];
  const hotspotValues = sortedHotspots.length > 0 ? sortedHotspots.map(h => h[1]) : [0];
  const maxHotspot = Math.max(...hotspotValues, 1);

  const ctxHotspots = document.getElementById("chartHotspots");
  if (ctxHotspots) {
    if (chartHotspotsInstance) chartHotspotsInstance.destroy();
    chartHotspotsInstance = new Chart(ctxHotspots, {
      type: "bar",
      data: {
        labels: hotspotLabels,
        datasets: [{
          label: "Complaints",
          data: hotspotValues,
          backgroundColor: "#8b5cf6",
          borderRadius: 6,
          borderSkipped: false,
          barThickness: sortedHotspots.length <= 3 ? 32 : (sortedHotspots.length <= 5 ? 24 : 18),
          maxBarThickness: 34
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#0f172a",
            titleFont: { family: 'Inter', size: 11 },
            bodyFont: { family: 'Inter', size: 11 },
            padding: 8,
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            suggestedMax: maxHotspot <= 3 ? maxHotspot + 1 : Math.ceil(maxHotspot * 1.15),
            grid: { color: "#f1f5f9" },
            ticks: { precision: 0, font: { family: 'Inter', size: 10 } }
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { family: 'Inter', size: 10, weight: '500' },
              callback: function(val) {
                const label = this.getLabelForValue(val);
                return label.length > 20 ? label.substr(0, 18) + "..." : label;
              }
            }
          }
        }
      }
    });
  }

  // --- 5. Failure Category Breakdown (Extended Chart) ---
  const catCounts = {};
  tickets.forEach(t => {
    const c = (t.category || "").trim() || "General";
    catCounts[c] = (catCounts[c] || 0) + 1;
  });

  const sortedCats = Object.entries(catCounts)
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);

  const catLabels = sortedCats.length > 0 ? sortedCats.map(c => c[0]) : ["General"];
  const catValues = sortedCats.length > 0 ? sortedCats.map(c => c[1]) : [1];

  const ctxCat = document.getElementById("chartCategoryBreakdown");
  if (ctxCat) {
    if (chartCategoryBreakdownInstance) chartCategoryBreakdownInstance.destroy();
    chartCategoryBreakdownInstance = new Chart(ctxCat, {
      type: "doughnut",
      data: {
        labels: catLabels,
        datasets: [{
          data: catValues,
          backgroundColor: ["#0284c7", "#ea580c", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4", "#64748b"],
          borderWidth: 3,
          borderColor: "#ffffff",
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "50%",
        layout: {
          padding: { top: 6, bottom: 6 }
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              boxWidth: 10,
              boxHeight: 10,
              font: { family: 'Inter', size: 10, weight: '500' },
              padding: 8
            }
          },
          tooltip: {
            backgroundColor: "#0f172a",
            titleFont: { family: 'Inter', size: 11 },
            bodyFont: { family: 'Inter', size: 11 },
            padding: 8,
            cornerRadius: 6
          }
        }
      }
    });
  }

  // --- 6. MTTR / Speed to Fix by Priority Level (Extended Chart) ---
  const prioMttrSums = { "HIGH": { mins: 0, count: 0 }, "MEDIUM": { mins: 0, count: 0 }, "LOW": { mins: 0, count: 0 } };

  tickets.forEach(t => {
    const p = String(t.priority || "MEDIUM").toUpperCase();
    if (t.ticket_completion_time && t.repair_start_time && t.ticket_completion_time !== "—" && t.repair_start_time !== "—") {
      const start = new Date(t.repair_start_time);
      const end = new Date(t.ticket_completion_time);
      if (!isNaN(start) && !isNaN(end) && end >= start) {
        const mins = (end - start) / (1000 * 60);
        if (prioMttrSums[p]) {
          prioMttrSums[p].mins += mins;
          prioMttrSums[p].count++;
        }
      }
    }
  });

  const prioLabels = ["HIGH (Urgent)", "MEDIUM (Normal)", "LOW"];
  const prioAvgHours = [
    prioMttrSums["HIGH"].count > 0 ? parseFloat((prioMttrSums["HIGH"].mins / prioMttrSums["HIGH"].count / 60).toFixed(1)) : 0,
    prioMttrSums["MEDIUM"].count > 0 ? parseFloat((prioMttrSums["MEDIUM"].mins / prioMttrSums["MEDIUM"].count / 60).toFixed(1)) : 0,
    prioMttrSums["LOW"].count > 0 ? parseFloat((prioMttrSums["LOW"].mins / prioMttrSums["LOW"].count / 60).toFixed(1)) : 0
  ];
  const maxPrioHours = Math.max(...prioAvgHours);

  const ctxPrio = document.getElementById("chartMttrPriority");
  if (ctxPrio) {
    if (chartMttrPriorityInstance) chartMttrPriorityInstance.destroy();
    chartMttrPriorityInstance = new Chart(ctxPrio, {
      type: "bar",
      data: {
        labels: prioLabels,
        datasets: [{
          label: "Avg MTTR (Hours)",
          data: prioAvgHours,
          backgroundColor: ["#ea580c", "#0284c7", "#10b981"],
          borderRadius: 6,
          borderSkipped: false,
          barThickness: 44,
          maxBarThickness: 52
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#0f172a",
            titleFont: { family: 'Inter', size: 11 },
            bodyFont: { family: 'Inter', size: 11 },
            padding: 8,
            cornerRadius: 6,
            callbacks: {
              label: function(ctx) { return ` Avg Fix Time: ${ctx.raw} Hours`; }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: 'Inter', size: 10, weight: '600' } }
          },
          y: {
            beginAtZero: true,
            suggestedMax: maxPrioHours > 0 ? Math.ceil(maxPrioHours * 1.25) : 5,
            grid: { color: "#f1f5f9" },
            ticks: {
              font: { family: 'Inter', size: 10 },
              callback: function(val) { return val + "h"; }
            }
          }
        }
      }
    });
  }
}

// ==========================================================================
// 12. VISUAL ANALYTICS REPORT & CHART EXPORTS
// ==========================================================================
function downloadSingleChart(canvasId, title) {
  const chartCanvas = document.getElementById(canvasId);
  if (!chartCanvas) {
    alert("Chart canvas not found for export.");
    return;
  }

  // Ensure canvas is rendered if extended
  const extRow = document.getElementById("extendedChartsRow");
  const wasHidden = extRow && extRow.style.display === "none";
  if (wasHidden) {
    extRow.style.display = "grid";
    [chartHotspotsInstance, chartCategoryBreakdownInstance, chartMttrPriorityInstance].forEach(inst => {
      if (inst) {
        try { inst.resize(); inst.update('none'); } catch (e) {}
      }
    });
  }

  const exportWidth = 1200;
  const exportHeight = 800;
  const expCanvas = document.createElement("canvas");
  expCanvas.width = exportWidth;
  expCanvas.height = exportHeight;
  const ctx = expCanvas.getContext("2d");

  // White Background
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, exportWidth, exportHeight);

  // Top Header Banner
  const bannerGrad = ctx.createLinearGradient(0, 0, exportWidth, 0);
  bannerGrad.addColorStop(0, "#0f172a");
  bannerGrad.addColorStop(1, "#1e293b");
  ctx.fillStyle = bannerGrad;
  ctx.fillRect(0, 0, exportWidth, 110);

  // Brand / App Name
  ctx.fillStyle = "#38bdf8";
  ctx.font = "bold 13px 'Inter', system-ui, sans-serif";
  ctx.fillText("PMT ANALYSIS • PLANT MAINTENANCE & EQUIPMENT ANALYTICS", 30, 32);

  // Chart Main Title
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 24px 'Inter', system-ui, sans-serif";
  ctx.fillText(title, 30, 65);

  // Active Filters Subtitle
  const filterInfo = `Facility: ${currentKitchen}  |  Zone: ${currentZone}  |  Area: ${currentArea}  |  Status: ${currentStatus}  |  Window: ${currentTimeFilter}  |  Records: ${filteredTickets.length}`;
  ctx.fillStyle = "#94a3b8";
  ctx.font = "500 13px 'Inter', system-ui, sans-serif";
  ctx.fillText(filterInfo, 30, 93);

  // Logo in Banner
  const logoImg = document.querySelector(".brand-logo");
  if (logoImg && logoImg.complete && logoImg.naturalWidth > 0) {
    ctx.save();
    ctx.beginPath();
    ctx.arc(exportWidth - 60, 55, 28, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    ctx.drawImage(logoImg, exportWidth - 88, 27, 56, 56);
    ctx.restore();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(exportWidth - 60, 55, 28, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Chart Container Card Box
  const cardX = 30;
  const cardY = 130;
  const cardW = exportWidth - 60;
  const cardH = exportHeight - 170;

  drawRoundedRect(ctx, cardX, cardY, cardW, cardH, 8, "#f8fafc", "#e2e8f0", 1.5);

  // Draw Chart Canvas into the card with padding
  const pad = 24;
  const targetX = cardX + pad;
  const targetY = cardY + pad;
  const targetW = cardW - (pad * 2);
  const targetH = cardH - (pad * 2);

  try {
    ctx.drawImage(chartCanvas, targetX, targetY, targetW, targetH);
  } catch (err) {
    console.error("Error capturing chart canvas:", err);
  }

  // Footer
  ctx.fillStyle = "#64748b";
  ctx.font = "500 11px 'Inter', system-ui, sans-serif";
  const dateStr = new Date().toLocaleString();
  ctx.fillText(`Generated: ${dateStr} • PMT Analysis Live Dashboard Report`, 30, exportHeight - 16);
  ctx.textAlign = "right";
  ctx.fillText("The Akshaya Patra Foundation", exportWidth - 30, exportHeight - 16);
  ctx.textAlign = "left";

  if (wasHidden) {
    extRow.style.display = "none";
  }

  // Trigger download
  const cleanTitle = title.replace(/[^a-zA-Z0-9]/g, "_");
  const kitchenTag = currentKitchen !== "All Kitchens" ? `_${currentKitchen.replace(/\s+/g, '_')}` : "";
  const filename = `PMT_Chart_${cleanTitle}${kitchenTag}_${new Date().toISOString().slice(0, 10)}.png`;

  expCanvas.toBlob(blob => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, "image/png");
}

function exportVisualAnalyticsReport() {
  const btn = document.getElementById("btnDownloadChartsReport");
  const origBtnHtml = btn ? btn.innerHTML : "";
  if (btn) {
    btn.innerHTML = `<svg class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Generating Report...`;
    btn.disabled = true;
  }

  // Ensure extended charts are rendered for capture
  const extRow = document.getElementById("extendedChartsRow");
  const wasHidden = extRow && extRow.style.display === "none";
  if (wasHidden) {
    extRow.style.display = "grid";
  }

  // Force full-size layout and update for all 6 chart instances
  [
    chartTopMachinesInstance,
    chartStatusInstance,
    chartTechsInstance,
    chartHotspotsInstance,
    chartCategoryBreakdownInstance,
    chartMttrPriorityInstance
  ].forEach(inst => {
    if (inst) {
      try {
        inst.resize();
        inst.update('none');
      } catch (e) {}
    }
  });

  setTimeout(() => {
    try {
      const expWidth = 1600;
      const expHeight = 1260;
      const expCanvas = document.createElement("canvas");
      expCanvas.width = expWidth;
      expCanvas.height = expHeight;
      const ctx = expCanvas.getContext("2d");

      // Background
      ctx.fillStyle = "#f1f5f9";
      ctx.fillRect(0, 0, expWidth, expHeight);

      // Top Executive Header Banner (Dark gradient)
      const bannerH = 140;
      const bannerGrad = ctx.createLinearGradient(0, 0, expWidth, 0);
      bannerGrad.addColorStop(0, "#0f172a");
      bannerGrad.addColorStop(1, "#1e293b");
      ctx.fillStyle = bannerGrad;
      ctx.fillRect(0, 0, expWidth, bannerH);

      // Top Title Bar
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 13px 'Inter', system-ui, sans-serif";
      ctx.fillText("PMT ANALYSIS • PLANT MAINTENANCE & EQUIPMENT ANALYTICS SYSTEM", 36, 34);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 26px 'Inter', system-ui, sans-serif";
      ctx.fillText("Visual Maintenance & Equipment Analytics Report", 36, 68);

      const reportDate = new Date().toLocaleString();
      ctx.fillStyle = "#94a3b8";
      ctx.font = "500 13px 'Inter', system-ui, sans-serif";
      ctx.fillText(`Generated: ${reportDate}  •  Scope: Live Operational Supabase Dataset`, 36, 94);

      // Logo in Report Banner
      const repLogoImg = document.querySelector(".brand-logo");
      if (repLogoImg && repLogoImg.complete && repLogoImg.naturalWidth > 0) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(expWidth - 76, 56, 36, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(repLogoImg, expWidth - 112, 20, 72, 72);
        ctx.restore();
        ctx.strokeStyle = "rgba(255, 255, 255, 0.45)";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(expWidth - 76, 56, 36, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Active Filter Pills in Header
      const filters = [
        { label: "Kitchen", val: currentKitchen },
        { label: "Zone", val: currentZone },
        { label: "Area", val: currentArea },
        { label: "Asset", val: currentEquipment },
        { label: "Status", val: currentStatus },
        { label: "Time", val: currentTimeFilter }
      ];

      let filterX = 36;
      const filterY = 108;
      filters.forEach(f => {
        if (f.val && f.val !== "All Equipment" && f.val !== "All Categories") {
          const txt = `${f.label}: ${f.val}`;
          ctx.font = "600 11px 'Inter', system-ui, sans-serif";
          const tw = ctx.measureText(txt).width;
          drawRoundedRect(ctx, filterX, filterY, tw + 16, 22, 11, "rgba(255,255,255,0.12)", "rgba(255,255,255,0.2)", 1);
          ctx.fillStyle = "#e2e8f0";
          ctx.fillText(txt, filterX + 8, filterY + 15);
          filterX += tw + 12;
        }
      });

      // Executive KPI Strip Bar (White Card)
      const kpiBarY = bannerH + 16;
      const kpiBarH = 75;
      const kpiBarW = expWidth - 72;
      drawRoundedRect(ctx, 36, kpiBarY, kpiBarW, kpiBarH, 8, "#ffffff", "#cbd5e1", 1.5);

      // Metrics in KPI Bar
      const totalTickets = filteredTickets.length;
      const pendingCount = filteredTickets.filter(t => ["RAISED", "ASSIGNED", "IN_PROGRESS", "PENDING_SPARES"].includes(t.status)).length;
      const completedCount = filteredTickets.filter(t => t.status === "COMPLETED").length;
      const verifiedCount = filteredTickets.filter(t => t.status === "VERIFIED" || t.is_dual_verified).length;
      const mttrText = document.getElementById("valMttr") ? document.getElementById("valMttr").textContent : "—";
      const delayText = document.getElementById("valDelay") ? document.getElementById("valDelay").textContent : "—";

      const kpis = [
        { label: "TOTAL COMPLAINTS", val: String(totalTickets), color: "#0f172a" },
        { label: "PENDING / IN REPAIR", val: String(pendingCount), color: "#ea580c" },
        { label: "COMPLETED JOBS", val: String(completedCount), color: "#0284c7" },
        { label: "DUAL VERIFIED", val: String(verifiedCount), color: "#10b981" },
        { label: "AVG TIME TO FIX (MTTR)", val: mttrText, color: "#6366f1" },
        { label: "AVG START DELAY", val: delayText, color: "#d97706" }
      ];

      const kpiColW = kpiBarW / kpis.length;
      kpis.forEach((k, idx) => {
        const kX = 36 + (idx * kpiColW);
        if (idx > 0) {
          ctx.strokeStyle = "#f1f5f9";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(kX, kpiBarY + 12);
          ctx.lineTo(kX, kpiBarY + kpiBarH - 12);
          ctx.stroke();
        }

        ctx.fillStyle = "#64748b";
        ctx.font = "700 10px 'Inter', system-ui, sans-serif";
        ctx.fillText(k.label, kX + 16, kpiBarY + 26);

        ctx.fillStyle = k.color;
        ctx.font = "bold 20px 'JetBrains Mono', monospace";
        ctx.fillText(k.val, kX + 16, kpiBarY + 56);
      });

      // 2x3 Grid of Charts
      const chartsConfig = [
        { id: "chartTopMachines", title: "Top Problem Machines", subtitle: "Most frequent equipment breakdowns", badge: "Asset Ranking" },
        { id: "chartStatus", title: "Breakdown Status Distribution", subtitle: "Live breakdown lifecycle stages", badge: "Status" },
        { id: "chartTechs", title: "Technician Team Leaderboard", subtitle: "Resolved vs pending jobs per technician", badge: "Team Velocity" },
        { id: "chartHotspots", title: "Problem Hotspots (Zone & Area)", subtitle: "Ticket concentration across facility sections", badge: "Hotspots" },
        { id: "chartCategoryBreakdown", title: "Failure Category Distribution", subtitle: "Breakdown classification by failure type", badge: "Categories" },
        { id: "chartMttrPriority", title: "Avg Repair Time (MTTR) by Priority", subtitle: "Hands-on fix duration by severity level", badge: "Speed to Fix" }
      ];

      const gridStartY = kpiBarY + kpiBarH + 16;
      const gridCols = 3;
      const colGap = 16;
      const rowGap = 16;
      const cardW = (expWidth - 72 - (colGap * (gridCols - 1))) / gridCols;
      const cardH = 430;

      chartsConfig.forEach((cfg, idx) => {
        const colIdx = idx % gridCols;
        const rowIdx = Math.floor(idx / gridCols);
        const cX = 36 + colIdx * (cardW + colGap);
        const cY = gridStartY + rowIdx * (cardH + rowGap);

        // Chart Card Background
        drawRoundedRect(ctx, cX, cY, cardW, cardH, 8, "#ffffff", "#e2e8f0", 1.5);

        // Card Header Bar
        ctx.fillStyle = "#1e293b";
        ctx.font = "bold 14px 'Inter', system-ui, sans-serif";
        ctx.fillText(cfg.title, cX + 14, cY + 24);

        ctx.fillStyle = "#64748b";
        ctx.font = "500 11px 'Inter', system-ui, sans-serif";
        ctx.fillText(cfg.subtitle, cX + 14, cY + 40);

        // Badge
        ctx.font = "bold 9px 'Inter', system-ui, sans-serif";
        const badgeW = ctx.measureText(cfg.badge).width + 12;
        drawRoundedRect(ctx, cX + cardW - badgeW - 14, cY + 12, badgeW, 18, 4, "#f1f5f9", "#cbd5e1", 1);
        ctx.fillStyle = "#475569";
        ctx.fillText(cfg.badge, cX + cardW - badgeW - 8, cY + 24);

        // Separator line
        ctx.strokeStyle = "#f1f5f9";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(cX, cY + 50);
        ctx.lineTo(cX + cardW, cY + 50);
        ctx.stroke();

        // Draw Chart Canvas
        const cEl = document.getElementById(cfg.id);
        if (cEl) {
          const pad = 12;
          const targetX = cX + pad;
          const targetY = cY + 54;
          const targetW = cardW - (pad * 2);
          const targetH = cardH - 62;
          try {
            ctx.drawImage(cEl, targetX, targetY, targetW, targetH);
          } catch (err) {
            console.error("Error drawing chart to report:", cfg.id, err);
          }
        }
      });

      // Bottom Footer Bar
      const footerY = expHeight - 32;
      ctx.fillStyle = "#64748b";
      ctx.font = "500 11px 'Inter', system-ui, sans-serif";
      ctx.fillText("PMT Analysis • Plant Maintenance & Equipment Analytics • The Akshaya Patra Foundation", 36, footerY);

      ctx.textAlign = "right";
      ctx.fillText("Confidential Operational Intelligence • Filter-Scoped Export", expWidth - 36, footerY);
      ctx.textAlign = "left";

      if (wasHidden) {
        extRow.style.display = "none";
      }

      // Download file
      const kitchenTag = currentKitchen !== "All Kitchens" ? `_${currentKitchen.replace(/\s+/g, '_')}` : "";
      const zoneTag = currentZone !== "All Zones" ? `_${currentZone.replace(/\s+/g, '_')}` : "";
      const statusTag = currentStatus !== "All Statuses" ? `_${currentStatus}` : "";
      const dateTag = new Date().toISOString().slice(0, 10);
      const filename = `PMT_Visual_Maintenance_Analytics${kitchenTag}${zoneTag}${statusTag}_${dateTag}.png`;

      expCanvas.toBlob(blob => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        if (btn) {
          btn.innerHTML = origBtnHtml;
          btn.disabled = false;
        }
      }, "image/png");

    } catch (e) {
      console.error("Error generating visual analytics report:", e);
      alert("Error generating report: " + e.message);
      if (wasHidden && extRow) extRow.style.display = "none";
      if (btn) {
        btn.innerHTML = origBtnHtml;
        btn.disabled = false;
      }
    }
  }, 120);
}

function drawRoundedRect(ctx, x, y, width, height, radius, fillStyle, strokeStyle, lineWidth) {
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();

  if (fillStyle) {
    ctx.fillStyle = fillStyle;
    ctx.fill();
  }
  if (strokeStyle) {
    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = lineWidth || 1;
    ctx.stroke();
  }
  ctx.restore();
}

// ==========================================================================
// 13. UTILITY FUNCTIONS
// ==========================================================================
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

