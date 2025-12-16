# BusinessWebsite
this a small ecommerce website that will incorporate  debt tracking functionality

A Django-based web application for managing **customers, products, orders, payments, and debts**.  
Includes both **customer-facing dashboards** and a **custom admin dashboard** with role-based access.

---

## Features
- **Authentication**
  - Custom login with role-based redirect
  - Customers → `/dashboard/`
  - Admins → `/admin-dashboard/`
- **Customer Dashboard**
  - View personal orders, debts, and payments (read-only)
- **Admin Dashboard**
  - Staff-only access (`@staff_member_required`)
  - Manage all orders, debts, and payments
- **Models**
  - Customer, Product, Order, OrderItem, Payment, Debt
- **API Endpoints**
  - REST API powered by Django REST Framework (DRF)
  - Token-based authentication (`/auth/login/`)
  - CRUD endpoints for customers, products, orders, payments, debts

---

##  Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ecommerce-system.git
   cd ecommerce-system
2. - Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
3. - Install dependencies:
pip install -r requirements.txt
4. - Apply migrations:
python manage.py makemigrations
python manage.py migrate
5. - Create a superuser:
python manage.py createsuperuser
6. - Run the server:
python manage.py runserver


 Project Structure
ecommerce/
 ├── models.py        # Customer, Product, Order, Payment, Debt
 ├── views.py         # Customer & Admin dashboards, API views
 ├── urls.py          # Routes for API + dashboards
 ├── admin.py         # Django admin registrations
 └── templates/
      ├── ecommerce/  # customer & admin templates
      └── auth/       # login.html

Usage
- Customer Login → /auth/login-page/ → redirected to /dashboard/
- Admin Login → /auth/login-page/ → redirected to /admin-dashboard/
- API Endpoints → /customers/, /products/, /orders/, /payments/, /debts/

✅ Deliverables Checklist
- [x] Models created and migrated
- [x] Admin registered for all models
- [x] Customer dashboard implemented
- [x] Admin dashboard implemented
- [x] Role-based login redirect
- [x] REST API endpoints with DRF
- [ ] Deployment docs (Heroku/Docker)
- [ ] Unit tests for models and views



License
This project is licensed under the MIT License.

---

This README gives you:
- A clear **overview** of the system.  
- **Setup instructions** for anyone cloning the repo.  
- **Usage notes** for both dashboards and API.  
- A **deliverables checklist** to track progress.  







- 
