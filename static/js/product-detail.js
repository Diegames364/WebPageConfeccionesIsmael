document.addEventListener("DOMContentLoaded", () => {
  /* ================= REFERENCIAS ================= */
  const variantSelect = document.getElementById("variantSelect");
  const priceText = document.getElementById("priceText");
  const lineTotalText = document.getElementById("lineTotalText");
  const stockHint = document.getElementById("stockHint");
  const mainImg = document.getElementById("mainImg");
  const thumbBtns = document.querySelectorAll(".thumb-btn");
  const addBtn = document.getElementById("addBtn");

  const qtyInput = document.getElementById("qtyInput");
  const btnPlus = document.getElementById("btnPlus");
  const btnMinus = document.getElementById("btnMinus");

  // Referencias para COLOR
  const colorDisplay = document.getElementById("colorDisplay");
  const colorNameEl = document.getElementById("colorName");
  const colorDotEl = document.getElementById("colorDot");

  let currentStock = 0;
  let currentPrice = 0.0;

  /* ================= FUNCIÓN PRINCIPAL ================= */
  function updateUI() {
    if (!variantSelect) return;

    const opt = variantSelect.options[variantSelect.selectedIndex];
    if (!opt) return;

    // Datos básicos
    const rawPrice = opt.dataset.price || "0";
    currentPrice = parseFloat(rawPrice.replace(',', '.')) || 0;
    currentStock = parseInt(opt.dataset.stock) || 0;
    const variantImage = opt.dataset.image;

    // --- LÓGICA DE COLOR ---
    const colorName = opt.dataset.color;
    const colorHex = opt.dataset.hex;

    if (colorDisplay) {
        if (colorName && colorName.trim() !== "") {
            colorDisplay.classList.remove("d-none");
            colorDisplay.classList.add("d-flex"); 
            
            if(colorNameEl) colorNameEl.textContent = colorName;
            if(colorDotEl) colorDotEl.style.backgroundColor = colorHex || "#ccc";
        } else {
            colorDisplay.classList.add("d-none");
            colorDisplay.classList.remove("d-flex");
        }
    }

    // Validar cantidad
    let qty = parseInt(qtyInput.value) || 1;
    if (currentStock > 0 && qty > currentStock) {
        qty = currentStock;
        qtyInput.value = qty;
    }

    // Actualizar Precios
    const total = currentPrice * qty;
    if (priceText) priceText.textContent = currentPrice.toFixed(2);
    if (lineTotalText) lineTotalText.textContent = total.toFixed(2);

    // Actualizar Stock y Botones
    if (stockHint) {
      if (currentStock <= 0) {
        stockHint.innerHTML = `<i class="bi bi-x-circle-fill text-danger"></i> <span class="text-danger fw-medium">Agotado</span>`;
        if(addBtn) addBtn.disabled = true;
        if(qtyInput) qtyInput.disabled = true;
      } else if (currentStock < 5) {
        stockHint.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-warning"></i> <span class="text-warning fw-medium">¡Solo quedan ${currentStock} unidades!</span>`;
        if(addBtn) addBtn.disabled = false;
        if(qtyInput) qtyInput.disabled = false;
      } else {
        stockHint.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i> <span class="text-success fw-medium">Disponible (${currentStock} en stock)</span>`;
        if(addBtn) addBtn.disabled = false;
        if(qtyInput) qtyInput.disabled = false;
      }
    }
    updateQuantityButtonsState(qty);

    // Actualizar Imagen
    if (variantImage && mainImg) {
      setMainImage(variantImage);
    }
  }

  function setMainImage(src) {
      if (!mainImg || mainImg.src === src) return;
      mainImg.style.opacity = '0.5';
      setTimeout(() => {
          mainImg.src = src;
          mainImg.style.opacity = '1';
      }, 150);
  }

  function updateQuantityButtonsState(currentQty) {
      if(!btnMinus || !btnPlus) return;
      btnMinus.disabled = currentQty <= 1;
      btnPlus.disabled = (currentStock > 0 && currentQty >= currentStock);
  }

  /* ================= LISTENERS ================= */
  if (variantSelect) variantSelect.addEventListener("change", updateUI);

  if (qtyInput) {
    qtyInput.addEventListener("input", function() {
        let val = parseInt(this.value);
        if (isNaN(val) || val < 1) val = 1;
        if (currentStock > 0 && val > currentStock) val = currentStock;
        if (val !== parseInt(this.value)) this.value = val;
        updateUI();
    });
    qtyInput.addEventListener("blur", function() {
        if(!this.value) this.value = 1;
        updateUI();
    });
  }

  if (btnPlus) {
      btnPlus.addEventListener("click", () => {
          let qty = parseInt(qtyInput.value) || 1;
          if (currentStock === 0 || qty < currentStock) {
              qtyInput.value = qty + 1;
              updateUI();
          }
      });
  }
  if (btnMinus) {
      btnMinus.addEventListener("click", () => {
          let qty = parseInt(qtyInput.value) || 1;
          if (qty > 1) {
              qtyInput.value = qty - 1;
              updateUI();
          }
      });
  }

  thumbBtns.forEach((btn) => {
    btn.addEventListener("click", function() {
      const src = this.dataset.src;
      setMainImage(src);
      thumbBtns.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
    });
  });

  const firstThumb = thumbBtns[0];
  if (firstThumb) {
      thumbBtns.forEach(t => t.classList.remove('active'));
      firstThumb.classList.add('active');
  }

  // INICIALIZAR
  updateUI();
});