/* ==========================================================================
   SNEAKER PULSE COMMAND CENTER - 3D CARD TILT INTERACTION
   ========================================================================== */

function initCardTilt(cardElement) {
  if (!cardElement || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  cardElement.addEventListener("mousemove", (e) => {
    const rect = cardElement.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -8;
    const rotateY = ((x - centerX) / centerX) * 8;

    cardElement.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
  });

  cardElement.addEventListener("mouseleave", () => {
    cardElement.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)";
  });
}
