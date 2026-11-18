document.addEventListener("DOMContentLoaded", () => {
  const menu = document.querySelector(".nav-menu");
  const button = document.querySelector(".nav-menu-button");
  if (!menu || !button) return;

  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    menu.classList.toggle("is-open", !expanded);
  });

  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) {
      button.setAttribute("aria-expanded", "false");
      menu.classList.remove("is-open");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      button.setAttribute("aria-expanded", "false");
      menu.classList.remove("is-open");
      button.focus();
    }
  });
});
