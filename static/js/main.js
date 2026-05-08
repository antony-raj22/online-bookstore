/* ============================================================
   BookStore — main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Auto-hide alerts after 4s ─────────────────────────── */
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });

  /* ── Qty input validation ──────────────────────────────── */
  document.querySelectorAll('.qty-input').forEach(input => {
    input.addEventListener('change', function () {
      const val = parseInt(this.value);
      if (isNaN(val) || val < 0) this.value = 0;
      if (val > 99) this.value = 99;
    });
  });

  /* ── Navbar scroll shadow ──────────────────────────────── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  /* ── Newsletter form ───────────────────────────────────── */
  const newsletterForm = document.getElementById('newsletterForm');
  const msgDiv = document.getElementById('newsletterMsg');
  if (newsletterForm && msgDiv) {
    newsletterForm.addEventListener('submit', e => {
      e.preventDefault();
      const emailInput = newsletterForm.querySelector('.newsletter-input');
      if (emailInput.value.trim()) {
        msgDiv.innerHTML = '<span style="color:#d4edda;">✨ Thanks for subscribing! Check your inbox soon.</span>';
        emailInput.value = '';
        setTimeout(() => { msgDiv.innerHTML = ''; }, 4000);
      }
    });
  }

  /* ── Category cards ripple click ──────────────────────── */
  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', function () {
      this.style.transform = 'scale(0.97)';
      setTimeout(() => { this.style.transform = ''; }, 180);
    });
  });

  /* ── Add-to-cart feedback ──────────────────────────────── */
  document.querySelectorAll('a[href*="add_to_cart"]').forEach(btn => {
    btn.addEventListener('click', function () {
      const orig = this.textContent;
      this.textContent = '✓ Added!';
      this.style.background = '#2e7d32';
      this.style.color = 'white';
      setTimeout(() => {
        this.textContent = orig;
        this.style.background = '';
        this.style.color = '';
      }, 1400);
    });
  });

});