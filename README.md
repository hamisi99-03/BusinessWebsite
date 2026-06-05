# Business Website 🛒

A full-featured Django-based e-commerce platform for managing products, orders, inventory, and payments. Built with a clean admin panel and customer‑facing storefront.

---

## 👥 Development Team

- **Hamisi Ali** – Backend Developer  
- **bkoimett** – Frontend Developer  

---

## 🚀 Features

- **Product Management** – Create, read, update, and delete products with multiple images
- **Order & Payment Workflow** – Seamless checkout process with payment integration
- **Inventory Tracking** – Automatic stock validation and updates
- **Admin Dashboard** – Dedicated interface for managing products, orders, and customers
- **Responsive Frontend** – Mobile‑friendly design using Bootstrap

---

## 🛠️ Tech Stack

| Layer       | Technology                     |
|-------------|--------------------------------|
| Backend     | Django (Python)                |
| Frontend    | HTML5, CSS3, Bootstrap 5       |
| Database    | SQLite (dev) / PostgreSQL (prod) |
| Version Control | Git + GitHub               |
| Media Storage | Local filesystem (customizable to S3) |

---

## 📂 Project Structure

```text
BusinessWebsite/
├── ecommerce/                 # Main Django app
│   ├── models.py              # Product, Order, Payment, ProductImage
│   ├── forms.py               # Product & image formsets
│   ├── views.py               # Business logic & routing
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS, images
├── media/                     # Uploaded product images
├── db.sqlite3                 # Default database
├── manage.py                  # Django CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hamisi99-03/BusinessWebsite.git
   cd BusinessWebsite
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. Open `http://127.0.0.1:8000` in your browser.

---

## 🤝 Contributing

Contributions are welcome!  
Please open an issue first to discuss any major changes. For minor fixes, feel free to submit a pull request.

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

For questions or support, reach out to the development team.
