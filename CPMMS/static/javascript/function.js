const activePage = window.location.pathname;
const navLinks = document.querySelectorAll('nav a');

navLinks.forEach(link => {
    const linkPath = new URL(link.href).pathname;
    if(linkPath === activePage) {
        link.classList.add('active');
    }
})