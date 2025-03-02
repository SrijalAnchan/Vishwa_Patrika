document.addEventListener("DOMContentLoaded", function () {
    // Create custom cursor
    let cursor = document.createElement("div");
    cursor.classList.add("cursor");
    document.body.appendChild(cursor);
    
    // Follow mouse movement
    document.addEventListener("mousemove", function (e) {
        cursor.style.left = (e.clientX - 15) + "px";  
        cursor.style.top = (e.clientY - 15) + "px";
    });
    
    // Enhanced button hover effects
    document.querySelectorAll(".btn-custom, .button-hover-effect").forEach(button => {
        button.addEventListener("mouseenter", () => {
            // Keep the original gradient but add transform and shadow effects
            cursor.style.transform = "scale(2.5)";
            cursor.style.boxShadow = "0 0 30px rgba(46, 139, 87, 0.7)";
        });
        
        button.addEventListener("mouseleave", () => {
            cursor.style.transform = "scale(1.5)";
            cursor.style.boxShadow = "0 0 25px rgba(46, 139, 87, 0.5)";
        });
    });
    
    // Add hover effects for navbar links
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("mouseenter", () => {
            cursor.style.transform = "scale(2)";
            cursor.style.boxShadow = "0 0 25px rgba(218, 165, 32, 0.6)";
        });
        
        link.addEventListener("mouseleave", () => {
            cursor.style.transform = "scale(1.5)";
            cursor.style.boxShadow = "0 0 25px rgba(46, 139, 87, 0.5)";
        });
    });
    
    // Make cursor smaller when on text
    document.querySelectorAll("p, h1, h2, h3, h4, h5, h6").forEach(text => {
        text.addEventListener("mouseenter", () => {
            cursor.style.transform = "scale(0.8)";
        });
        
        text.addEventListener("mouseleave", () => {
            cursor.style.transform = "scale(1.5)";
        });
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Add fade-out animation
            alert.style.opacity = '0';
            
            // Remove the alert from DOM after fade-out completes
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 700); // Match fadeIn animation duration
        }, 5000); // Show for 5 seconds
    });
    
    // Add active class to current nav item based on URL
    const currentLocation = window.location.href;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.href === currentLocation) {
            link.classList.add('active');
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});