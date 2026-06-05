/* ============================================================
   BookStore main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('themeToggle');
  const applyTheme = theme => {
    const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = normalizedTheme;
    if (!themeToggle) return;
    const isDark = normalizedTheme === 'dark';
    themeToggle.innerHTML = `<i class="fa-solid ${isDark ? 'fa-sun' : 'fa-moon'}"></i>`;
    themeToggle.setAttribute('aria-label', `Switch to ${isDark ? 'light' : 'dark'} theme`);
    themeToggle.setAttribute('title', `${isDark ? 'Light' : 'Dark'} theme`);
  };

  if (themeToggle) {
    const currentTheme = document.documentElement.dataset.theme || 'light';
    applyTheme(currentTheme);
    themeToggle.addEventListener('click', () => {
      const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('bookstore:theme', nextTheme);
      applyTheme(nextTheme);
    });
  }

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

  const footerPolicyPanel = document.getElementById('footer-policy-panel');
  const footerPolicyLinks = document.querySelectorAll('[data-footer-policy-target]');
  const footerPolicyItems = document.querySelectorAll('[data-footer-policy-content]');
  footerPolicyLinks.forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      const targetId = link.dataset.footerPolicyTarget;
      if (!footerPolicyPanel || !targetId) return;

      footerPolicyPanel.hidden = false;
      footerPolicyLinks.forEach(item => item.classList.toggle('is-active', item === link));
      footerPolicyItems.forEach(item => {
        item.classList.toggle('is-active', item.id === targetId);
      });
      footerPolicyPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', function () {
      this.style.transform = 'scale(0.97)';
      setTimeout(() => { this.style.transform = ''; }, 180);
    });
  });

  const heroRotator = document.querySelector('[data-hero-rotator]');
  if (heroRotator) {
    const heroImages = (heroRotator.dataset.heroImages || '')
      .split('|')
      .map(src => src.trim())
      .filter(Boolean);
    const interval = Number.parseInt(heroRotator.dataset.heroInterval || '15000', 10);
    let heroIndex = 0;

    if (heroImages.length > 1) {
      heroImages.slice(1).forEach(src => {
        const image = new Image();
        image.src = src;
      });

      window.setInterval(() => {
        heroIndex = (heroIndex + 1) % heroImages.length;
        heroRotator.classList.add('is-changing');
        window.setTimeout(() => {
          heroRotator.src = heroImages[heroIndex];
          heroRotator.classList.remove('is-changing');
        }, 260);
      }, Number.isFinite(interval) && interval > 0 ? interval : 15000);
    }
  }

  const wishlistKey = 'bookstore:wishlist';
  const wishlistButtons = document.querySelectorAll('.wishlist-toggle');
  const wishlistCount = document.getElementById('wishlistCount');
  const savedShelf = document.getElementById('savedShelf');
  const savedBookRow = document.getElementById('savedBookRow');
  const clearSavedBooks = document.getElementById('clearSavedBooks');
  const bookCards = document.querySelectorAll('.book-card[data-book-id]');
  const bookFilterButtons = document.querySelectorAll('[data-book-filter]');
  const bookFilterCount = document.getElementById('bookFilterCount');
  const bookFilterEmpty = document.getElementById('bookFilterEmpty');
  let activeBookFilter = 'all';
  const getWishlist = () => {
    try {
      return JSON.parse(localStorage.getItem(wishlistKey) || '[]');
    } catch (error) {
      return [];
    }
  };
  const saveWishlist = items => {
    localStorage.setItem(wishlistKey, JSON.stringify(items));
  };
  const savedBookFromButton = button => ({
    id: String(button.dataset.bookId),
    title: button.dataset.bookTitle || 'Saved book',
    author: button.dataset.bookAuthor || '',
    price: button.dataset.bookPrice || '',
    cover: button.dataset.bookCover || '',
    url: button.dataset.bookUrl || '#',
  });
  const renderSavedShelf = () => {
    if (!savedShelf || !savedBookRow) return;
    const saved = getWishlist().slice(0, 8);
    savedBookRow.innerHTML = '';
    savedShelf.hidden = saved.length === 0;

    saved.forEach(book => {
      const card = document.createElement('a');
      card.className = 'saved-book-card';
      card.href = book.url || '#';

      const image = document.createElement('img');
      image.src = book.cover || 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=190&h=240&fit=crop';
      image.alt = book.title || 'Book cover';

      const text = document.createElement('span');
      const title = document.createElement('strong');
      title.textContent = book.title || 'Saved book';
      const author = document.createElement('small');
      author.textContent = book.author || 'Saved for later';
      const price = document.createElement('em');
      price.textContent = book.price || 'View book';

      text.append(title, author, price);
      card.append(image, text);
      savedBookRow.appendChild(card);
    });
  };
  const updateWishlistUI = () => {
    const saved = getWishlist();
    const savedIds = new Set(saved.map(item => String(item.id)));
    if (wishlistCount) wishlistCount.textContent = saved.length;

    wishlistButtons.forEach(button => {
      const isSaved = savedIds.has(String(button.dataset.bookId));
      button.classList.toggle('is-saved', isSaved);
      button.setAttribute('aria-label', `${isSaved ? 'Remove' : 'Save'} ${button.dataset.bookTitle}`);
      if (button.classList.contains('icon-action')) {
        button.innerHTML = `<i class="${isSaved ? 'fa-solid' : 'fa-regular'} fa-heart"></i>`;
      } else {
        button.innerHTML = `<i class="${isSaved ? 'fa-solid' : 'fa-regular'} fa-heart"></i> ${isSaved ? 'Saved' : 'Save Book'}`;
      }
    });
    renderSavedShelf();
  };

  const applyBookFilter = filter => {
    activeBookFilter = filter || 'all';
    const savedIds = new Set(getWishlist().map(item => String(item.id)));
    let visibleCount = 0;

    bookCards.forEach(card => {
      const isNew = card.dataset.bookNew === 'true';
      const inStock = Number.parseInt(card.dataset.bookStock || '0', 10) > 0;
      const isSaved = savedIds.has(String(card.dataset.bookId));
      const shouldShow =
        activeBookFilter === 'all' ||
        (activeBookFilter === 'new' && isNew) ||
        (activeBookFilter === 'stock' && inStock) ||
        (activeBookFilter === 'saved' && isSaved);

      card.hidden = !shouldShow;
      if (shouldShow) visibleCount += 1;
    });

    bookFilterButtons.forEach(button => {
      button.classList.toggle('is-active', button.dataset.bookFilter === activeBookFilter);
    });

    if (bookFilterCount) {
      bookFilterCount.textContent = `${visibleCount} book${visibleCount === 1 ? '' : 's'}`;
    }
    if (bookFilterEmpty) {
      bookFilterEmpty.hidden = visibleCount !== 0;
    }
  };

  wishlistButtons.forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      const saved = getWishlist();
      const id = String(button.dataset.bookId);
      const existing = saved.findIndex(item => String(item.id) === id);
      if (existing >= 0) {
        saved.splice(existing, 1);
      } else {
        saved.push(savedBookFromButton(button));
      }
      saveWishlist(saved);
      updateWishlistUI();
      applyBookFilter(activeBookFilter);
    });
  });
  clearSavedBooks?.addEventListener('click', () => {
    saveWishlist([]);
    updateWishlistUI();
    applyBookFilter(activeBookFilter);
  });
  updateWishlistUI();

  bookFilterButtons.forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      applyBookFilter(button.dataset.bookFilter || 'all');
    });
  });
  applyBookFilter(activeBookFilter);

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

  document.querySelectorAll('.quick-view').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      if (!modal || !modalTitle || !modalText || !modalIcon || !modalConfirm) return;
      lastFocused = button;
      modalTitle.textContent = button.dataset.bookTitle || 'Book preview';
      modalText.innerHTML = `
        <span class="quick-view-meta">${button.dataset.bookGenre || 'Book'} by ${button.dataset.bookAuthor || 'Unknown author'}</span>
        <strong class="quick-view-price">${button.dataset.bookPrice || ''}</strong>
        <span class="quick-view-stock">${button.dataset.bookStock || ''}</span>
      `;
      modalIcon.innerHTML = '<i class="fa-solid fa-book-open"></i>';
      modalConfirm.textContent = 'View Details';
      modalConfirm.href = button.dataset.bookUrl || '#';
      modal.classList.add('open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      modalConfirm.focus();
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(closeButton => {
    closeButton.addEventListener('click', closeModal);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeModal();
  });

  const recentKey = 'bookstore:recentlyViewed';
  const readRecentBooks = () => {
    try {
      const books = JSON.parse(localStorage.getItem(recentKey) || '[]');
      return Array.isArray(books) ? books : [];
    } catch (error) {
      return [];
    }
  };
  const writeRecentBooks = books => {
    localStorage.setItem(recentKey, JSON.stringify(books.slice(0, 6)));
  };
  const detailBook = document.querySelector('[data-detail-book-id]');
  if (detailBook) {
    const book = {
      id: String(detailBook.dataset.detailBookId),
      title: detailBook.dataset.detailBookTitle || 'Book',
      author: detailBook.dataset.detailBookAuthor || '',
      price: detailBook.dataset.detailBookPrice || '',
      cover: detailBook.dataset.detailBookCover || '',
      url: detailBook.dataset.detailBookUrl || window.location.pathname,
    };
    const existing = readRecentBooks().filter(item => String(item.id) !== book.id);
    writeRecentBooks([book, ...existing]);
  }

  const recentSection = document.getElementById('recentlyViewed');
  const recentRow = document.getElementById('recentBookRow');
  if (recentSection && recentRow) {
    const recentBooks = readRecentBooks().filter(item => item && item.id).slice(0, 4);
    if (recentBooks.length) {
      recentRow.innerHTML = '';
      recentBooks.forEach(book => {
        const link = document.createElement('a');
        link.className = 'recent-book-card';
        link.href = book.url || '#';

        const image = document.createElement('img');
        image.src = book.cover || 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=190&h=240&fit=crop';
        image.alt = book.title || 'Book cover';

        const text = document.createElement('span');
        const title = document.createElement('strong');
        title.textContent = book.title || 'Book';
        const author = document.createElement('small');
        author.textContent = book.author || '';
        const price = document.createElement('em');
        price.textContent = book.price || '';

        text.append(title, author, price);
        link.append(image, text);
        recentRow.appendChild(link);
      });
      recentSection.hidden = false;
    }
  }

  const deliveryInput = document.getElementById('deliveryPincode');
  const deliveryButton = document.getElementById('deliveryEstimateBtn');
  const deliveryResult = document.getElementById('deliveryResult');
  if (deliveryInput && deliveryButton && deliveryResult) {
    const estimateDelivery = () => {
      const value = deliveryInput.value.replace(/\D/g, '').slice(0, 6);
      deliveryInput.value = value;
      if (value.length < 6) {
        deliveryResult.textContent = 'Enter a 6-digit pincode to check delivery.';
        deliveryResult.classList.add('is-warning');
        return;
      }

      const firstDigit = Number.parseInt(value.charAt(0), 10);
      const days = firstDigit <= 3 ? '2-4 days' : firstDigit <= 6 ? '3-5 days' : '4-7 days';
      deliveryResult.textContent = `Estimated delivery: ${days}. Final date appears at checkout.`;
      deliveryResult.classList.remove('is-warning');
    };
    deliveryButton.addEventListener('click', estimateDelivery);
    deliveryInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        estimateDelivery();
      }
    });
  }

  const copyBookLink = document.getElementById('copyBookLink');
  if (copyBookLink) {
    copyBookLink.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(window.location.href);
        copyBookLink.innerHTML = '<i class="fa-solid fa-check"></i> Copied';
      } catch (error) {
        copyBookLink.innerHTML = '<i class="fa-solid fa-link"></i> Copy failed';
      }
      window.setTimeout(() => {
        copyBookLink.innerHTML = '<i class="fa-solid fa-link"></i> Copy Link';
      }, 1800);
    });
  }

  const shareBook = document.getElementById('shareBook');
  if (shareBook) {
    shareBook.addEventListener('click', async () => {
      const title = document.querySelector('.book-detail-info h1')?.textContent.trim() || document.title;
      if (navigator.share) {
        try {
          await navigator.share({ title, url: window.location.href });
          return;
        } catch (error) {
          if (error.name === 'AbortError') return;
        }
      }
      copyBookLink?.click();
    });
  }

  const adminPanels = document.querySelectorAll('[data-admin-tab-panel]');
  if (adminPanels.length) {
    const adminTabs = ['books', 'orders', 'subscribers', 'stock'];
    const adminTabLinks = document.querySelectorAll(
      '.admin-tabs a[href^="#"], .dashboard-stats a[href^="#"], .admin-focus a[href^="#"]'
    );

    const showAdminTab = tab => {
      const activeTab = adminTabs.includes(tab) ? tab : 'books';
      adminPanels.forEach(panel => {
        panel.hidden = panel.dataset.adminTabPanel !== activeTab;
      });
      adminTabLinks.forEach(link => {
        const linkTab = (link.getAttribute('href') || '').replace('#', '');
        link.classList.toggle('is-active', linkTab === activeTab);
        link.classList.toggle('active', linkTab === activeTab);
        if (link.closest('.admin-tabs')) {
          link.setAttribute('aria-selected', String(linkTab === activeTab));
        }
      });
      if (window.location.hash !== `#${activeTab}`) {
        history.replaceState(null, '', `#${activeTab}`);
      }
    };

    adminTabLinks.forEach(link => {
      link.addEventListener('click', event => {
        const tab = (link.getAttribute('href') || '').replace('#', '');
        if (!adminTabs.includes(tab)) return;
        event.preventDefault();
        showAdminTab(tab);
      });
    });

    window.addEventListener('hashchange', () => {
      showAdminTab(window.location.hash.replace('#', ''));
    });
    showAdminTab(window.location.hash.replace('#', ''));
  }

  const backToTop = document.getElementById('backToTop');
  if (backToTop) {
    const toggleBackToTop = () => {
      backToTop.classList.toggle('is-visible', window.scrollY > 520);
    };
    window.addEventListener('scroll', toggleBackToTop, { passive: true });
    backToTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    toggleBackToTop();
  }
});
