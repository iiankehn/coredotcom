// Northline uses only a small amount of vanilla JavaScript.
// This controls the mobile navigation.

const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#site-nav");

if (menuButton && navigation) {
    menuButton.addEventListener("click", () => {
        const isOpen = navigation.classList.toggle("open");

        menuButton.setAttribute("aria-expanded", String(isOpen));
        menuButton.querySelector(".sr-only").textContent =
            isOpen ? "Close menu" : "Open menu";
    });

    navigation.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            navigation.classList.remove("open");
            menuButton.setAttribute("aria-expanded", "false");
            menuButton.querySelector(".sr-only").textContent = "Open menu";
        });
    });
}
