/* =====================================================
   CHECKOUT.JS
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {

  /* =======================
     Helpers
     ======================= */
  const parsePrice = (str) => {
    if (!str) return 0;
    const num = parseFloat(str); 
    return isNaN(num) ? 0 : num;
  };

  const money = (n) => parsePrice(n).toFixed(2);

  /* =======================
     Elementos del resumen
     ======================= */
  const subtotalEl = document.getElementById("subtotal-text");
  const shippingEl = document.getElementById("shipping-cost-text");
  const totalEl = document.getElementById("total-text");

  /* =======================
     Entrega
     ======================= */
  const deliveryPickup = document.getElementById("id_delivery_mode_0"); // Asegúrate que este ID coincida con el input generado por Django
  const deliveryHome = document.getElementById("id_delivery_mode_1");
  const zoneWrapper = document.getElementById("shipping-zone-wrapper");
  const zoneSelect = document.getElementById("id_shipping_zone");
  const addressInput = document.getElementById("id_customer_address");
  const storeAddress = document.getElementById("store-address");
  const badgeDelivery = document.getElementById("badgeDelivery");

  /* =======================
     Pago
     ======================= */
  const paySelect = document.getElementById("id_payment_method");
  const payTransfer = document.getElementById("pay-transferencia");
  const payContra = document.getElementById("pay-contraentrega");
  const payEmpty = document.getElementById("pay-empty");
  const btnWhatsapp = document.getElementById("btnWhatsapp");

  /* =======================
      Subtotal REAL
     ======================= */
  // Ahora tomamos el dato limpio directamente
  const FIXED_SUBTOTAL = subtotalEl ? parsePrice(subtotalEl.dataset.subtotal) : 0;

  /* =======================
     Obtener costo envío desde zona
     ======================= */
  function getShippingCost() {
    if (!deliveryHome?.checked) return 0;
    if (!zoneSelect || !zoneSelect.value) return 0;
    const opt = zoneSelect.options[zoneSelect.selectedIndex];
    return parsePrice(opt?.dataset.cost);
  }

  /* =======================
     Actualizar resumen
     ======================= */
  function updateSummary() {
    const shipping = getShippingCost();
    const total = FIXED_SUBTOTAL + shipping;
    if (shippingEl) shippingEl.textContent = money(shipping);
    if (totalEl) totalEl.textContent = money(total);
  }

  /* =======================
     UI Entrega
     ======================= */
  function updateDeliveryUI() {
    const isPickup = deliveryPickup?.checked;
    const isDelivery = deliveryHome?.checked;

    if (zoneWrapper) zoneWrapper.style.display = isDelivery ? "" : "none";

    if (addressInput) {
      const wrapper = addressInput.closest(".col-12");
      if (wrapper) wrapper.style.display = isDelivery ? "" : "none";
    }

    if (storeAddress) {
      storeAddress.classList.toggle("d-none", !isPickup);
    }

    if (badgeDelivery) {
      badgeDelivery.textContent = isPickup ? "Retiro" : "Envío";
    }


    if (isPickup && zoneSelect) {
        zoneSelect.classList.remove("is-invalid");
    }

    updateSummary();
  }

  /* =======================
     UI Pago
     ======================= */
  function updatePaymentUI() {
    if (!paySelect) return;

    payTransfer?.classList.add("d-none");
    payContra?.classList.add("d-none");
    payEmpty?.classList.add("d-none");

    const val = paySelect.value;

    if (val === "transferencia") {
      payTransfer?.classList.remove("d-none");
      const totalText = totalEl ? totalEl.textContent : "0.00";
      const msg = encodeURIComponent(
        `Hola, realicé un pedido por $${totalText} y adjunto el comprobante de transferencia.`
      );
      if(btnWhatsapp) btnWhatsapp.href = `https://wa.me/593999519375?text=${msg}`;

    } else if (val === "contraentrega") {
      payContra?.classList.remove("d-none");
    } else {
      payEmpty?.classList.remove("d-none");
    }
  }

  /* =======================
     Eventos
     ======================= */
  const radios = document.querySelectorAll('input[name="delivery_mode"]');
  radios.forEach(radio => radio.addEventListener("change", updateDeliveryUI));

  zoneSelect?.addEventListener("change", updateSummary);
  paySelect?.addEventListener("change", updatePaymentUI);

  /* =======================
     Inicialización
     ======================= */
  updateDeliveryUI();
  updatePaymentUI();
});