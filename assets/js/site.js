const menuButton = document.querySelector("#mobile-menu-button");
const navigation = document.querySelector("#nav-menu");
const compactHeader = window.matchMedia("(width < 72rem)");

function setMenuOpen(open) {
    menuButton.setAttribute("aria-expanded", String(open));
    navigation.hidden = compactHeader.matches && !open;
}

function updateMenuLayout() {
    const focusedInNav = navigation.contains(document.activeElement);
    const focusedOnButton = document.activeElement === menuButton;

    menuButton.hidden = !compactHeader.matches;
    setMenuOpen(false);

    if (compactHeader.matches && focusedInNav) {
        menuButton.focus();
    }

    if (!compactHeader.matches && focusedOnButton) {
        (navigation.querySelector("[aria-current='page']") ?? navigation.querySelector("a")).focus();
    }
}

menuButton.addEventListener("click", () => {
    setMenuOpen(menuButton.getAttribute("aria-expanded") === "false");
});

document.querySelector(".site-header").addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
        setMenuOpen(false);
        menuButton.focus();
    }
});

compactHeader.addEventListener("change", updateMenuLayout);
updateMenuLayout();
