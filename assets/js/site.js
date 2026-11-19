document.addEventListener("DOMContentLoaded", () => {

    const button =
        document.getElementById("mobile-menu-button");

    const nav =
        document.getElementById("nav-menu");

    button.addEventListener("click", () => {
        nav.classList.toggle("show");
    });

});