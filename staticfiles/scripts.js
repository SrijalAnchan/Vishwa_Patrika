document.addEventListener("mousemove", function(e) {
    let cursor = document.querySelector(".cursor");
    cursor.style.left = e.pageX + "px";
    cursor.style.top = e.pageY + "px";
});

/* Glow effect on hover */
document.querySelectorAll("button").forEach(button => {
    button.addEventListener("mouseenter", () => {
        document.querySelector(".cursor").classList.add("hover");
    });
    button.addEventListener("mouseleave", () => {
        document.querySelector(".cursor").classList.remove("hover");
    });
});
