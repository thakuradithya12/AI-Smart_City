(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const hasFinePointer = window.matchMedia("(pointer: fine)");
  if (prefersReducedMotion.matches || !hasFinePointer.matches || !document.body) return;

  let scheduled = false;
  let pointerX = 0;
  let pointerY = 0;
  const maximumShift = 8;

  window.addEventListener("pointermove", (event) => {
    if (event.pointerType !== "mouse" || scheduled) return;
    scheduled = true;
    pointerX = (event.clientX / window.innerWidth - 0.5) * maximumShift;
    pointerY = (event.clientY / window.innerHeight - 0.5) * maximumShift;
    window.requestAnimationFrame(() => {
      document.body.style.setProperty("--city-shift-x", `${pointerX}px`);
      document.body.style.setProperty("--city-shift-y", `${pointerY}px`);
      scheduled = false;
    });
  }, { passive: true });

  window.addEventListener("blur", () => {
    document.body.style.removeProperty("--city-shift-x");
    document.body.style.removeProperty("--city-shift-y");
  });
})();
