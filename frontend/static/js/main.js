/* ============================================================
   BookStore main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });

  const cartUpdateForm = document.getElementById('cartUpdateForm');
  const cartAutoStatus = document.getElementById('cartAutoStatus');
  const formatRupees = value => {
    const amount = Number.parseFloat(value || 0);
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };
  const setCartStatus = (message, isError = false) => {
    if (!cartAutoStatus) return;
    cartAutoStatus.textContent = message;
    cartAutoStatus.classList.toggle('is-error', isError);
  };
  const applyCartPayload = payload => {
    if (!payload || !Array.isArray(payload.items)) return;
    const seenBookIds = new Set();

    payload.items.forEach(item => {
      seenBookIds.add(String(item.book_id));
      const row = document.querySelector(`[data-cart-row="${item.book_id}"]`);
      const quantityInput = row ? row.querySelector('.qty-input') : null;
      const subtotal = document.querySelector(`[data-cart-subtotal="${item.book_id}"]`);
      if (quantityInput) quantityInput.value = item.quantity;
      if (subtotal) subtotal.textContent = formatRupees(item.subtotal);
    });

    document.querySelectorAll('[data-cart-row]').forEach(row => {
      if (!seenBookIds.has(row.dataset.cartRow)) row.remove();
    });

    const itemLabel = document.getElementById('cartItemsLabel');
    const itemAmount = document.getElementById('cartItemsAmount');
    const totalAmount = document.getElementById('cartTotalAmount');
    const navCount = document.querySelector('.cart-count');

    if (itemLabel) itemLabel.textContent = `Items (${payload.item_count})`;
    if (itemAmount) itemAmount.textContent = formatRupees(payload.total);
    if (totalAmount) totalAmount.textContent = formatRupees(payload.total);
    if (navCount) navCount.textContent = payload.item_count;
    if (payload.item_count === 0) window.location.reload();
  };
  let cartRefreshTimer = null;
  const refreshCart = () => {
    if (!cartUpdateForm || cartUpdateForm.dataset.autoRefresh !== 'true') return;
    window.clearTimeout(cartRefreshTimer);
    cartRefreshTimer = window.setTimeout(async () => {
      setCartStatus('Updating...');
      try {
        const response = await fetch(cartUpdateForm.action, {
          method: 'POST',
          body: new FormData(cartUpdateForm),
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          credentials: 'same-origin',
        });
        if (!response.ok) throw new Error('Cart update failed');
        applyCartPayload(await response.json());
        setCartStatus('Cart updated');
      } catch (error) {
        setCartStatus('Auto update failed. Use Update Cart.', true);
      }
    }, 500);
  };

  if (cartUpdateForm && cartUpdateForm.dataset.autoRefresh === 'true') {
    cartUpdateForm.addEventListener('submit', event => {
      event.preventDefault();
      refreshCart();
    });
  }

  document.querySelectorAll('.qty-input').forEach(input => {
    const normalizeQuantity = function () {
      const val = parseInt(this.value, 10);
      const max = parseInt(this.max, 10);
      if (isNaN(val) || val < 0) this.value = 0;
      if (!isNaN(max) && val > max) this.value = max;
    };

    input.addEventListener('input', refreshCart);
    input.addEventListener('change', function () {
      normalizeQuantity.call(this);
      refreshCart();
    });
  });

  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  const userBtn = document.getElementById('userMenuBtn');
  const userDrop = document.getElementById('userDropdown');
  if (userBtn && userDrop) {
    userBtn.addEventListener('click', event => {
      event.stopPropagation();
      userDrop.classList.toggle('open');
      userBtn.setAttribute('aria-expanded', userDrop.classList.contains('open'));
    });
    document.addEventListener('click', () => {
      userDrop.classList.remove('open');
      userBtn.setAttribute('aria-expanded', 'false');
    });
  }

  const newsletterForm = document.getElementById('newsletterForm');
  const msgDiv = document.getElementById('newsletterMsg');
  if (newsletterForm && msgDiv) {
    newsletterForm.addEventListener('submit', event => {
      event.preventDefault();
      const emailInput = newsletterForm.querySelector('.newsletter-input');
      if (emailInput.value.trim()) {
        msgDiv.textContent = 'Thanks for subscribing! Check your inbox soon.';
        msgDiv.classList.add('newsletter-msg-success');
        emailInput.value = '';
        setTimeout(() => {
          msgDiv.textContent = '';
          msgDiv.classList.remove('newsletter-msg-success');
        }, 4000);
      }
    });
  }

  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', function () {
      this.style.transform = 'scale(0.97)';
      setTimeout(() => { this.style.transform = ''; }, 180);
    });
  });

  document.querySelectorAll('.clickable-book').forEach(card => {
    card.addEventListener('click', event => {
      if (event.target.closest('a, button, input, select, textarea')) return;
      const href = card.dataset.href;
      if (href) window.location.href = href;
    });
    card.addEventListener('keydown', event => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      if (event.target.closest('a, button, input, select, textarea')) return;
      event.preventDefault();
      const href = card.dataset.href;
      if (href) window.location.href = href;
    });
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'link');
  });

  document.querySelectorAll('.pw-toggle').forEach(button => {
    button.addEventListener('click', function () {
      const input = document.getElementById(this.dataset.target);
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      this.innerHTML = isPassword
        ? '<i class="fa-solid fa-eye-slash"></i>'
        : '<i class="fa-solid fa-eye"></i>';
    });
  });

  const pw1 = document.getElementById('id_password1');
  const pwStrength = document.getElementById('pwStrength');
  const pwBar = document.getElementById('pwBar');
  const pwLabel = document.getElementById('pwLabel');
  if (pw1 && pwStrength && pwBar && pwLabel) {
    pw1.addEventListener('input', function () {
      const value = this.value;
      if (!value) {
        pwStrength.style.display = 'none';
        return;
      }

      pwStrength.style.display = 'flex';
      let score = 0;
      if (value.length >= 8) score++;
      if (/[A-Z]/.test(value)) score++;
      if (/[0-9]/.test(value)) score++;
      if (/[^A-Za-z0-9]/.test(value)) score++;

      const levels = ['Weak', 'Fair', 'Good', 'Strong'];
      const colors = ['#e53935', '#f4a93a', '#43a047', '#1976d2'];
      const widths = ['25%', '50%', '75%', '100%'];
      const index = Math.max(Math.min(score - 1, 3), 0);
      pwBar.style.width = widths[index];
      pwBar.style.background = colors[index];
      pwLabel.textContent = levels[index];
      pwLabel.style.color = colors[index];
    });
  }

  const modal = document.getElementById('appModal');
  const modalTitle = document.getElementById('appModalTitle');
  const modalText = document.getElementById('appModalText');
  const modalIcon = document.getElementById('appModalIcon');
  const modalConfirm = document.getElementById('appModalConfirm');
  let lastFocused = null;

  const closeModal = () => {
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
    if (lastFocused) lastFocused.focus();
  };

  const openModal = trigger => {
    if (!modal || !modalTitle || !modalText || !modalIcon || !modalConfirm) return;
    lastFocused = trigger;
    modalTitle.textContent = trigger.dataset.modalTitle || 'Confirm action';
    modalText.textContent = trigger.dataset.modalText || 'Are you sure you want to continue?';
    modalConfirm.textContent = trigger.dataset.modalConfirm || 'Continue';
    modalConfirm.href = trigger.href;
    modalIcon.innerHTML = `<i class="fa-solid ${trigger.dataset.modalIcon || 'fa-circle-info'}"></i>`;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    modalConfirm.focus();
  };

  document.querySelectorAll('[data-modal-title]').forEach(trigger => {
    trigger.addEventListener('click', event => {
      if (!trigger.href) return;
      event.preventDefault();
      openModal(trigger);
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(closeButton => {
    closeButton.addEventListener('click', closeModal);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeModal();
  });
});
