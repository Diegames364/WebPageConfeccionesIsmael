document.addEventListener("DOMContentLoaded", () => {
    
    /* 1. APARIENCIA BOOTSTRAP */
    const inputs = document.querySelectorAll("input, textarea, select");
    inputs.forEach(el => {
        if (!el.classList.contains("form-check-input")) {
            el.classList.add("form-control");
        }
    });

    /* 2. VALIDACIÓN DE ERRORES */
    const errors = document.querySelectorAll(".invalid-feedback");
    errors.forEach(err => {
        if (err.textContent.trim() !== "") {
            const wrapper = err.closest(".mb-3") || err.parentElement;
            if (wrapper) {
                const input = wrapper.querySelector("input, textarea, select");
                if (input) {
                    input.classList.add("is-invalid");
                    err.classList.add("d-block");
                }
            }
        }
    });

    /* 3. TOGGLE PASSWORD (Mostrar/Ocultar contraseña) */
    const toggleBtns = document.querySelectorAll("[data-toggle-pw]");
    
    toggleBtns.forEach(btn => {
        btn.addEventListener("click", function() {
            const targetSelector = this.getAttribute("data-toggle-pw");
            const input = document.querySelector(targetSelector);
            const icon = this.querySelector("i");

            if (input) {
                if (input.type === "password") {
                    input.type = "text";
                    if(icon) {
                        icon.classList.remove("bi-eye");
                        icon.classList.add("bi-eye-slash");
                    }
                } else {
                    input.type = "password";
                    if(icon) {
                        icon.classList.remove("bi-eye-slash");
                        icon.classList.add("bi-eye");
                    }
                }
            }
        });
    });
}); 