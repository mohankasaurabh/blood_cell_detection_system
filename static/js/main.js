/* ========================================================================= */
/*  BloodCell AI — Front-end behaviour                                       */
/*  Theme toggle · drag & drop · loading overlay · toasts · data table       */
/*  Every block is null-safe so a single shared file works on every page.    */
/* ========================================================================= */

(function () {
    "use strict";

    /* ------------------------------------------------------------------ */
    /*  Theme toggle (persisted in localStorage)                          */
    /* ------------------------------------------------------------------ */
    function initTheme() {
        var root = document.documentElement;
        var toggle = document.getElementById("themeToggle");

        // Sync current theme (set early by the inline head script).
        var current = root.getAttribute("data-theme") || "light";

        function paint(theme) {
            root.setAttribute("data-theme", theme);
            if (toggle) toggle.innerHTML = theme === "dark" ? "☀️" : "🌙";
        }

        paint(current);

        // Guard: some pages may not render the toggle button.
        if (!toggle) return;

        toggle.addEventListener("click", function () {
            var next =
                root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem("theme", next);
            paint(next);
        });
    }

    /* ------------------------------------------------------------------ */
    /*  Toast notifications                                                */
    /* ------------------------------------------------------------------ */
    function showToast(message, type) {
        var stack = document.getElementById("toastStack");
        if (!stack) return;

        var toast = document.createElement("div");
        toast.className = "toast " + (type || "");

        var icon = type === "success" ? "✅" : type === "error" ? "⚠️" : "ℹ️";
        toast.innerHTML =
            '<span class="toast-icon">' + icon + "</span>" +
            '<span class="toast-msg"></span>';
        toast.querySelector(".toast-msg").textContent = message;

        stack.appendChild(toast);

        setTimeout(function () {
            toast.classList.add("hide");
            setTimeout(function () { toast.remove(); }, 300);
        }, 4000);
    }

    // Auto-dismiss server-rendered flash toasts after a few seconds.
    function initServerToasts() {
        var serverStack = document.getElementById("serverToasts");
        if (!serverStack) return;
        setTimeout(function () {
            Array.prototype.forEach.call(
                serverStack.querySelectorAll(".toast"),
                function (t) {
                    t.classList.add("hide");
                    setTimeout(function () { t.remove(); }, 300);
                }
            );
        }, 4500);
    }

    /* ------------------------------------------------------------------ */
    /*  Upload: drag & drop, filename preview, loading overlay            */
    /* ------------------------------------------------------------------ */
    function initUpload() {
        var dropZone = document.getElementById("dropZone");
        var fileInput = document.getElementById("fileInput");
        var form = document.getElementById("uploadForm");
        var overlay = document.getElementById("loadingOverlay");

        if (dropZone && fileInput) {
            var dropText = document.getElementById("dropText");
            var dropHint = document.getElementById("dropHint");

            ["dragenter", "dragover"].forEach(function (evt) {
                dropZone.addEventListener(evt, function (e) {
                    e.preventDefault();
                    dropZone.classList.add("dragover");
                });
            });

            ["dragleave", "drop"].forEach(function (evt) {
                dropZone.addEventListener(evt, function (e) {
                    e.preventDefault();
                    dropZone.classList.remove("dragover");
                });
            });

            dropZone.addEventListener("drop", function (e) {
                if (e.dataTransfer && e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    updateFileName();
                }
            });

            fileInput.addEventListener("change", updateFileName);

            function updateFileName() {
                if (fileInput.files && fileInput.files.length) {
                    var name = fileInput.files[0].name;
                    dropZone.classList.add("has-file");
                    if (dropText) dropText.textContent = "✓ " + name;
                    if (dropHint) dropHint.textContent = "Click to choose a different file";
                }
            }
        }

        // Show the loading overlay while detection runs.
        if (form) {
            form.addEventListener("submit", function (e) {
                if (fileInput && (!fileInput.files || !fileInput.files.length)) {
                    e.preventDefault();
                    showToast("Please choose an image first.", "error");
                    return;
                }
                if (overlay) overlay.classList.add("active");
            });
        }

        // Sample buttons navigate (GET) and also trigger server-side detection,
        // so show the same loading overlay while the request is in flight.
        if (overlay) {
            Array.prototype.forEach.call(
                document.querySelectorAll(".sample-trigger"),
                function (link) {
                    link.addEventListener("click", function () {
                        overlay.classList.add("active");
                    });
                }
            );
        }
    }

    /* ------------------------------------------------------------------ */
    /*  Reports table: search, sort, pagination                          */
    /* ------------------------------------------------------------------ */
    function initTable() {
        var table = document.getElementById("reportsTable");
        var body = document.getElementById("reportsBody");
        if (!table || !body) return;

        var allRows = Array.prototype.slice.call(body.querySelectorAll("tr"));
        var filtered = allRows.slice();

        var searchInput = document.getElementById("tableSearch");
        var resultCount = document.getElementById("resultCount");
        var noResults = document.getElementById("noResults");
        var pageInfo = document.getElementById("pageInfo");
        var pageControls = document.getElementById("pageControls");
        var paginationBar = document.getElementById("pagination");

        var PAGE_SIZE = 8;
        var currentPage = 1;
        var sortState = { index: -1, dir: 1 };

        /* ---- rendering ---- */
        function render() {
            var total = filtered.length;
            var pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
            if (currentPage > pages) currentPage = pages;

            var start = (currentPage - 1) * PAGE_SIZE;
            var end = start + PAGE_SIZE;

            // Hide all, then show the current page slice.
            allRows.forEach(function (r) { r.style.display = "none"; });
            filtered.slice(start, end).forEach(function (r) {
                r.style.display = "";
            });

            if (noResults) noResults.style.display = total ? "none" : "";
            if (paginationBar) paginationBar.style.display = total ? "" : "none";

            if (resultCount) {
                resultCount.textContent =
                    total + (total === 1 ? " report" : " reports");
            }
            if (pageInfo) {
                pageInfo.textContent = total
                    ? "Showing " + (start + 1) + "–" +
                      Math.min(end, total) + " of " + total
                    : "";
            }

            renderControls(pages);
        }

        function renderControls(pages) {
            if (!pageControls) return;
            pageControls.innerHTML = "";

            function pageButton(label, page, opts) {
                opts = opts || {};
                var btn = document.createElement("button");
                btn.className = "page-btn" + (opts.active ? " active" : "");
                btn.textContent = label;
                btn.disabled = !!opts.disabled;
                if (!opts.disabled && !opts.active) {
                    btn.addEventListener("click", function () {
                        currentPage = page;
                        render();
                    });
                }
                pageControls.appendChild(btn);
            }

            pageButton("‹", currentPage - 1, { disabled: currentPage === 1 });
            for (var p = 1; p <= pages; p++) {
                pageButton(String(p), p, { active: p === currentPage });
            }
            pageButton("›", currentPage + 1, { disabled: currentPage === pages });
        }

        /* ---- search ---- */
        if (searchInput) {
            searchInput.addEventListener("input", function () {
                var q = searchInput.value.trim().toLowerCase();
                filtered = allRows.filter(function (r) {
                    return (r.getAttribute("data-search") || "").indexOf(q) !== -1;
                });
                currentPage = 1;
                render();
            });
        }

        /* ---- sorting ---- */
        var headers = table.querySelectorAll("thead th.sortable");
        Array.prototype.forEach.call(headers, function (th, i) {
            th.addEventListener("click", function () {
                var type = th.getAttribute("data-key");

                if (sortState.index === i) {
                    sortState.dir *= -1;
                } else {
                    sortState.index = i;
                    sortState.dir = 1;
                }

                Array.prototype.forEach.call(headers, function (h) {
                    h.classList.remove("sort-asc", "sort-desc");
                });
                th.classList.add(sortState.dir === 1 ? "sort-asc" : "sort-desc");

                filtered.sort(function (a, b) {
                    var av = a.children[i].getAttribute("data-sort") || "";
                    var bv = b.children[i].getAttribute("data-sort") || "";
                    if (type === "num") {
                        return (parseFloat(av) - parseFloat(bv)) * sortState.dir;
                    }
                    return av.localeCompare(bv) * sortState.dir;
                });

                currentPage = 1;
                render();
            });
        });

        render();
    }

    /* ------------------------------------------------------------------ */
    /*  Delete confirmation                                                */
    /* ------------------------------------------------------------------ */
    function initDeleteConfirm() {
        var forms = document.querySelectorAll(".delete-form");
        Array.prototype.forEach.call(forms, function (form) {
            form.addEventListener("submit", function (e) {
                if (!window.confirm("Delete this report? This cannot be undone.")) {
                    e.preventDefault();
                }
            });
        });
    }

    /* ------------------------------------------------------------------ */
    /*  Boot                                                               */
    /* ------------------------------------------------------------------ */
    document.addEventListener("DOMContentLoaded", function () {
        initTheme();
        initServerToasts();
        initUpload();
        initTable();
        initDeleteConfirm();
    });
})();
