# 📚 Library Management System
#Live Demo:https://library-management-system-67oc.onrender.com


A **full-featured, production-style Library Management System** built with Django. This is a portfolio-grade, real-world college/university library management application with role-based access control, complete book circulation workflows, automatic fine calculation, and a professional responsive UI.

![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### 👥 User Roles
- **Admin** — Full control over everything: users, books, authors, categories, publishers, issue/return, fines, reports, and Django admin.
- **Librarian** — Add/edit/delete books, manage members, issue & return books, view overdue books, fines, and borrowing history.
- **Member/Student** — Browse & search books, view own borrowing history, due dates, fines, and update profile.

### 📖 Catalog Management
- Full CRUD for **Books**, **Authors**, **Categories**, **Publishers**
- Cover image upload, shelf location, inventory tracking (total vs. available copies)
- Availability badges: **Available / Limited / Unavailable**
- Search by title, ISBN, author, category, plus filters & pagination

### 🔄 Book Circulation
- Issue workflow with live fine & due-date preview
- Return workflow with automatic overdue days and fine calculation
- Business rules enforced in a service layer (no logic in templates):
  - Max borrow limit per member
  - Cannot issue a book with no available copies
  - Issuing decreases / returning increases available copies
  - A book already held cannot be issued again
  - Auto-calculated due dates
  - Automatic overdue detection
  - Returned/lost books cannot be returned again

### 💰 Automatic Fine Calculation
- Sliding-rate fines: **first 7 days ₹5/day**, **after 7 days ₹10/day**
- Rates/periods configurable via `.env` — never hardcoded

### 📊 Dashboard & Reports
- Live statistics cards: Total Books, Available, Issued, Members, Overdue, Total Fines
- Recent Issues, Recent Returns, Overdue Books, Popular Books
- Dedicated Reports page with fine breakdowns, most-borrowed books, most-active members, and category stats

### 🛡️ Security
- Django authentication with proper password hashing
- Role-based authorization (permission-checked, not just hidden buttons)
- CSRF protection, secure form handling, environment-based secrets
- Configurable `DEBUG` & `ALLOWED_HOSTS`

---

## 🧰 Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.13, Django 5.2             |
| Frontend   | HTML5, CSS3, Vanilla JavaScript     |
| Database   | SQLite (dev) / ready for PostgreSQL |
| ORM        | Django ORM                          |
| Icons      | Font Awesome 6                      |
| Auth       | Django Authentication System        |

---

## 🗂️ Project Structure

```
library_management/
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── config/                  # Project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── library/                 # Main library app
│   ├── models.py            # Book, Author, Category, Publisher, BorrowRecord
│   ├── forms.py
│   ├── views.py
│   ├── services.py          # Business logic (issue/return/fine)
│   ├── utils.py             # Config helpers
│   ├── admin.py
│   ├── urls.py
│   └── management/commands/seed_library.py
│
├── accounts/                # Auth & member profiles
│   ├── models.py            # MemberProfile
│   ├── forms.py
│   ├── views.py
│   ├── admin.py
│   └── urls.py
│
├── templates/               # Django templates
│   ├── base.html
│   ├── partials/
│   ├── dashboard/
│   ├── library/
│   └── accounts/
│
├── static/                  # CSS, JS, images
├── media/                   # Uploaded files (covers, avatars)
└── db.sqlite3               # SQLite database (git-ignored)
```

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/library-management-system.git
cd library-management-system

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your values (SECRET_KEY, DEBUG, etc.)

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Seed demo data (optional but recommended)
python manage.py seed_library

# 8. Run the server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** 🎉

---

## 👤 Demo Accounts

After running `python manage.py seed_library`:

| Role     | Username   | Password       |
|----------|------------|----------------|
| Admin    | `admin`    | `admin123`     |
| Librarian| `librarian`| `librarian123` |
| Member   | `aarav`    | `member123`    |

---

## ⚙️ Configuration

Environment variables (see `.env.example`):

| Variable                     | Default | Description                          |
|------------------------------|---------|--------------------------------------|
| `DJANGO_SECRET_KEY`          | —       | Secret key (set in production)       |
| `DJANGO_DEBUG`               | `True`  | Debug mode (`False` in production)   |
| `DJANGO_ALLOWED_HOSTS`       | `localhost,127.0.0.1` | Allowed hosts              |
| `LIBRARY_MAX_BORROW_LIMIT`   | `5`     | Max books a member can borrow        |
| `LIBRARY_BORROW_PERIOD_DAYS` | `14`    | Default loan period                  |
| `LIBRARY_FINE_INITIAL_RATE`  | `5`     | ₹/day for first `FREE_DAYS` days     |
| `LIBRARY_FINE_LATE_RATE`     | `10`    | ₹/day after `FREE_DAYS` days         |
| `LIBRARY_FINE_FREE_DAYS`     | `7`     | First N overdue days at initial rate  |

---

## 🧪 Running Tests

```bash
python manage.py test
```

Tests cover authentication, book creation/availability, issuing, returning, fine calculation, borrowing limits, and unauthorized access.

---

## 📸 Screenshots

> *Add screenshots here for your portfolio:*
> - Dashboard overview
> - Book catalog with search/filters
> - Issue book workflow
> - Return book with fine calculation
> - Member profile
> - Reports page

---

## 🔮 Future Improvements

- Email notifications for due/overdue reminders
- Book reservations / hold queue
- Barcode / QR code scanning for issue & return
- e-book support & download links
- Advanced analytics charts (Chart.js)
- Multi-branch / multi-library support
- SMS notifications

---

## 👤 Author

**Your Name** — [LinkedIn](www.linkedin.com/in/aditya-naik-5a7b79317) · [GitHub](https://github.com/addy-1922)

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
