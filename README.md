# Driving Services FastAPI

A modern web application for managing driving-related services, in particluar car insurance policies, built with FastAPI, Jinja2, and a modular Python backend. This project demonstrates best practices in API design, frontend-backend integration, and clean code architecture.

---

## 📑 Table of Contents
- [🚀 Live Application & API Documentation](#-live-demo--api-documentation)
- [🛠️ Tech Stack](#️-tech-stack)
- [✨ Features](#-features)
- [📚 API Endpoints](#-api-endpoints)
- [🏁 Running the Application Locally](#-running-the-application-locally)
- [🧑‍💻 Coding Techniques & Best Practices](#-coding-techniques--best-practices)
- [🧪 Testing](#-testing)
- [📁 Folder Structure](#-folder-structure)
- [📖 User Manual](#-user-manual)

---

## 🚀 Live Application & API Documentation

- **Production API Docs:** [https://driving-services-fastapi.onrender.com/docs](https://driving-services-fastapi.onrender.com/docs)
- The above link provides interactive Swagger UI for all available API endpoints.
You can login with the flowing Username-Password combinations or register a new user
admin1 - password123 - Admin
member1 - pass123 - User
member2 - pass123 – User
bobsmith – passcode - User
issy - BlueFish7 - Admin
luke – password - Admin
steve - MyPass123 - Admin
newmember – password - User
jessica - password123 - User
daniel - CarLover12 - User

---

## 🛠️ Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), Python 3.12
- **Frontend:** Jinja2 templates, HTML5, CSS3, JavaScript
- **Database:** (Pluggable, see `db_connect.py`)
- **Testing:** pytest
- **Containerisation:** Docker (see `Dockerfile`)

---

## ✨ Features

### Backend (API)
- User authentication (JWT) and profile management
- Car insurance policy management (CRUD)
- Optional extras for insurance policies (CRUD)
- Modular service and data access layers
- Error handling and response standardisation
- Admin-only endpoints for sensitive operations

### Frontend
- Responsive user dashboard (profile, details, password change)
- Dynamic forms and validation
- Clean, modern UI with custom CSS
- Comprehensive admin dashboard
- Manage users, policies, and optional extras
- Perform CRUD operations on all entities
- Access to admin-only features

---

## 📚 API Endpoints

| Method | Endpoint                        | Description & Modes                                 |
|--------|----------------------------------|-----------------------------------------------------|
| POST   | `/token`                        | Obtain JWT access and refresh tokens                |
| POST   | `/refresh_token`                 | Refresh JWT tokens                                  |
| POST   | `/verify_authentication`         | Verify current JWT token                            |
| POST   | `/create_user`                   | Create a new user (admin only)                      |
| GET    | `/read_user`                     | Read users: `mode=list_all`, `mode=filter`, `mode=by_id`, `mode=myself` |
| PUT    | `/update_user`                   | Update user details (admin or self)                 |
| PATCH  | `/update_user_password`          | Update user password (admin override or self)       |
| DELETE | `/delete_user`                   | Delete a user (admin only)                          |
| POST   | `/register_user`                 | Register a new user (public)                        |
| POST   | `/create_optional_extra`         | Create an optional extra (admin only)               |
| GET    | `/read_optional_extra`           | Read optional extras: `mode=list_all`, `mode=by_id` |
| PUT    | `/update_optional_extra`         | Update an optional extra (admin only)               |
| DELETE | `/delete_optional_extra`         | Delete an optional extra (admin only)               |
| POST   | `/create_car_insurance_policy`   | Create a car insurance policy (admin or self)       |
| GET    | `/read_car_insurance_policy`     | Read policies: `mode=list_all`, `mode=by_id`, `mode=myself`, `mode=filter` |
| PUT    | `/update_car_insurance_policy`   | Update a car insurance policy (admin or self)       |
| DELETE | `/delete_car_insurance_policy`   | Delete a car insurance policy (admin only)          |
| GET    | `/healthcheck`                   | Health check endpoint                               |

See [API Docs](https://driving-services-fastapi.onrender.com/docs) for the full list and interactive testing.

---

## 🏁 Running the Application Locally

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Luke-Best-AA/driving-services-fastapi.git
   cd driving-services-fastapi
   ```
2. **Create a Python virtual environment (Python 3.12+ recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Set up the Database (SQL Server Express):**
   - Download and install [SQL Server Express](https://www.microsoft.com/en-us/sql-server/sql-server-downloads).
   - Create a new local SQL Server instance (default instance name is usually `SQLEXPRESS`).
   - Open SQL Server Management Studio (SSMS) or use `sqlcmd` to connect to your instance.
   - Run the provided SQL scripts to create the database, tables, and populate initial data. (See below for example SQLs.)

5. **Create a `.env` file in the project root:**
	Example contents:
	```powershell
	SERVER=localhost\SQLEXPRESS
	DB_NAME=DrivingServiceManagement
	DB_USER=your_sql_username
	DB_PASSWORD=your_sql_password
	ENV=dev
	SECRET_KEY=your_secret_key
	```
	Adjust parameters as needed for your environment.  
	To generate a secret key, you can use:
	```powershell
	[guid]::NewGuid().ToString("N")
	```

6. **Run the application:**
   ```powershell
   uvicorn app.main:app --reload
   ```
   The app will be available at [http://localhost:8000](http://localhost:8000)

7. **Access the frontend:**
   - Open [http://localhost:8000](http://localhost:8000) in your browser.

8. **API Docs (local):**
   - [http://localhost:8000/docs](http://localhost:8000/docs)

---

### SQL Scripts to Create Local Database
Create Database Stucture

```sql
-- Create Database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'DrivingServiceManagement')
    CREATE DATABASE DrivingServiceManagement;
GO

-- Use the Database
USE DrivingServiceManagement;
GO

-- Create Users Table if not exists
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'Users') AND type = N'U')
BEGIN
    CREATE TABLE Users (
        user_id INT PRIMARY KEY IDENTITY(1,1),
        username NVARCHAR(50) NOT NULL UNIQUE,
        password NVARCHAR(255) NOT NULL,
        email NVARCHAR(100) NOT NULL UNIQUE,
        is_admin BIT NOT NULL
    );
END
GO

-- Create Car Insurance Policy Table if not exists
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'CarInsurancePolicy') AND type = N'U')
BEGIN
    CREATE TABLE CarInsurancePolicy (
        ci_policy_id INT PRIMARY KEY IDENTITY(1,1),
        user_id INT NOT NULL,
        vrn NVARCHAR(20) NOT NULL,
        make NVARCHAR(50) NOT NULL,
        model NVARCHAR(50) NOT NULL,
        policy_number NVARCHAR(50) NOT NULL UNIQUE,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        coverage NVARCHAR(255) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    );
END
GO

-- Create Optional Extras Table if not exists
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'OptionalExtras') AND type = N'U')
BEGIN
    CREATE TABLE OptionalExtras (
        extra_id INT PRIMARY KEY IDENTITY(1,1),
        name NVARCHAR(50) NOT NULL UNIQUE,
        code NVARCHAR(20) NOT NULL UNIQUE,
        price DECIMAL(10,2) NOT NULL
    );
END
GO

-- Create Car Insurance Policy Optional Extras Table if not exists
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'CarInsurancePolicyOptionalExtras') AND type = N'U')
BEGIN
    CREATE TABLE CarInsurancePolicyOptionalExtras (
        ci_policy_id INT NOT NULL,
        extra_id INT NOT NULL,
        FOREIGN KEY (ci_policy_id) REFERENCES CarInsurancePolicy(ci_policy_id),
        FOREIGN KEY (extra_id) REFERENCES OptionalExtras(extra_id),
        PRIMARY KEY (ci_policy_id, extra_id)
    );
END
GO
```

Insert Dummy Records - Records created below are for demonstration purposes. There are at least 10 records in each table in production.
```sql
-- Use the Database
USE DrivingServiceManagement;
GO

-- Insert into Users Table
INSERT INTO Users (username, password, email, is_admin) VALUES
('admin1', 'password123', 'admin1@example.com', 1),
('member1', 'password123', 'member1@example.com', 0),
('member2', 'password123', 'member2@example.com', 0);
GO

-- Insert into Car Insurance Policy Table
INSERT INTO CarInsurancePolicy (user_id, vrn, make, model, policy_number, start_date, end_date, coverage) VALUES
(2, 'ABC123', 'Toyota', 'Corolla', 'CI12345', '2025-01-01', '2026-01-01', 'Full Coverage'),
(2, 'XYZ789', 'Honda', 'Civic', 'CI67890', '2025-02-01', '2026-02-01', 'Third Party'),
(3, 'LMN456', 'Ford', 'Focus', 'CI11111', '2025-03-01', '2026-03-01', 'Full Coverage');
GO

-- Insert into Optional Extras Table
INSERT INTO OptionalExtras (name, code, price) VALUES
('Roadside Assistance', 'RA001', 50.00),
('Comprehensive', 'COMP002', 100.00),
('Personal Accident Cover', 'PAC003', 75.00);
GO

-- Insert into Car Insurance Policy Optional Extras Table
INSERT INTO CarInsurancePolicyOptionalExtras (ci_policy_id, extra_id) VALUES
(1, 1),
(1, 2),
(2, 3),
(3, 1),
(3, 3);
GO
```

---

## 🧑‍💻 Coding Techniques & Best Practices

- **Separation of Concerns:** Service, data, and presentation layers are modularized.
- **Type Hints & Pydantic Models:** For data validation and clear API contracts.
- **Error Handling:** Centralised error constants and response formatting.
- **Testing:** Unit tests for core modules in the `tests/` directory.
- **Environment Configuration:** Settings managed via `config.py`.
- **Static & Template Organisation:** All static assets and templates are under `app/static/` and `app/templates/`.

---

## 🧪 Testing

Run all tests with:
```powershell
$env:PYTHONPATH = "$PWD"
pytest
```

---

## 📁 Folder Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app entrypoint
│   ├── controllers/           # API route controllers
│   ├── models/                # Pydantic models
│   ├── services/              # Business logic/services
│   ├── utils/                 # Utility modules (db, config, etc)
│   ├── static/                # CSS, JS, images
│   └── templates/             # Jinja2 HTML templates
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Containerisation
├── run.py                     # Detects environment from .env and runs application
└── README.md                  # Project documentation
```

---
