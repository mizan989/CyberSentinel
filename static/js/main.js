/**
 * CyberSentinel — Claymorphism + Inspira UI + Watermelon UI Engine
 * Features: Lenis Smooth Scrolling, Spotlight Illumination, Ripple Tags, Shortcut (Ctrl+K)
 */

document.addEventListener("DOMContentLoaded", function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --------------------------------------------------------------------------
  // 1. Lenis Ultra-Smooth Inertia Scrolling Engine
  // --------------------------------------------------------------------------
  let lenisInstance = null;
  if (typeof Lenis !== "undefined" && !prefersReducedMotion) {
    lenisInstance = new Lenis({
      duration: 1.25,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Exponential deceleration
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 2.0,
      infinite: false,
    });

    function raf(time) {
      lenisInstance.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
    window.lenis = lenisInstance;

    // Connect Lenis scroll events to sticky header shadow
    const navbar = document.querySelector(".cs-navbar");
    if (navbar) {
      lenisInstance.on("scroll", ({ scroll }) => {
        if (scroll > 20) {
          navbar.style.boxShadow = "0 14px 35px -5px rgba(80, 60, 45, 0.12), inset 3px 3px 6px rgba(255, 255, 255, 0.95), inset -3px -3px 8px rgba(103, 162, 197, 0.12)";
        } else {
          navbar.style.boxShadow = "0 10px 30px -5px rgba(80, 60, 45, 0.08), inset 3px 3px 6px rgba(255, 255, 255, 0.95), inset -3px -3px 8px rgba(103, 162, 197, 0.08)";
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // 2. Inspira UI Dynamic Spotlight Cursor Tracker
  // --------------------------------------------------------------------------
  const spotlightCards = document.querySelectorAll(".spotlight-card, .cs-card, .cs-profile-card, .cs-vuln-card");
  spotlightCards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });

  // --------------------------------------------------------------------------
  // 3. Viewport Scroll Reveal Observers (Spring Transitions)
  // --------------------------------------------------------------------------
  const animateElements = document.querySelectorAll("[data-animate]");
  if (animateElements.length > 0) {
    const observerOptions = {
      root: null,
      rootMargin: "0px 0px -50px 0px",
      threshold: 0.05,
    };

    const animateObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animated");
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    animateElements.forEach((el) => animateObserver.observe(el));
  }

  // --------------------------------------------------------------------------
  // 4. Animated Number Counters
  // --------------------------------------------------------------------------
  const counterElements = document.querySelectorAll(".cs-counter");
  if (counterElements.length > 0) {
    const counterObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const targetValue = parseInt(el.getAttribute("data-target"), 10) || 0;
          const duration = 1200;
          const startTime = performance.now();

          function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentCount = Math.floor(easeOut * targetValue);
            el.textContent = currentCount.toLocaleString();

            if (progress < 1) {
              requestAnimationFrame(updateCounter);
            } else {
              el.textContent = targetValue.toLocaleString();
            }
          }

          requestAnimationFrame(updateCounter);
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.2 });

    counterElements.forEach((el) => counterObserver.observe(el));
  }

  // --------------------------------------------------------------------------
  // 5. Watermelon UI Keyboard Shortcut Listener (Ctrl+K / Cmd+K)
  // --------------------------------------------------------------------------
  window.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      const searchInput = document.querySelector("input[name='q'], #targetSelect, #subnetInput");
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        if (searchInput.select) searchInput.select();
      }
    }
  });

  // --------------------------------------------------------------------------
  // 6. Bootstrap Tooltips Initialization
  // --------------------------------------------------------------------------
  if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipEls.forEach((el) => new bootstrap.Tooltip(el));
  }
});
