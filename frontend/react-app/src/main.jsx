import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import '../../static/store/css/style.css';
import './styles.css';

const fallbackCover = 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=190&h=240&fit=crop';
const rupees = (value) => `₹${Number(value || 0).toFixed(2)}`;

function getCookie(name) {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1];
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.method && options.method !== 'GET') {
    headers['X-CSRFToken'] = getCookie('csrftoken') || '';
  }

  const response = await fetch(path, {
    credentials: 'same-origin',
    ...options,
    headers
  });
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : {};
  if (!response.ok) {
    throw new Error(payload.error || 'Request failed');
  }
  return payload;
}

function App() {
  const [theme, setTheme] = useState(localStorage.getItem('bookstore:theme') || 'light');
  const [route, setRoute] = useState({ name: 'home' });
  const [bootstrap, setBootstrap] = useState(null);
  const [cart, setCart] = useState({ items: [], item_count: 0, total: '0.00' });
  const [toast, setToast] = useState('');

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('bookstore:theme', theme);
  }, [theme]);

  useEffect(() => {
    api('/api/bootstrap/')
      .then((data) => {
        setBootstrap(data);
        setCart(data.cart);
      })
      .catch((error) => setToast(error.message));
  }, []);

  function navigate(nextRoute) {
    setRoute(nextRoute);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function addToCart(bookId) {
    try {
      const data = await api(`/api/cart/add/${bookId}/`, { method: 'POST' });
      setCart(data);
      setToast(data.message || 'Book added to cart.');
    } catch (error) {
      setToast(error.message);
    }
  }

  async function updateCart(bookId, quantity) {
    try {
      const data = await api('/api/cart/update/', {
        method: 'POST',
        body: JSON.stringify({ [bookId]: quantity })
      });
      setCart(data);
    } catch (error) {
      setToast(error.message);
    }
  }

  async function removeFromCart(bookId) {
    try {
      const data = await api(`/api/cart/remove/${bookId}/`, { method: 'POST' });
      setCart(data);
    } catch (error) {
      setToast(error.message);
    }
  }

  const categories = bootstrap?.categories || [];
  const user = bootstrap?.user || {};

  return (
    <>
      <Navbar
        cartCount={cart.item_count}
        user={user}
        theme={theme}
        onTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onNavigate={navigate}
      />

      {toast && (
        <button className="react-toast alert alert-success" onClick={() => setToast('')}>
          <i className="fa-solid fa-circle-info"></i> {toast}
        </button>
      )}

      <main>
        <div className="container">
          {route.name === 'home' && (
            <HomePage
              categories={categories}
              activeGenre={route.genre || ''}
              isSubscribed={user.is_subscribed}
              onOpenBook={(id) => navigate({ name: 'book', id })}
              onAdd={addToCart}
              onNavigate={navigate}
            />
          )}
          {route.name === 'book' && (
            <BookPage
              id={route.id}
              onBack={() => navigate({ name: 'home' })}
              onOpenBook={(id) => navigate({ name: 'book', id })}
              onAdd={addToCart}
            />
          )}
          {route.name === 'categories' && (
            <CategoriesPage categories={categories} onSelect={(slug) => navigate({ name: 'home', genre: slug })} />
          )}
          {route.name === 'cart' && (
            <CartPage cart={cart} onUpdate={updateCart} onRemove={removeFromCart} onShop={() => navigate({ name: 'home' })} />
          )}
        </div>
      </main>

      <Footer isSubscribed={user.is_subscribed} onNavigate={navigate} />
    </>
  );
}

function Navbar({ cartCount, user, theme, onTheme, onNavigate }) {
  return (
    <nav className="navbar" id="mainNav">
      <div className="container nav-container">
        <button className="logo react-link" onClick={() => onNavigate({ name: 'home' })}>
          <i className="fa-solid fa-book-open"></i> BookStore
        </button>

        <form className="search-form" onSubmit={(event) => event.preventDefault()}>
          <input
            type="text"
            className="search-input"
            placeholder="Search books, authors..."
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                onNavigate({ name: 'home', q: event.currentTarget.value });
              }
            }}
          />
        </form>

        <div className="nav-links">
          <button className="nav-link react-link" title="Home" onClick={() => onNavigate({ name: 'home' })}>
            <i className="fa-solid fa-house"></i><span className="nav-label">Home</span>
          </button>
          <button className="nav-link react-link" title="Categories" onClick={() => onNavigate({ name: 'categories' })}>
            <i className="fa-solid fa-layer-group"></i><span className="nav-label">Categories</span>
          </button>
          <a href="/subscribe/" className={`nav-link ${user.is_subscribed ? 'is-subscribed' : ''}`} title="Subscribe">
            <i className={`fa-solid ${user.is_subscribed ? 'fa-circle-check' : 'fa-envelope'}`}></i>
            <span className="nav-label">{user.is_subscribed ? 'Subscribed' : 'Subscribe'}</span>
          </a>
          <a href="/track-order/" className="nav-link" title="Track Order">
            <i className="fa-solid fa-location-dot"></i><span className="nav-label">Track</span>
          </a>
          <button className="nav-link cart-icon react-link" title="Cart" onClick={() => onNavigate({ name: 'cart' })}>
            <i className="fa-solid fa-cart-shopping"></i>
            <span className="cart-count">{cartCount}</span>
          </button>
          <button type="button" className="theme-toggle" onClick={onTheme} aria-label="Switch theme" title="Theme">
            <i className={`fa-solid ${theme === 'dark' ? 'fa-sun' : 'fa-moon'}`}></i>
          </button>

          {user.is_authenticated ? (
            <a href="/order-history/" className="nav-link">
              <i className="fa-solid fa-circle-user"></i><span className="nav-label">{user.name || 'Account'}</span>
            </a>
          ) : (
            <>
              <a href="/login/" className="nav-link">
                <i className="fa-solid fa-right-to-bracket"></i><span className="nav-label">Login</span>
              </a>
              <a href="/register/" className="btn-outline">
                <i className="fa-solid fa-user-plus"></i> Register
              </a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

function HomePage({ categories, activeGenre, isSubscribed, onOpenBook, onAdd, onNavigate }) {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ q: '', genre: activeGenre, availability: '', sort: 'newest' });

  useEffect(() => {
    setFilters((current) => ({ ...current, genre: activeGenre }));
  }, [activeGenre]);

  useEffect(() => {
    const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value)).toString();
    setLoading(true);
    api(`/api/books/?${query}`)
      .then((data) => setBooks(data.books))
      .finally(() => setLoading(false));
  }, [filters]);

  const featuredCategories = [
    ['fiction', 'fa-book-open', 'Fiction', 'Novels, thrillers & more'],
    ['nonfiction', 'fa-microscope', 'Non-Fiction', 'History, science, biography'],
    ['children', 'fa-shapes', "Children's", 'Picture books & young readers'],
    ['academic', 'fa-graduation-cap', 'Academic', 'Textbooks & reference'],
    ['thriller', 'fa-user-secret', 'Thriller', 'Crime, mystery & suspense'],
    ['romance', 'fa-heart', 'Romance', 'Love stories & more'],
    ['scifi', 'fa-rocket', 'Sci-Fi', 'Space, future & beyond']
  ];

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge"><i className="fa-solid fa-bookmark"></i> Online bookstore</div>
          <h1>BookStore</h1>
          <p>Shop novels, textbooks, children's books, thrillers, and more with fast delivery and simple checkout.</p>
          <div className="hero-actions">
            <a href="#featured" className="btn-primary"><i className="fa-solid fa-magnifying-glass"></i> Shop Books</a>
            <a href="/subscribe/" className="btn-secondary">
              <i className={`fa-solid ${isSubscribed ? 'fa-circle-check' : 'fa-envelope'}`}></i>
              {isSubscribed ? 'Subscribed' : 'Get 10% Off'}
            </a>
          </div>
          <div className="hero-trust">
            <span><i className="fa-solid fa-truck fa-fw"></i> Free delivery over ₹400</span>
            <span><i className="fa-solid fa-rotate-left fa-fw"></i> No-hassle returns</span>
            <span><i className="fa-solid fa-lock fa-fw"></i> Safe checkout</span>
          </div>
          <div className="mood-finder" aria-label="Browse by mood">
            <span>Quick browse</span>
            <button onClick={() => onNavigate({ name: 'home', genre: 'fiction' })}>a story</button>
            <button onClick={() => onNavigate({ name: 'home', genre: 'thriller' })}>a thrill</button>
            <button onClick={() => onNavigate({ name: 'home', genre: 'academic' })}>to study</button>
          </div>
        </div>
        <div className="hero-image">
          <img
            src="https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=900&auto=format&fit=crop"
            alt="Open books"
            loading="lazy"
            decoding="async"
          />
        </div>
      </section>

      <section className="reader-tools" aria-label="BookStore features">
        <Feature icon="fa-heart" title="0 saved books" copy="Keep favorites while browsing." />
        <Feature icon="fa-eye" title="Quick preview" copy="Peek at book details without losing your place." />
        <Feature icon="fa-tags" title="Subscriber savings" copy="Get 10% off eligible orders." />
      </section>

      <section className="smart-book-finder" aria-label="Smart book finder">
        <div className="smart-finder-copy">
          <span className="eyebrow"><i className="fa-solid fa-sliders"></i> Smart Finder</span>
          <h2>Find the right book faster</h2>
          <p>Search by title, author, or description, then narrow results by genre, stock, and price order.</p>
        </div>
        <form className="smart-finder-form" onSubmit={(event) => event.preventDefault()}>
          <label>
            <span>Search</span>
            <input value={filters.q} onChange={(event) => setFilters({ ...filters, q: event.target.value })} placeholder="Book, author, keyword" />
          </label>
          <label>
            <span>Genre</span>
            <select value={filters.genre} onChange={(event) => setFilters({ ...filters, genre: event.target.value })}>
              <option value="">All genres</option>
              {categories.map((category) => (
                <option key={category.slug} value={category.slug}>{category.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Availability</span>
            <select value={filters.availability} onChange={(event) => setFilters({ ...filters, availability: event.target.value })}>
              <option value="">All books</option>
              <option value="in_stock">In stock</option>
              <option value="new">New arrivals</option>
            </select>
          </label>
          <label>
            <span>Sort</span>
            <select value={filters.sort} onChange={(event) => setFilters({ ...filters, sort: event.target.value })}>
              <option value="newest">Newest first</option>
              <option value="price_low">Price low to high</option>
              <option value="price_high">Price high to low</option>
              <option value="title">Title A-Z</option>
              <option value="stock">Most stock</option>
            </select>
          </label>
          <div className="smart-finder-actions">
            <button type="button" className="btn-primary"><i className="fa-solid fa-magnifying-glass"></i> Find Books</button>
            <button type="button" className="btn-secondary" onClick={() => setFilters({ q: '', genre: '', availability: '', sort: 'newest' })}>
              <i className="fa-solid fa-rotate-left"></i> Reset
            </button>
          </div>
        </form>
      </section>

      <div className="section-title">Shop Categories</div>
      <div className="category-grid">
        {featuredCategories.map(([slug, icon, name, copy]) => (
          <button key={slug} className="category-card react-card-button" onClick={() => onNavigate({ name: 'home', genre: slug })}>
            <div className="cat-icon"><i className={`fa-solid ${icon}`}></i></div>
            <h3>{name}</h3>
            <p>{copy}</p>
            <span className="cat-arrow"><i className="fa-solid fa-arrow-right"></i></span>
          </button>
        ))}
        <button className="category-card cat-card-all react-card-button" onClick={() => onNavigate({ name: 'categories' })}>
          <div className="cat-icon"><i className="fa-solid fa-layer-group"></i></div>
          <h3>All Categories</h3>
          <p>Explore every genre</p>
          <span className="cat-arrow"><i className="fa-solid fa-arrow-right"></i></span>
        </button>
      </div>

      <div className="section-title" id="featured">
        <i className="fa-solid fa-star"></i>
        Featured Books
      </div>
      <div className="book-toolbar" aria-label="Featured book filters">
        <div className="book-filter-group">
          <button type="button" className="book-filter is-active"><i className="fa-solid fa-border-all"></i> All</button>
          <button type="button" className="book-filter" onClick={() => setFilters({ ...filters, availability: 'new' })}><i className="fa-solid fa-star"></i> New</button>
          <button type="button" className="book-filter" onClick={() => setFilters({ ...filters, availability: 'in_stock' })}><i className="fa-solid fa-circle-check"></i> In stock</button>
        </div>
        <span className="book-filter-count">{books.length} book{books.length === 1 ? '' : 's'}</span>
      </div>
      {loading ? <Status text="Loading books..." /> : <BooksGrid books={books} onOpenBook={onOpenBook} onAdd={onAdd} />}
    </>
  );
}

function Feature({ icon, title, copy }) {
  return (
    <div className="reader-tool">
      <i className={`fa-solid ${icon}`}></i>
      <div>
        <strong>{title}</strong>
        <span>{copy}</span>
      </div>
    </div>
  );
}

function BooksGrid({ books, onOpenBook, onAdd }) {
  if (!books.length) {
    return <div className="book-filter-empty">No books matched your filters.</div>;
  }

  return (
    <div className="books-grid">
      {books.map((book) => (
        <article className="book-card clickable-book" key={book.id}>
          <button className="book-cover-wrap react-image-button" onClick={() => onOpenBook(book.id)}>
            <img src={book.cover_url} alt={book.title} className="book-cover" onError={(event) => { event.currentTarget.src = fallbackCover; }} />
            <div className="book-card-tools">
              <span className="icon-action"><i className="fa-regular fa-heart"></i></span>
              <span className="icon-action"><i className="fa-solid fa-eye"></i></span>
            </div>
            {book.is_new && <span className="book-badge new">New</span>}
            {book.stock === 0 && <span className="book-badge oos">Sold Out</span>}
          </button>
          <div className="book-info">
            <div className="book-genre-tag">{book.genre_label}</div>
            <button className="book-title react-title-button" onClick={() => onOpenBook(book.id)}>{book.title}</button>
            <div className="book-author"><i className="fa-solid fa-pen-nib"></i> {book.author}</div>
            <div className="book-price amount-highlight">{rupees(book.price)}</div>
            <div className="book-card-actions">
              {book.stock > 0 ? (
                <>
                  <button className="btn-small btn-add-cart" onClick={() => onAdd(book.id)}>
                    <i className="fa-solid fa-cart-plus"></i> Add
                  </button>
                  <a href={`/buy-now/${book.id}/`} className="btn-small btn-buy-now">
                    <i className="fa-solid fa-bolt"></i> Buy
                  </a>
                </>
              ) : (
                <span className="btn-small disabled">Sold Out</span>
              )}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function BookPage({ id, onBack, onOpenBook, onAdd }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    setData(null);
    api(`/api/books/${id}/`).then(setData);
  }, [id]);

  if (!data) {
    return <Status text="Loading book..." />;
  }

  const { book, related_books: relatedBooks } = data;
  return (
    <>
      <section className="book-detail">
        <div className="book-detail-image">
          <img src={book.cover_url} alt={book.title} onError={(event) => { event.currentTarget.src = fallbackCover; }} />
        </div>

        <div className="book-detail-info">
          <span className="eyebrow">{book.genre_label || 'Fiction'}</span>
          <h1>{book.title}</h1>
          <p className="author-tag">by {book.author}</p>
          <div className="price-tag amount-highlight">{rupees(book.price)}</div>
          <p className="description-text">{book.description}</p>
          {book.stock > 0 ? (
            <div className="stock-badge in-stock"><i className="fa-solid fa-check"></i> In Stock - {book.stock} left</div>
          ) : (
            <div className="stock-badge out-of-stock"><i className="fa-solid fa-xmark"></i> Out of Stock</div>
          )}

          <div className="book-helper-panel">
            <div className="delivery-estimator">
              <label>
                <span><i className="fa-solid fa-truck-fast"></i> Delivery estimate</span>
                <small>Enter your pincode for a basic estimate.</small>
              </label>
              <div className="delivery-input-row">
                <input type="text" inputMode="numeric" maxLength="6" placeholder="Pincode" />
                <button type="button" className="btn-secondary">Check</button>
              </div>
              <p className="delivery-result">Most locations deliver in 3-6 days.</p>
            </div>
            <div className="book-share-tools">
              <button type="button" className="btn-secondary"><i className="fa-regular fa-heart"></i> Save Book</button>
              <button type="button" className="btn-secondary"><i className="fa-solid fa-link"></i> Copy Link</button>
              <button type="button" className="btn-secondary"><i className="fa-solid fa-share-nodes"></i> Share</button>
            </div>
          </div>

          <div className="book-detail-actions">
            {book.stock > 0 ? (
              <>
                <button className="btn-secondary btn-large" onClick={() => onAdd(book.id)}>
                  <i className="fa-solid fa-cart-plus"></i> Add to Cart
                </button>
                <a href={`/buy-now/${book.id}/`} className="btn-primary btn-large">
                  <i className="fa-solid fa-bolt"></i> Buy
                </a>
              </>
            ) : (
              <button disabled className="btn-dark btn-large disabled">Unavailable</button>
            )}
            <button onClick={onBack} className="btn-secondary btn-large">
              <i className="fa-solid fa-arrow-left"></i> Back
            </button>
          </div>
        </div>
      </section>

      {!!relatedBooks.length && (
        <section className="related-books">
          <div className="section-title"><i className="fa-solid fa-bookmark"></i> More {book.genre_label} Books</div>
          <div className="related-book-grid">
            {relatedBooks.map((related) => (
              <button key={related.id} className="related-book-card react-card-button" onClick={() => onOpenBook(related.id)}>
                <img src={related.cover_url} alt={related.title} onError={(event) => { event.currentTarget.src = fallbackCover; }} />
                <div>
                  <strong>{related.title}</strong>
                  <span>{related.author}</span>
                  <em>{rupees(related.price)}</em>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function CategoriesPage({ categories, onSelect }) {
  return (
    <>
      <section className="cat-inline-hero">
        <span className="eyebrow"><i className="fa-solid fa-layer-group"></i> Categories</span>
        <h1>Shop Categories</h1>
        <p>Choose a shelf and browse books from that collection.</p>
      </section>
      <div className="category-grid">
        {categories.map((category) => (
          <button key={category.slug} className="category-card react-card-button" onClick={() => onSelect(category.slug)}>
            <div className="cat-icon"><i className="fa-solid fa-book-open"></i></div>
            <h3>{category.name}</h3>
            <p>{category.description}</p>
            <span className="cat-arrow"><i className="fa-solid fa-arrow-right"></i></span>
          </button>
        ))}
      </div>
    </>
  );
}

function CartPage({ cart, onUpdate, onRemove, onShop }) {
  return (
    <>
      <div className="page-hero">
        <span className="eyebrow">Your Selection</span>
        <h1>Shopping Cart</h1>
      </div>

      {cart.items.length ? (
        <div className="cart-wrapper">
          <div className="cart-table-wrap">
            <table className="cart-table">
              <thead>
                <tr>
                  <th>Book</th>
                  <th>Price</th>
                  <th>Qty</th>
                  <th>Subtotal</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cart.items.map((item) => (
                  <tr key={item.book_id}>
                    <td>
                      <span className="cart-book-title">{item.book.title}</span>
                      <span className="cart-book-author">{item.book.author}</span>
                    </td>
                    <td>{rupees(item.book.price)}</td>
                    <td>
                      <input
                        type="number"
                        value={item.quantity}
                        min="0"
                        max={item.book.stock}
                        className="qty-input"
                        onChange={(event) => onUpdate(item.book_id, event.target.value)}
                      />
                    </td>
                    <td className="cart-subtotal">{rupees(item.subtotal)}</td>
                    <td>
                      <button className="btn-remove" onClick={() => onRemove(item.book_id)}>Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="cart-summary">
            <h3>Order Summary</h3>
            <div className="summary-row">
              <span>Items ({cart.item_count})</span><span>{rupees(cart.total)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping</span><span>Free</span>
            </div>
            <div className="summary-row total">
              <span>Total</span><span>{rupees(cart.total)}</span>
            </div>
            <a href="/checkout/" className="btn-success">Checkout <i className="fa-solid fa-arrow-right"></i></a>
            <button className="btn-secondary" onClick={onShop}>Continue Shopping</button>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon"><i className="fa-solid fa-cart-shopping"></i></div>
          <h3>Your cart is empty</h3>
          <p>Looks like you haven't added any books yet.</p>
          <button onClick={onShop} className="btn-primary">Browse Books</button>
        </div>
      )}
    </>
  );
}

function Footer({ isSubscribed, onNavigate }) {
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-top">
          <div className="footer-brand-col">
            <div className="footer-logo"><i className="fa-solid fa-book-open"></i> BookStore</div>
            <p className="footer-tagline">Discover your next great read.</p>
            <div className="footer-socials">
              <a href="https://x.com/home" title="Twitter/X"><i className="fa-brands fa-x-twitter"></i></a>
              <a href="https://www.instagram.com/bookstore.b001/" title="Instagram"><i className="fa-brands fa-instagram"></i></a>
              <a href="https://www.facebook.com/profile.php?id=61590729831674" title="Facebook"><i className="fa-brands fa-facebook-f"></i></a>
              <a href="https://www.youtube.com/@Book-m6u" title="YouTube"><i className="fa-brands fa-youtube"></i></a>
            </div>
          </div>

          <div className="footer-nav-col">
            <h4>Shop</h4>
            <button onClick={() => onNavigate({ name: 'home' })}><i className="fa-solid fa-house fa-fw"></i> Home</button>
            <button onClick={() => onNavigate({ name: 'categories' })}><i className="fa-solid fa-layer-group fa-fw"></i> Categories</button>
            <button onClick={() => onNavigate({ name: 'cart' })}><i className="fa-solid fa-cart-shopping fa-fw"></i> Cart</button>
            <a href="/track-order/"><i className="fa-solid fa-location-dot fa-fw"></i> Track Order</a>
          </div>

          <div className="footer-nav-col">
            <h4>Account</h4>
            <a href="/login/"><i className="fa-solid fa-right-to-bracket fa-fw"></i> Login</a>
            <a href="/register/"><i className="fa-solid fa-user-plus fa-fw"></i> Register</a>
          </div>

          <div className="footer-nav-col">
            <h4>{isSubscribed ? 'Subscription' : 'Newsletter'}</h4>
            <p className="footer-newsletter-copy">
              {isSubscribed ? 'You are subscribed. Your 10% discount applies at checkout.' : 'Subscribed users get 10% off book orders.'}
            </p>
            <a href="/subscribe/" className="footer-sub-btn">
              <i className={`fa-solid ${isSubscribed ? 'fa-circle-check' : 'fa-envelope'}`}></i>
              {isSubscribed ? 'Subscribed' : 'Subscribe'}
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function Status({ text }) {
  return <div className="empty-state"><p>{text}</p></div>;
}

createRoot(document.getElementById('root')).render(<App />);
