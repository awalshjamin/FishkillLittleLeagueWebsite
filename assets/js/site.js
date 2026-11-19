const menuButton = document.querySelector("#mobile-menu-button");
const navigation = document.querySelector("#nav-menu");
const compactHeader = window.matchMedia("(max-width: 67.499rem)");

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
        navigation.querySelector("[aria-current='page']").focus();
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
