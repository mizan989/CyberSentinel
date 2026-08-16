/**
 * CyberSentinel — Motion & Parallax Engine
 * Powered by Lenis Smooth Scroll & Viewport Observers
 */

document.addEventListener("DOMContentLoaded", function () {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --------------------------------------------------------------------------
  // 1. Lenis Smooth Scrolling Engine
  // --------------------------------------------------------------------------
  let lenisInstance = null;
  if (typeof Lenis !== "undefined" && !prefersReducedMotion) {
    lenisInstance = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1,
      touchMultiplier: 2,
    });

    function raf(time) {
      lenisInstance.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
    window.lenis = lenisInstance;
  }

  // --------------------------------------------------------------------------
  // 2. Parallax Scroll & Mouse Engine
  // --------------------------------------------------------------------------
  if (!prefersReducedMotion) {
    // Parallax Orbs Mouse & Scroll Tracking
    const orb1 = document.querySelector(".cs-orb-1");
    const orb2 = document.querySelector(".cs-orb-2");
    const orb3 = document.querySelector(".cs-orb-3");
    const parallaxLayers = document.querySelectorAll(".parallax-layer");

    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    window.addEventListener("mousemove", (e) => {
      targetMouseX = (e.clientX / window.innerWidth - 0.5) * 2; // -1 to 1
      targetMouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });

    function updateParallax() {
      // Smooth lerp mouse position
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      const scrollY = window.scrollY || 0;

      if (orb1) {
        const yOffset = scrollY * 0.15 + mouseY * 35;
        const xOffset = mouseX * 30;
        orb1.style.transform = `translate3d(${xOffset}px, ${yOffset}px, 0)`;
      }

      if (orb2) {
        const yOffset = -scrollY * 0.12 + mouseY * -25;
        const xOffset = mouseX * -25;
        orb2.style.transform = `translate3d(${xOffset}px, ${yOffset}px, 0)`;
      }

      if (orb3) {
        const yOffset = scrollY * 0.08 + mouseY * 20;
        const xOffset = mouseX * 20;
        orb3.style.transform = `translate3d(${xOffset}px, ${yOffset}px, 0)`;
      }

      // Parallax layers with data-speed
      parallaxLayers.forEach((layer) => {
        const speed = parseFloat(layer.getAttribute("data-speed")) || 0.1;
        const yOffset = scrollY * speed + (mouseY * speed * 20);
        layer.style.transform = `translate3d(0, ${yOffset}px, 0)`;
      });

      requestAnimationFrame(updateParallax);
    }

    requestAnimationFrame(updateParallax);
  }

  // --------------------------------------------------------------------------
  // 3. Viewport Scroll Reveal Observers
  // --------------------------------------------------------------------------
  const animateElements = document.querySelectorAll("[data-animate]");
  if (animateElements.length > 0) {
    const observerOptions = {
      root: null,
      rootMargin: "0px 0px -40px 0px",
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
  // 4. Card Spotlight Cursor Tracking
  // --------------------------------------------------------------------------
  const spotlightCards = document.querySelectorAll(".spotlight-card");
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
  // 5. Animated Number Counters
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
  // 6. Bootstrap Tooltips
  // --------------------------------------------------------------------------
  if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
    const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipEls.forEach((el) => new bootstrap.Tooltip(el));
  }
});
