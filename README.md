# Online Bookstore

A Django-powered online bookstore with a React/Vite shopping frontend. The backend manages books, users, carts, orders, subscriptions, payments, and support APIs. The React app provides the customer-facing catalog, category browsing, cart experience, responsive layout, and light/dark theme.

## Features

- Book catalog with search, genre filters, availability filters, sorting, stock status, and related books.
- React frontend with home, categories, book detail, and cart views.
- Session-based cart API with add, update, remove, item count, and totals.
- Django authentication support with user profile data.
- Razorpay and Cash on Delivery order model support.
- Subscription plans for monthly, quarterly, and yearly readers.
- 10% subscribed-user discount logic for eligible checkout flows.
- Order tracking fields, invoice-ready order totals, cancellation state, and payment status tracking.
- Optional Gemini-powered support chat with local fallback behavior.
- Django admin support for managing books, orders, subscribers, and users.
- GitHub Actions workflow for Django checks and tests.

## Tech Stack

- Python 3.12+
- Django 5.2+
- SQLite for local development
- React 18
- Vite 6
- JavaScript, HTML, CSS
- Razorpay integration fields
- Optional Gemini API integration

## Project Structure

```text
online-bookstore/
  backend/
    bookstore_project/
      settings.py
      urls.py
      wsgi.py
    store/
      admin.py
      apps.py
      forms.py
      models.py
      urls.py
      views.py
      management/commands/
      migrations/
  frontend/
    react-app/
      index.html
      package.json
      package-lock.json
      vite.config.js
      src/
        main.jsx
        styles.css
    templates/
      registration/
      store/
    static/
      js/
      store/css/
  .github/workflows/django.yml
  .env.example
  .gitignore
  CONTRIBUTING.md
  manage.py
  requirements.txt
```

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Create your local environment file:

```powershell
copy .env.example .env
```

Run migrations and create an admin user:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Start Django:

```powershell
python manage.py runserver
```

The Django backend runs at:

```text
http://127.0.0.1:8000/
```

## React Frontend

Open a second terminal and run:

```powershell
cd frontend\react-app
npm install
npm run dev
```

The React app runs at:

```text
http://127.0.0.1:5173/
```

The React dev server calls the Django API, so keep Django running at the same time.

Build the React app:

```powershell
cd frontend\react-app
npm run build
```

Preview the production build:

```powershell
npm run preview
```

## Environment Variables

Copy `.env.example` to `.env` before running locally.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Use `True` for local development |
| `ALLOWED_HOSTS` | Comma-separated Django allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Optional trusted origins for the React dev server |
| `RAZORPAY_KEY_ID` | Razorpay public key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key |
| `GEMINI_API_KEY` | Optional Gemini key for support chat |
| `GEMINI_MODEL` | Gemini model name |
| `EMAIL_HOST` | SMTP host for password reset email |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_USE_TLS` | TLS setting for SMTP |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password or app password |
| `DEFAULT_FROM_EMAIL` | Sender address |
| `SOCIAL_AUTH_*` | Optional OAuth credentials |

Example local React origin:

```text
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## Useful Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test store
python manage.py runserver
```

Seed sample books if needed:

```powershell
python manage.py seed_books
```

Test email configuration:

```powershell
python manage.py test_email
```

## API Endpoints

The React app currently uses these Django JSON endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/bootstrap/` | Current user, cart, and category data |
| `GET` | `/api/books/` | Book list with filters and sorting |
| `GET` | `/api/books/<book_id>/` | Book detail and related books |
| `GET` | `/api/categories/` | Category list with book counts |
| `GET` | `/api/cart/` | Current cart |
| `POST` | `/api/cart/add/<book_id>/` | Add one book to cart |
| `POST` | `/api/cart/update/` | Update cart quantities |
| `POST` | `/api/cart/remove/<book_id>/` | Remove a book from cart |

The existing Django views also contain checkout, subscription, order, payment, support, and admin-dashboard logic used by the backend.

## Development Notes

- Main backend logic: `backend/store/views.py`
- Data models: `backend/store/models.py`
- URL routes: `backend/store/urls.py`
- Django settings: `backend/bookstore_project/settings.py`
- React entry point: `frontend/react-app/src/main.jsx`
- React styles: `frontend/react-app/src/styles.css`
- Django templates: `frontend/templates/`
- Static Django assets: `frontend/static/`

## Git And GitHub

Files intentionally ignored:

- `.env`
- `.env.*` except `.env.example`
- `.venv/`
- `venv/`
- `db.sqlite3`
- `frontend/react-app/node_modules/`
- `frontend/react-app/dist/`
- local Playwright output scripts and temporary artifacts

Before pushing changes:

```powershell
git status
python manage.py check
python manage.py test store
```

Commit and push:

```powershell
git add .
git commit -m "Describe your change"
git push origin main
```

## CI

GitHub Actions runs on pushes and pull requests to `main` or `master`.

The workflow:

1. Checks out the repository.
2. Installs Python dependencies from `requirements.txt`.
3. Runs `python manage.py check`.
4. Runs `python manage.py test store`.

## Security Notes

- Do not commit `.env`, local databases, virtual environments, or generated dependency folders.
- Use strong production values for `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS`.
- Store Razorpay, Gemini, email, and OAuth secrets outside GitHub source code.
- Review `npm audit` output before deploying frontend dependencies to production.
