# Online BookStore

A Django online bookstore with book browsing, cart checkout, Razorpay payments, paid subscriptions, subscribed-user discounts, order tracking, staff administration, and an AI-assisted customer support widget.

## Features

- Browse books by category, search, and sort.
- Add books to cart or use the single-click **Buy** action.
- Checkout with Razorpay or Cash on Delivery.
- Track order status, view order history, cancel eligible orders, and print invoices.
- Subscribe to monthly, quarterly, or yearly plans with Razorpay.
- Active paid subscribed users receive an automatic 10% discount on book orders.
- Already subscribed users see their current plan, validity date, remaining days, interests, and benefits instead of the plan purchase form.
- Customer support chat answers questions about recommendations, orders, subscriptions, subscribed-user discounts, contact details, and policies.
- Optional Gemini support responses use local store context and fall back to built-in replies when no API key is configured.
- Staff dashboard manages books, orders, and subscribed users.

## Project Structure

```text
online-bookstore/
  backend/
    bookstore_project/      Django project settings and URLs
    store/                  Store app, models, views, forms, admin, migrations
  frontend/
    templates/store/        Django templates
    static/                 CSS and JavaScript assets
  manage.py                 Django CLI entry point
  requirements.txt          Python dependencies
  .env.example              Environment variable template
```

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Environment Variables

Copy `.env.example` to `.env` and fill in only the services you need.

- `SECRET_KEY`: Django secret key.
- `DEBUG`: `True` for local development, `False` in production.
- `ALLOWED_HOSTS`: comma-separated hostnames.
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`: enable live Razorpay payments. If omitted, the app uses demo payment buttons.
- `GEMINI_API_KEY`: enables Gemini AI responses for customer support.
- `GEMINI_MODEL`: defaults to `gemini-1.5-flash`.
- `EMAIL_*` and `DEFAULT_FROM_EMAIL`: optional email settings.
- `SOCIAL_AUTH_*`: optional Google, Facebook, and GitHub login settings.

## Subscribed-User Discount Rules

The 10% book-order discount is only applied when all of these are true:

1. The customer is signed in.
2. The signed-in account has an email address.
3. A `Subscriber` record exists for that email.
4. The subscriber is active, paid, and not expired.

At checkout, the app stores:

- `subtotal_amount`: cart total before discount.
- `discount_amount`: subscribed-user discount amount.
- `total_amount`: final payable amount after discount.

Payment pages and invoices show the subtotal, discount, and final total.

## Razorpay Order Confirmation

Razorpay orders are not confirmed when checkout details are submitted. The app first creates an awaiting-payment order and sends the customer to Razorpay.

- Before payment succeeds: the order is not confirmed, no bill is shown, and stock is not reserved.
- After Razorpay verification succeeds: stock is reserved, payment status becomes paid, order status becomes processing, tracking is created, and the bill becomes available.
- If Razorpay verification fails: the order remains unconfirmed and can be retried from **My Orders**.
- Cash on Delivery orders are confirmed immediately because online payment is not required.

## Customer Support AI

The support widget lives in the base template and posts messages to `/support/chat/`.

When `GEMINI_API_KEY` is available, the app sends Gemini a limited store context containing:

- the current user type,
- whether the user has an active subscription,
- subscription prices,
- relevant books,
- recent authenticated-user orders.

If Gemini is unavailable or no API key is configured, local rule-based replies handle book recommendations, order tracking, subscription plans, 10% subscribed-user discount questions, support contact details, privacy, and return/refund policy answers.

## Subscription Flow

1. User opens `/subscribe/`.
2. User selects a plan and submits name, email, and reading interests.
3. App creates or updates the subscriber record as awaiting payment.
4. User completes Razorpay or demo payment.
5. Subscriber is marked active and paid, with an expiry date based on the selected plan.
6. Future visits to `/subscribe/` show the active plan validity and benefits instead of the plan form.
7. Future checkouts with a matching signed-in account email receive the 10% discount.

## Git Hygiene

Virtual environment folders are intentionally ignored:

```text
.venv/
venv/
```

If either folder was already committed, remove it from Git tracking without deleting local files:

```powershell
git rm -r --cached .venv venv
git commit -m "Remove virtual environments from repository"
```

Keep dependencies in `requirements.txt`, not inside committed virtual environment directories.

## Useful Commands

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
python manage.py check
```
