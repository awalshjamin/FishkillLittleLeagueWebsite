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

const registrationStatuses = document.querySelectorAll("[data-registration-deadline]");

if (registrationStatuses.length) {
    const easternDate = new Intl.DateTimeFormat("en-US", {
        timeZone: "America/New_York",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    });

    function updateRegistrationDeadlines() {
        const parts = Object.fromEntries(
            easternDate.formatToParts(new Date()).map(({ type, value }) => [type, value])
        );
        const today = `${parts.year}-${parts.month}-${parts.day}`;

        for (const status of registrationStatuses) {
            if (today <= status.dataset.registrationDeadline) continue;

            const label = status.querySelector("strong");
            label.textContent = status.dataset.closedLabel;

            for (const link of document.querySelectorAll(
                `[data-registration-link="${status.dataset.registrationStatus}"]`
            )) {
                if (link.tagName === "A") {
                    const replacement = document.createElement("span");
                    replacement.textContent = link.dataset.closedLabel ?? link.textContent;
                    link.replaceWith(replacement);
                } else {
                    link.remove();
                }
            }
        }
    }

    updateRegistrationDeadlines();
    window.addEventListener("pageshow", updateRegistrationDeadlines);
    window.setInterval(updateRegistrationDeadlines, 60_000);
}
