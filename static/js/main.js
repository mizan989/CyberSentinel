// CyberSentinel - shared frontend helpers
// Page-specific logic (scan progress polling, report charts) lives in the
// respective templates' {% block scripts %}. This file holds small
// utilities shared across pages.

document.addEventListener("DOMContentLoaded", function () {
  // Enable Bootstrap tooltips globally, if any are present.
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach((el) => new bootstrap.Tooltip(el));
});
