/* =====================================================
   MAIN.JS
   Script principal del sitio
   ===================================================== */

/* ===============================
   Mini carrito
   =============================== */

/**
 * Actualiza el badge del carrito
 */
function setCartBadge(n) {
  const badge = document.getElementById("cartBadge");
  if (!badge) return;

  const val = parseInt(n || 0, 10);
  badge.textContent = val;
  badge.classList.toggle("d-none", val <= 0);
}

/**
 * Aplica pequeñas animaciones a los items del mini carrito
 */
function enhanceMiniCart(container) {
  if (!container) return;

  const items = container.querySelectorAll(".mc2-item, .mini-cart-item");
  items.forEach((el, idx) => {
    el.style.animationDelay = `${Math.min(idx, 10) * 45}ms`;
  });
}

/**
 * Carga/recarga el contenido del mini carrito
 */
async function refreshMiniCart() {
  const body = document.getElementById("miniCartBody");

  if (body) {
    body.innerHTML = `<div class="text-muted small p-3">Cargando…</div>`;
  }

  try {
    if (!window.CART_SUMMARY_URL) {
      console.warn("CART_SUMMARY_URL no está definida");
      return;
    }

    const res = await fetch(window.CART_SUMMARY_URL, {
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    });

    if (!res.ok) {
      if (body) {
        body.innerHTML = `
          <div class="text-danger small p-3">
            Error cargando carrito (${res.status})
          </div>`;
      }
      return;
    }

    const data = await res.json();

    if (!data.ok) {
      if (body) {
        body.innerHTML = `
          <div class="text-danger small p-3">
            No se pudo cargar el carrito
          </div>`;
      }
      return;
    }

    // Actualizar badge
    setCartBadge(data.cart_count);

    // Renderizar HTML del mini carrito
    if (body) {
      body.innerHTML =
        data.mini_cart_html ||
        "<div class='text-muted small p-3'>Carrito vacío</div>";
    }

    enhanceMiniCart(body);

  } catch (err) {
    console.error(err);
    if (body) {
      body.innerHTML = `
        <div class="text-danger small p-3">
          Error: respuesta inválida del servidor
        </div>`;
    }
  }
}

/* ===============================
   Eventos globales
   =============================== */

document.addEventListener("click", (e) => {
  const btn = e.target.closest("#btnCartCanvas");
  if (btn) {
    refreshMiniCart();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  refreshMiniCart();
});

/* =====================================================*/
/* =====================================================
   PRODUCT DETAIL
   ===================================================== */

/* ---------- util ---------- */
function formatMoneyDetail(n) {
  n = Number(n || 0);
  return n.toFixed(2);
}

/* ---------- galería ---------- */
document.querySelectorAll(".thumb").forEach(btn => {
  btn.addEventListener("click", () => {
    const src = btn.dataset.src;
    const main = document.getElementById("mainImg");
    if (!main || !src) return;

    main.classList.remove("fade-pop");
    main.style.opacity = "0.86";
    main.src = src;

    requestAnimationFrame(() => {
      main.style.opacity = "1";
      main.classList.add("fade-pop");
    });
  });
});

/* ---------- variante / precio ---------- */
const sel = document.getElementById("variantSelect");
const qty = document.getElementById("qtyInput");
const priceText = document.getElementById("priceText");
const lineTotalText = document.getElementById("lineTotalText");
const stockHint = document.getElementById("stockHint");
const addBtn = document.getElementById("addBtn");

function swapMainImage(url) {
  const main = document.getElementById("mainImg");
  if (!main || !url) return;

  const img = new Image();
  img.onload = () => {
    main.classList.remove("fade-pop");
    main.style.opacity = "0.86";
    main.src = url;
    requestAnimationFrame(() => {
      main.style.opacity = "1";
      main.classList.add("fade-pop");
    });
  };
  img.src = url;
}

function refreshDetail() {
  if (!sel) return;

  const opt = sel.options[sel.selectedIndex];
  const price = Number(opt?.dataset.price || 0);
  const stock = Number(opt?.dataset.stock || 0);

  let q = parseInt(qty?.value || "1", 10);
  if (isNaN(q) || q < 1) q = 1;
  if (stock > 0 && q > stock) q = stock;
  if (qty) qty.value = q;

  priceText.textContent = formatMoneyDetail(price);
  lineTotalText.textContent = formatMoneyDetail(price * q);

  if (stockHint) {
    if (stock <= 0) stockHint.textContent = "Sin stock en esta variante.";
    else if (stock <= 5) stockHint.textContent = `¡Últimas unidades! Stock disponible: ${stock}`;
    else stockHint.textContent = `Stock disponible: ${stock}`;
  }

  if (addBtn) {
    const disabled = stock <= 0;
    addBtn.disabled = disabled;
    addBtn.classList.toggle("disabled", disabled);
  }

  const imgUrl = opt?.dataset.image;
  if (imgUrl) swapMainImage(imgUrl);
}

if (sel) sel.addEventListener("change", refreshDetail);
if (qty) qty.addEventListener("input", refreshDetail);
refreshDetail();
/* =====================================================*/