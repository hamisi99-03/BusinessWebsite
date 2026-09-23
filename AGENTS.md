# AGENTS.md

## Working Agreement

- Always ask before starting any task. Do not begin implementation or make changes until the user has approved.
- First, clearly lay out the plan/approach: what will change, which files are involved, and the steps in order.
- Wait for explicit confirmation, then proceed only with the approved plan. If scope changes or new questions arise, stop and ask again before continuing.

### Git Workflow

- After any change or addition is made, stop and ask for confirmation before running the git workflow.
- Once confirmed, perform the full git workflow (stage → commit → push) using the approved steps.
- Never run git commands (add, commit, push, PR) without explicit confirmation.

## Project

Django 5.2 e-commerce platform ("H&I Store") for managing products, orders, inventory, debts, consignments, expenses, and payments. Serves HTML templates plus a DRF API. Deployed to Render with PostgreSQL and Redis; media stored in Supabase S3-compatible buckets.

## Setup

A virtualenv lives in `env/` (not `venv/`). Activate on Windows:

```powershell
env\Scripts\activate
pip install -r requirements.txt
```

`SECRET_KEY` is mandatory (`ecommerce_manager/settings.py:32` reads `os.environ['SECRET_KEY']`) — `manage.py` fails with `KeyError: 'SECRET_KEY'` without it. There is no committed `.env`; copy `.env.example` to `.env` and set at least `SECRET_KEY` (and `DEBUG=True`) before running anything.

## Commands

```powershell
python manage.py runserver            # dev server at http://127.0.0.1:8000
python manage.py test                 # run tests (ecommerce/tests.py)
python manage.py check                # system checks
python manage.py makemigrations       # after model changes
python manage.py migrate              # apply migrations
python manage.py createsuperuser
python manage.py collectstatic --no-input
python manage.py seed_data            # seed demo users/products/orders
```

There is no lint/format config (no ruff, flake8, black, or pytest). Do not assume one exists; use `python manage.py check` and `python manage.py test` to verify changes.

## Architecture

- `ecommerce_manager/` — project package. `settings.py`, root `urls.py`, WSGI/ASGI.
- `ecommerce/` — the single app holding all business logic:
  - `models.py` — `Category`, `Brand`, `Customer`, `Product`, `ProductImage`, `Order`, `OrderItem`, `Payment`, `Debt`, `StockAdjustment`, `Supplier`, `Consignment`, `ConsignmentItem`, `Expense`, `Cart`, `CartItem`, `Notification`.
  - `views.py` — DRF ViewSets for the API plus function views for the HTML dashboard/storefront.
  - `serializers.py`, `forms.py`, `admin.py`, `signals.py`, `urls.py`, `storage_backends.py`, `notifications_util.py`, `widgets.py`.
  - `templates/ecommerce/` — server-rendered pages; `static/` — CSS/JS.
- Routes: everything is mounted under `/api/` (`ecommerce_manager/urls.py`), and `/` redirects to `/api/store/products/`. Django admin is at `/admin/`.

## Conventions

- Views split by audience: DRF ViewSets (`ProductViewSet`, `OrderViewSet`, etc.) use permission classes (`StaffOnly`, `StaffOrReadPublic`, `AuthenticatedReadStaffWrite` in `views.py`) for API access; HTML views use `staff_member_required` / login decorators. Public product reads are allowed, writes are staff-only.
- State-changing HTML actions (logout, cart removal, etc.) require POST and are covered by regression tests.
- Registration must never grant staff privileges.
- Business logic lives in `signals.py` (debt creation/updating, price syncing, customer creation, image cleanup) — check there before adding logic to views.
- Media uses two Supabase buckets: `product-media` (public) and `profile-media` (private), via `storage_backends.py`.
- Settings are environment-driven; production behavior (HTTPS redirect, secure cookies, HSTS, Redis cache) activates when `DEBUG=False`. Tests use `@override_settings(SECURE_SSL_REDIRECT=False)`.
- Keep `.env` and secrets out of commits — `.gitignore` covers `.env`, `env/`, `db.sqlite3`, and `media/`.

## Deployment

Render uses `render.yaml` with `build.sh` (install → collectstatic → migrate) and `start.sh` (migrate → gunicorn, `ecommerce_manager.wsgi`). Python 3.11.1 in the Render config; local virtualenv is 3.14.
