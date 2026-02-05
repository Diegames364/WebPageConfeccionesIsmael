document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll('a[href="#featured"]');
  
  links.forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const target = document.querySelector("#featured");
      if (target) {
        target.scrollIntoView({
          behavior: "smooth"
        });
      }
    });
  });
});