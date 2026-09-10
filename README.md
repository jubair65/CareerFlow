# CareerFlow — Local Development Setup

This document guides you through setting up the CareerFlow project for local development. CareerFlow is an AI-powered Presentation & Recruitment Coach built with React and Django. Follow these steps to clone the repository, install dependencies, configure the database, and run the complete application locally.

---

## Technology Stack

| Component | Technology | Version |
| --- | --- | --- |
| Frontend Framework | React | 19.0.0 |
| Frontend Language | TypeScript | 5.7.3 |
| Build Tool | Vite | 6.1.0 |
| CSS Framework | Tailwind CSS | 4.0.6 |
| Backend Framework | Django | 6.1.1 |
| REST API | Django REST Framework | 3.18.0 |
| Authentication | JWT (simplejwt) | 5.5.1 |
| Database | MySQL | 5.7+ / 8.0+ |
| Database Connector | PyMySQL | 1.2.0 |
| HTTP Client | Axios | 1.7.9 |
| API State Management | React Query (@tanstack/react-query) | 5.66.0 |
| Routing | Wouter | 3.5.1 |

---

## Prerequisites

Before you begin, ensure the following software is installed on your system:

### 1. Git

**Purpose:** Version control for cloning the repository.

**Installation:**
- **Windows:** Download from https://git-scm.com/ and run the installer
- **macOS:** `brew install git`
- **Linux (Ubuntu/Debian):** `sudo apt-get install git`

**Verify:**
```bash
git --version
```

Expected output: `git version 2.x.x` or higher

---

### 2. Python

**Purpose:** Required for the Django backend.

**Minimum Version:** Python 3.9

**Installation:**
- **Windows:** Download from https://www.python.org/ and run the installer. Check "Add Python to PATH" during installation.
- **macOS:** `brew install python3`
- **Linux (Ubuntu/Debian):** `sudo apt-get install python3 python3-pip python3-venv`

**Verify:**
```bash
python --version
```
or on macOS/Linux:
```bash
python3 --version
```

Expected output: `Python 3.9.x` or higher

---

### 3. Node.js and npm

**Purpose:** Required for the React frontend.

**Minimum Version:** Node.js 18.x, npm 9.x

**Installation:**
- **Windows & macOS:** Download from https://nodejs.org/ (LTS version recommended)
- **Linux (Ubuntu/Debian):** `sudo apt-get install nodejs npm`

**Verify:**
```bash
node --version
npm --version
```

Expected output: `v18.x.x` or higher for Node.js, `9.x.x` or higher for npm

---

### 4. MySQL Server

**Purpose:** Database for storing application data.

**Minimum Version:** MySQL 5.7 or MySQL 8.0

**Installation:**
- **Windows:** Download MySQL Community Server from https://dev.mysql.com/downloads/mysql/ and run the installer
- **macOS:** `brew install mysql` or download from MySQL website
- **Linux (Ubuntu/Debian):** `sudo apt-get install mysql-server`

**Verify:**
```bash
mysql --version
```

Expected output: `mysql Ver 8.0.x` or higher

**Start MySQL Service:**
- **Windows:** MySQL is typically started automatically or via Services panel
- **macOS:** `brew services start mysql`
- **Linux (Ubuntu/Debian):** `sudo systemctl start mysql` or `sudo service mysql start`

---

## Clone the Repository

Navigate to your desired project directory and clone the repository:

```bash
git clone https://github.com/jubair65/CareerFlow.git
cd CareerFlow
```

### Select the Development Branch

The project uses two main branches:

- **`main`** — Stable, production-ready version
- **`develop`** — Active development branch (for team members)

For local development, checkout the `develop` branch:

```bash
git checkout develop
git pull origin develop
```

---

## Project Structure

The CareerFlow project is organized as follows:

```
CareerFlow/
├── backend/                          # Django backend
│   ├── careerflow/                   # Django project configuration
│   │   ├── settings.py               # Django settings
│   │   ├── urls.py                   # URL routing
│   │   ├── wsgi.py                   # WSGI configuration
│   │   └── asgi.py                   # ASGI configuration
│   ├── apps/                         # Django applications
│   │   ├── authentication/           # User authentication app
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── migrations/
│   │   └── core/                     # Core functionality app
│   │       ├── models.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── migrations/
│   ├── manage.py                     # Django management script
│   ├── requirements.txt              # Python dependencies
│   └── .env.example                  # Environment variables template
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── api/                      # API client functions
│   │   │   └── auth.ts               # Authentication API configuration
│   │   ├── components/               # Reusable React components
│   │   ├── pages/                    # Page components
│   │   ├── App.tsx                   # Main App component
│   │   ├── main.tsx                  # Entry point
│   │   └── index.css                 # Global styles
│   ├── public/                       # Static assets
│   ├── package.json                  # npm dependencies and scripts
│   ├── package-lock.json             # npm lockfile
│   ├── vite.config.ts                # Vite configuration
│   ├── tsconfig.json                 # TypeScript configuration
│   └── index.html                    # HTML template
├── .gitignore                        # Git ignore rules
└── LOCAL_SETUP.md                    # This file

```

---

# BACKEND SETUP

## Backend Overview

The CareerFlow backend is built with Django 6.1.1 and Django REST Framework (DRF), providing a RESTful API for the frontend React application.

**Key Components:**

- **Django Project:** `backend/careerflow/` — Main project configuration
- **Django Apps:** 
  - `authentication` — User registration, login, logout, JWT token management
  - `core` — Core business logic for presentations and recruitment features
- **Database:** MySQL with PyMySQL connector
- **Authentication:** JWT tokens (via `djangorestframework_simplejwt`)
- **API Endpoints:** All prefixed with `/api/` (e.g., `/api/auth/`, `/api/core/`)
- **Development Server:** Runs on `http://127.0.0.1:8000`

**API Structure:**
```
http://127.0.0.1:8000/
├── /admin/              # Django admin panel
├── /api/auth/           # Authentication endpoints (register, login, logout, token refresh)
└── /api/core/           # Core feature endpoints
```

---

## Create Python Virtual Environment

A Python virtual environment isolates project dependencies, preventing conflicts with other Python projects on your system.

### macOS/Linux

```bash
cd CareerFlow/backend
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
cd CareerFlow\backend
python -m venv venv
venv\Scripts\activate
```

**Verify Activation:**

You should see `(venv)` prefix in your terminal prompt. If successful, the virtual environment is active. When you finish development, deactivate it with:

```bash
deactivate
```

---

## Install Backend Dependencies

Install all Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

**What's Installed:**

- **Django** (6.1.1) — Web framework
- **djangorestframework** (3.18.0) — REST API framework
- **djangorestframework_simplejwt** (5.5.1) — JWT authentication
- **django-cors-headers** (4.9.0) — CORS support for frontend
- **PyMySQL** (1.2.0) — MySQL database connector
- **python-dotenv** (1.2.3) — Environment variable loading

This step may take 1-2 minutes depending on your internet speed.

---

## Environment Variables

### Create .env File

The backend uses a `.env` file to store sensitive configuration. 

**Step 1:** Copy the template file:

### macOS/Linux
```bash
cd backend
cp .env.example .env
```

### Windows
```bash
cd backend
copy .env.example .env
```

**Step 2:** Open `backend/.env` in your text editor and update the values:

### Default .env File

```env
# Django Configuration
SECRET_KEY=careerflow-django-insecure-key-for-development-sprint1
DEBUG=True

# MySQL Database Configuration
DB_NAME=careerflow_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Frontend CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Environment Variable Reference

| Variable | Purpose | Default | Notes |
| --- | --- | --- | --- |
| `SECRET_KEY` | Django secret for session and token signing | `careerflow-django-insecure-key-for-development-sprint1` | Use a strong random key in production |
| `DEBUG` | Enable debug mode for development | `True` | **Always set to `False` in production** |
| `DB_NAME` | MySQL database name | `careerflow_db` | Name of the database to create |
| `DB_USER` | MySQL username | `root` | Usually `root` on local machines |
| `DB_PASSWORD` | MySQL password | `your_mysql_password` | **Update with your MySQL password** |
| `DB_HOST` | MySQL server address | `127.0.0.1` | Use `localhost` or `127.0.0.1` for local development |
| `DB_PORT` | MySQL port | `3306` | Standard MySQL port |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend URLs | `http://localhost:5173,http://127.0.0.1:5173` | URLs from which API requests are accepted |

### Required Changes

After copying `.env.example` to `.env`, **you must change:**

1. **`DB_PASSWORD`** — Set to your MySQL root password (or the password of the MySQL user you created)

### Security Warning

> ⚠️ **CRITICAL:** Never commit `.env` or real credentials to GitHub. The `.gitignore` file already excludes `.env`, but always verify before pushing code. Store `.env.example` with placeholder values only.

---

# DATABASE SETUP

## MySQL Server Setup

Before running Django, you must create the MySQL database and user.

### Step 1: Connect to MySQL

Open a terminal/command prompt and log in to MySQL:

```bash
mysql -u root -p
```

When prompted, enter your MySQL root password.

**Expected Output:**
```
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is XXX
Server version: 8.0.x MySQL Community Server

Type 'help;' or '\h' for help.

mysql>
```

### Step 2: Create the Database

Inside the MySQL prompt, create the database:

```sql
CREATE DATABASE careerflow_db;
```

**Expected Output:**
```
Query OK, 1 row affected (0.02 sec)
```

### Step 3: Verify Database Creation

```sql
SHOW DATABASES;
```

You should see `careerflow_db` in the list.

### Step 4: Exit MySQL

```sql
EXIT;
```

### Step 5: Verify Database Connection in Django

Django will use the credentials from your `.env` file to connect to MySQL. This happens automatically during migrations (next section).

---

## Database Migrations

Django migrations create the necessary database tables and schema. **Important:** Fresh developers only need to run `migrate`; the migration files already exist in the repository.

### Run Migrations

Ensure you're in the `backend/` directory with the virtual environment activated, then run:

```bash
python manage.py migrate
```

**Expected Output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, authentication, sessions, ...
Running migrations:
  Applying authentication.0001_initial... OK
  Applying core.0001_initial... OK
  ...
```

This creates all required tables in the `careerflow_db` database.

### When to Use makemigrations

**Do NOT use `makemigrations` unless:**

- You have created a **new Django model** in one of the apps
- You have **modified an existing model** and need to track the changes

If someone on your team created migrations, simply run:

```bash
python manage.py migrate
```

For new model development:

```bash
python manage.py makemigrations        # Create migration files
python manage.py migrate               # Apply to database
```

---

## Create Superuser (Admin)

The superuser account lets you access the Django admin panel at `/admin/`.

```bash
python manage.py createsuperuser
```

You'll be prompted for:

```
Username: admin
Email: admin@example.com
Password: (enter a strong password)
Password (again): (confirm)
```

**Keep these credentials safe** — you'll use them to log into `/admin/`.

### Access Django Admin

Once the backend server is running (see "Running the Project" section):

1. Open: `http://127.0.0.1:8000/admin/`
2. Log in with your superuser credentials
3. Manage users, view database records, and test authentication

---

# FRONTEND SETUP

## Frontend Overview

The CareerFlow frontend is a modern React application built with Vite, TypeScript, and Tailwind CSS. It communicates with the Django backend via a RESTful API.

**Key Components:**

- **Framework:** React 19.0.0
- **Language:** TypeScript 5.7.3
- **Build Tool:** Vite 6.1.0
- **Styling:** Tailwind CSS 4.0.6
- **HTTP Client:** Axios
- **State Management:** React Query
- **Routing:** Wouter
- **UI Components:** Radix UI + custom components
- **Development Server:** Runs on `http://localhost:5173`

**Available npm Scripts (from package.json):**

| Task | Command |
| --- | --- |
| Start development server | `npm run dev` |
| Build for production | `npm run build` |
| Preview production build locally | `npm run preview` |

---

## Install Frontend Dependencies

Navigate to the frontend directory and install npm packages:

```bash
cd CareerFlow/frontend
npm install
```

**What Happens:**

1. npm reads `package.json` and `package-lock.json`
2. Downloads all dependencies to `node_modules/` folder
3. Creates/updates `package-lock.json` to lock versions

**This may take 2-5 minutes depending on your internet speed.**

**Important:** Do NOT commit `node_modules/` to GitHub — it's already in `.gitignore`.

---

## Start Frontend Development Server

Run the Vite development server:

```bash
npm run dev
```

**Expected Output:**
```
  VITE v6.1.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### Access the Frontend

Open your browser and navigate to:

```
http://localhost:5173/
```

The page will automatically reload when you save changes to source files (hot module reloading).

---

# FRONTEND + BACKEND CONNECTION

## API Configuration

The frontend communicates with the Django backend through a REST API. The configuration is set up in two places:

### 1. Vite Proxy Configuration

**File:** `frontend/vite.config.ts`

```typescript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
},
```

**What This Does:**

- When the browser makes a request to `/api/*`, Vite automatically forwards it to `http://127.0.0.1:8000/api/*`
- This avoids CORS issues during development
- Both frontend and backend must be running for this to work

### 2. Axios API Client Configuration

**File:** `frontend/src/api/auth.ts`

```typescript
const API_BASE = '/api';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**What This Does:**

- Sets the base URL for all API requests to `/api`
- Automatically attaches JWT access tokens to requests
- Handles token refresh (401 response) automatically
- Clears tokens on logout

### 3. JWT Authentication

Tokens are managed in localStorage with keys:

- `careerflow_access_token` — Access token (60-minute lifetime)
- `careerflow_refresh_token` — Refresh token (7-day lifetime)
- `careerflow_user` — Cached user object

### API Request Flow

```
Browser (React App)
    │
    └─ http://localhost:5173
        │
        ├─ GET /api/auth/me/
        │ (Vite Proxy intercepts)
        │
        ▼
    Vite Dev Server (localhost:5173)
        │
        ├─ Forwards to backend
        │
        ▼
    Django Backend
    http://127.0.0.1:8000
        │
        ├─ GET /api/auth/me/
        ├─ Process request
        ├─ Return JSON response
        │
        ▼
    Response returned to browser
```

### CORS Configuration

Django is configured to accept requests from:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

This is set in `backend/.env`:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

# RUNNING THE PROJECT

## Start Both Servers

The CareerFlow application requires **two running servers** — one terminal for the backend, one for the frontend.

### Terminal 1: Start Django Backend

**From the project root**, navigate to backend and activate the virtual environment:

#### macOS/Linux
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

#### Windows
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Expected Output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
September 10, 2026 - 12:00:00
Django version 6.1.1, using settings 'careerflow.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Backend is running at:** `http://127.0.0.1:8000`

---

### Terminal 2: Start Vite Frontend

**In a new terminal**, navigate to the frontend directory:

```bash
cd CareerFlow/frontend
npm run dev
```

**Expected Output:**
```
  VITE v6.1.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ **Frontend is running at:** `http://localhost:5173`

---

## Access the Application

1. **Open your browser** and go to: `http://localhost:5173/`
2. **The frontend should load**
3. **Test the connection** by registering or logging in (depending on implemented features)

---

## Verify the Application

Follow this checklist to confirm everything is working:

### Prerequisites Check
- [ ] MySQL service is running
- [ ] You're in the correct project directory
- [ ] Virtual environment is activated (backend terminal shows `(venv)`)
- [ ] All dependencies are installed (`pip install -r requirements.txt`, `npm install`)

### Backend Check
- [ ] Run `python manage.py runserver` in the backend terminal
- [ ] Navigate to `http://127.0.0.1:8000/admin/`
- [ ] Log in with superuser credentials
- [ ] You see the Django admin panel

### Frontend Check
- [ ] Run `npm run dev` in the frontend terminal
- [ ] Navigate to `http://localhost:5173/`
- [ ] The page loads without errors
- [ ] Open browser DevTools (F12) → Console tab — check for errors

### API Connection Check
- [ ] From the frontend, attempt to **register** or **login** (if implemented)
- [ ] Open browser DevTools (F12) → Network tab
- [ ] Verify that API requests to `/api/auth/...` show status `200` (success) or `400` (validation error)
- [ ] If requests fail with CORS or 502 errors, verify both servers are running

### Database Check
- [ ] Log into `http://127.0.0.1:8000/admin/`
- [ ] Navigate to the **Users** section
- [ ] Verify that user registrations/logins created database records

---

# TROUBLESHOOTING

This section addresses common setup errors and their solutions.

## Python / Django Errors

### Error: "python: command not found" or "python not recognized"

**Problem:** Python is not installed or not in your system PATH.

**Solution:**
1. Install Python from https://www.python.org/
2. **Windows only:** During installation, check the box "Add Python to PATH"
3. Verify: `python --version`
4. If on macOS/Linux, try `python3 --version` instead

---

### Error: "No module named 'django'" or ModuleNotFoundError

**Problem:** Django dependencies are not installed, or virtual environment is not activated.

**Solution:**
```bash
# Ensure you're in the backend directory
cd CareerFlow/backend

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Verify:** `pip list` should show `Django==6.1.1`

---

### Error: "virtual environment not activated" (Windows-specific)

**Problem:** Virtual environment activation script isn't found or doesn't execute.

**Cause:** Python may not be installed correctly, or the virtual environment folder is corrupted.

**Solution:**

1. **Delete the venv folder:**
   ```bash
   cd backend
   rmdir venv /s /q  # Windows
   rm -rf venv       # macOS/Linux
   ```

2. **Recreate the virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Error: "Could not find a version that satisfies the requirement"

**Problem:** pip cannot download a specific package version (network issue or deprecated version).

**Solution:**

```bash
# Update pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Try installing requirements again
pip install -r requirements.txt
```

---

### Error: "django.core.exceptions.ImproperlyConfigured: Error loading MySQLdb module"

**Problem:** PyMySQL is not installed or Django can't connect to MySQL.

**Solution:**

1. **Ensure PyMySQL is installed:**
   ```bash
   pip install PyMySQL==1.2.0
   ```

2. **Ensure MySQL is running:**
   ```bash
   # macOS:
   brew services start mysql
   # Linux:
   sudo systemctl start mysql
   # Windows:
   # Start MySQL from Services panel or Start Menu
   ```

3. **Verify MySQL connection manually:**
   ```bash
   mysql -u root -p
   # Enter your MySQL password
   SHOW DATABASES;  # Should list careerflow_db
   EXIT;
   ```

---

### Error: "django.db.utils.OperationalError: (1049, "Unknown database 'careerflow_db'")"

**Problem:** The database `careerflow_db` does not exist in MySQL.

**Solution:**

1. **Create the database:**
   ```bash
   mysql -u root -p
   # Enter your MySQL password
   CREATE DATABASE careerflow_db;
   EXIT;
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

---

### Error: "django.db.utils.OperationalError: Access denied for user 'root'@'127.0.0.1'"

**Problem:** Database credentials in `.env` are incorrect.

**Solution:**

1. **Verify MySQL root password:**
   ```bash
   mysql -u root -p
   # If you can log in, your password is correct
   EXIT;
   ```

2. **Update `.env` with correct credentials:**
   ```env
   DB_USER=root
   DB_PASSWORD=your_actual_mysql_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

3. **Test the connection:**
   ```bash
   python manage.py migrate
   ```

---

### Error: "django.db.migrations.exceptions.MigrationError"

**Problem:** Database migration failed, usually due to schema issues or conflicting migrations.

**Solution:**

1. **Check migration status:**
   ```bash
   python manage.py showmigrations
   ```

2. **If migrations are stuck, try:**
   ```bash
   python manage.py migrate --fake-initial
   ```

3. **If still stuck, consider resetting the database** (development only):
   ```bash
   # DELETE THE DATABASE AND RECREATE IT
   mysql -u root -p
   DROP DATABASE careerflow_db;
   CREATE DATABASE careerflow_db;
   EXIT;
   
   python manage.py migrate
   ```

---

## Frontend / Node.js Errors

### Error: "npm: command not found" or "npm not recognized"

**Problem:** Node.js/npm is not installed or not in PATH.

**Solution:**

1. Install Node.js from https://nodejs.org/ (LTS version)
2. **Windows only:** Restart your terminal/command prompt after installation
3. Verify: `npm --version` and `node --version`

---

### Error: npm ERR! code ERESOLVE or dependency conflicts

**Problem:** npm cannot resolve conflicting dependencies.

**Solution:**

```bash
cd frontend

# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json  # macOS/Linux
rmdir node_modules /s /q  # Windows, then delete package-lock.json

# Reinstall
npm install
```

---

### Error: "Cannot find module '@vite/plugin-react'" or similar module errors

**Problem:** Dependencies aren't fully installed.

**Solution:**

```bash
cd frontend
npm install
```

---

### Error: "Port 5173 is already in use"

**Problem:** Another process is using port 5173, or a previous Vite server didn't shut down cleanly.

**Solution:**

**Option 1: Kill the process using port 5173**

#### macOS/Linux
```bash
lsof -i :5173  # List process using port 5173
kill -9 <PID>  # Kill the process
```

#### Windows
```bash
netstat -ano | findstr :5173           # Find process ID
taskkill /PID <PID> /F                 # Kill the process
```

**Option 2: Use a different port**

```bash
npm run dev -- --port 5174
```

---

### Error: "Cannot GET /" or blank page at localhost:5173

**Problem:** The Vite server is running, but the app isn't loading.

**Solution:**

1. **Check browser DevTools console (F12):**
   - Look for error messages
   - Common error: `Proxy error` or `Cannot connect to http://127.0.0.1:8000`

2. **Verify both servers are running:**
   ```bash
   # Backend should be running at 127.0.0.1:8000
   # Frontend should be running at 127.0.0.1:5173
   ```

3. **Restart Vite:**
   ```bash
   # In the frontend terminal
   npm run dev
   ```

---

### Error: "Vite failed to resolve '@/...' imports"

**Problem:** TypeScript path alias `@` is not resolving correctly.

**Solution:**

The alias should be configured in `vite.config.ts` (already done). Try:

1. Restart the dev server: `npm run dev`
2. Clear browser cache (Ctrl+Shift+Delete) and refresh
3. If persists, check `vite.config.ts` has:
   ```typescript
   resolve: {
     alias: {
       '@': path.resolve(__dirname, 'src'),
     },
   },
   ```

---

## API / Communication Errors

### Error: CORS Error — "Access to XMLHttpRequest at '...' from origin 'http://localhost:5173' has been blocked"

**Problem:** Django isn't configured to accept requests from the frontend URL.

**Solution:**

1. **Verify `backend/.env`:**
   ```env
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

2. **Verify `backend/careerflow/settings.py`:**
   ```python
   INSTALLED_APPS = [
       ...
       'corsheaders',
       ...
   ]
   
   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',  # Must be first
       ...
   ]
   ```

3. **Restart Django:**
   ```bash
   python manage.py runserver
   ```

---

### Error: "Failed to fetch" or "Network request failed" from frontend

**Problem:** Frontend cannot reach the backend API.

**Causes:**
- Django backend is not running
- Vite proxy target is incorrect
- Firewall is blocking port 8000

**Solution:**

1. **Verify Django is running:**
   ```bash
   # Should see "Starting development server at http://127.0.0.1:8000/"
   ```

2. **Test Django directly (no Vite proxy):**
   ```bash
   curl http://127.0.0.1:8000/api/auth/me/  # macOS/Linux
   # Should return 401 Unauthorized (expected, no token)
   ```

3. **Verify Vite proxy configuration** in `frontend/vite.config.ts`:
   ```typescript
   proxy: {
     '/api': {
       target: 'http://127.0.0.1:8000',
       changeOrigin: true,
     },
   },
   ```

4. **Restart both servers:**
   ```bash
   # Terminal 1: Stop Django (Ctrl+C), restart
   python manage.py runserver
   
   # Terminal 2: Stop Vite (Ctrl+C), restart
   npm run dev
   ```

---

### Error: HTTP 401 Unauthorized for login requests

**Problem:** Usually means credentials are wrong or the endpoint is incorrect.

**Solution:**

1. **Verify the endpoint exists:** `POST /api/auth/login/`
2. **Check request payload:**
   ```json
   {
     "email": "user@example.com",
     "password": "password123"
   }
   ```

3. **Test with curl (macOS/Linux):**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password123"}'
   ```

4. **Check Django logs** in the backend terminal for more details.

---

### Error: HTTP 500 Internal Server Error

**Problem:** Django encountered an error processing the request.

**Solution:**

1. **Check backend terminal** — error details are printed there
2. **Check Django logs** for the full error stack trace
3. **Common causes:**
   - Database connection error
   - Missing migration
   - Typo in view/serializer
   - Environment variable not set

4. **Restart Django:**
   ```bash
   python manage.py runserver
   ```

---

## MySQL / Database Errors

### Error: "MySQL server has gone away"

**Problem:** MySQL server crashed or stopped.

**Solution:**

1. **Restart MySQL:**
   ```bash
   # macOS:
   brew services restart mysql
   # Linux:
   sudo systemctl restart mysql
   # Windows:
   # Restart via Services panel
   ```

2. **Restart Django:**
   ```bash
   python manage.py runserver
   ```

---

### Error: "Access denied for user 'root'@'localhost'"

**Problem:** MySQL password in `.env` is incorrect, or MySQL root password hasn't been set.

**Solution:**

1. **Reset MySQL root password** (if forgotten):
   - Consult MySQL documentation for your OS
   - Or reinstall MySQL

2. **Update `.env`:**
   ```env
   DB_USER=root
   DB_PASSWORD=your_correct_password
   ```

3. **Test connection:**
   ```bash
   mysql -u root -p  # Enter password from .env
   ```

---

### Error: "Unknown database 'careerflow_db'"

**Problem:** Database hasn't been created.

**Solution:**

```bash
mysql -u root -p
CREATE DATABASE careerflow_db;
EXIT;

python manage.py migrate
```

---

## General Troubleshooting Tips

### 1. Check File Permissions

Ensure you have read/write permissions on the project folder:

```bash
# macOS/Linux:
chmod -R u+rwx CareerFlow/
```

---

### 2. Update All Tools

Outdated versions of npm, pip, or Node.js can cause issues:

```bash
# Update pip
pip install --upgrade pip

# Update npm
npm install -g npm@latest

# Update Node.js: Download and reinstall from https://nodejs.org/
```

---

### 3. Clear Caches

```bash
# npm cache
npm cache clean --force

# Python cache
cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Browser cache
# Chrome: Ctrl+Shift+Delete (Windows/Linux) or Cmd+Shift+Delete (macOS)
```

---

### 4. Restart Everything

When in doubt, restart all services:

```bash
# Kill backend and frontend (Ctrl+C in respective terminals)

# Restart MySQL
# macOS: brew services restart mysql
# Linux: sudo systemctl restart mysql
# Windows: Services panel

# Restart backend
python manage.py runserver

# Restart frontend
npm run dev
```

---

### 5. Check Logs

- **Django logs:** Printed in the backend terminal
- **Vite logs:** Printed in the frontend terminal
- **Browser console:** Press F12 in browser, click "Console" tab
- **Network tab:** F12 → Network tab shows all HTTP requests/responses

---

### 6. Seek Help

If you're still stuck:

1. **Read error messages carefully** — they often explain the problem
2. **Search the error online** — others have likely encountered it
3. **Check GitHub issues** at https://github.com/jubair65/CareerFlow/issues
4. **Ask your team** — describe what you did and what error you got

---

# DEVELOPMENT COMMANDS

## Backend Commands

Common Django management commands:

| Task | Command |
| --- | --- |
| Start development server | `python manage.py runserver` |
| Create new migration | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Create superuser | `python manage.py createsuperuser` |
| System checks | `python manage.py check` |
| Django shell | `python manage.py shell` |
| Collect static files | `python manage.py collectstatic` |

---

## Frontend Commands

Common npm commands:

| Task | Command |
| --- | --- |
| Install dependencies | `npm install` |
| Start dev server | `npm run dev` |
| Build for production | `npm run build` |
| Preview production build | `npm run preview` |
| Update dependencies | `npm update` |
| Check outdated packages | `npm outdated` |

---

# GIT WORKFLOW

## Branch Strategy

CareerFlow uses the following branch strategy:

```
main (stable)
 │
 ├── Release versions (tagged)
 │
develop (development)
 │
 ├── feature/user-authentication
 ├── feature/presentation-coach
 ├── bug-fix/login-issue
 └── ...
```

**Branch Purposes:**

- **`main`** — Stable, production-ready code. Only updated for releases.
- **`develop`** — Active development. All features merged here first.
- **`feature/*`** — New features (branch from `develop`)
- **`bug-fix/*`** — Bug fixes (branch from `develop`)

---

## Recommended Workflow

### 1. Start Work on a New Feature

```bash
# Ensure you're up-to-date
git checkout develop
git pull origin develop

# Create a feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Conventions:**

- Features: `feature/feature-name` (e.g., `feature/jwt-authentication`)
- Bug fixes: `bug-fix/bug-description` (e.g., `bug-fix/login-redirect`)
- Improvements: `improvement/description` (e.g., `improvement/api-performance`)

---

### 2. Make Changes and Commit

```bash
# Make your changes in your code editor
# ...

# Stage changes
git add .

# Commit with a descriptive message
git commit -m "Add JWT token refresh endpoint"
```

**Commit Message Guidelines:**

- Start with an action verb: "Add", "Fix", "Improve", "Refactor"
- Be specific about what changed
- Keep it concise (< 72 characters)
- Examples:
  - ✅ "Add user profile endpoint"
  - ✅ "Fix authentication token expiration"
  - ❌ "fixed stuff"
  - ❌ "changes"

---

### 3. Push to Remote and Create Pull Request

```bash
# Push your branch to GitHub
git push origin feature/your-feature-name
```

Then on GitHub:

1. Navigate to your repository
2. You'll see a prompt to create a Pull Request
3. Fill in the PR description
4. Request a code review from a team member
5. Address feedback from reviewers
6. Once approved, merge into `develop`

---

### 4. Delete the Feature Branch

After merging to `develop`:

```bash
# Delete local branch
git branch -d feature/your-feature-name

# Delete remote branch
git push origin --delete feature/your-feature-name
```

---

## Daily Workflow

```bash
# Start your day — sync with latest develop
git checkout develop
git pull origin develop

# Continue work on your feature
git checkout feature/your-feature-name
git pull origin feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Your descriptive message"

# Push changes
git push origin feature/your-feature-name

# End of day — sync again
git checkout develop
git pull origin develop
```

---

## Avoiding Merge Conflicts

1. **Regularly pull from develop:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/your-feature
   git merge develop
   ```

2. **Push frequently** to keep your remote branch updated

3. **Communicate with team** — know who's working on which files

4. **If conflict occurs:**
   ```bash
   # Open the conflicted files
   # Look for <<<<<<, ======, >>>>>> markers
   # Manually resolve conflicts
   # Stage and commit
   git add .
   git commit -m "Resolve merge conflict"
   git push origin feature/your-feature
   ```

---

# SECURITY

Always follow these security practices when developing CareerFlow:

## Secrets Management

- ❌ **Never commit `.env`** — contains sensitive credentials
- ✅ **Always use `.env.example`** with placeholder values
- ✅ **Store `.env` in a secure location** (e.g., your local machine only)
- ❌ **Never share database passwords, API keys, or secrets**
- ✅ **Use environment variables** for all sensitive data

---

## Database Credentials

- ❌ **Never hardcode passwords** in code
- ✅ **Always read from `.env`** using `os.getenv()`
- ❌ **Don't commit credentials** to Git
- ✅ **Use strong passwords** for development databases (even locally)
- ✅ **Use different credentials** for production vs. development

---

## API Security

- ✅ **Use HTTPS in production** (Django `SECURE_SSL_REDIRECT`)
- ✅ **Keep `DEBUG=False` in production** (prevents exposing sensitive info)
- ✅ **Use strong `SECRET_KEY`** in production (randomized, not default)
- ✅ **Enable CSRF protection** (Django default)
- ✅ **Validate all user input** (serializers, forms)
- ✅ **Implement rate limiting** for login attempts (future)

---

## Frontend Security

- ✅ **Store tokens in localStorage** (as currently implemented)
- ✅ **Clear tokens on logout** (removes from localStorage)
- ✅ **Use HTTPS only** for API calls in production
- ✅ **Validate all API responses** before using in UI
- ❌ **Don't log sensitive data** (passwords, tokens) to console

---

## Git Security

- ❌ **Never commit `.env`** file
- ❌ **Never commit `node_modules`** or `venv` directories
- ❌ **Never commit IDE settings** with sensitive info
- ✅ **Review `.gitignore`** before committing
- ✅ **Use `.env.example`** to document required variables

---

## Development Checklist

- [ ] `.env` is in `.gitignore`
- [ ] No hardcoded passwords in source code
- [ ] No API keys or secrets in Git history
- [ ] Virtual environment (`venv`) is not committed
- [ ] `node_modules` is not committed
- [ ] `.env.example` contains only placeholders
- [ ] Production credentials are never used locally
- [ ] All teammates have their own `.env` file

---

# COMPLETE QUICK START

For developers who already have all prerequisites installed, here's the fastest way to get up and running:

## Quick Start Script

```bash
# Clone repository
git clone https://github.com/jubair65/CareerFlow.git
cd CareerFlow
git checkout develop

# ===== BACKEND SETUP =====
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# ⚠️  EDIT .env and set DB_PASSWORD

# Create database (in MySQL CLI)
mysql -u root -p
CREATE DATABASE careerflow_db;
EXIT;

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start backend (keep terminal open)
python manage.py runserver
# ✅ Backend ready at http://127.0.0.1:8000

# ===== FRONTEND SETUP (NEW TERMINAL) =====
cd CareerFlow/frontend
npm install
npm run dev
# ✅ Frontend ready at http://localhost:5173

# ===== DONE =====
# Open browser: http://localhost:5173/
# Test with superuser credentials
```

---

# SETUP VERIFICATION CHECKLIST

Use this checklist to verify your local setup is complete and working:

### Prerequisites
- [ ] Git installed (`git --version`)
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm 9+ installed (`npm --version`)
- [ ] MySQL 5.7+ installed and running (`mysql --version`)

### Repository
- [ ] Repository cloned (`git clone https://github.com/jubair65/CareerFlow.git`)
- [ ] `develop` branch checked out (`git branch` shows `develop`)
- [ ] All files present (`ls backend/`, `ls frontend/`)

### Backend Setup
- [ ] Virtual environment created (`backend/venv/` exists)
- [ ] Virtual environment activated (`(venv)` in prompt)
- [ ] Dependencies installed (`pip list | grep Django`)
- [ ] `.env` file created and configured (`backend/.env` exists)
- [ ] Database created (`mysql -u root -p`, then `SHOW DATABASES;`)
- [ ] Migrations applied (`python manage.py showmigrations` shows all `[X]`)
- [ ] Superuser created (`python manage.py createsuperuser` completed)
- [ ] Django runs without errors (`python manage.py runserver`)

### Frontend Setup
- [ ] Dependencies installed (`frontend/node_modules/` exists)
- [ ] Vite starts (`npm run dev` shows no errors)
- [ ] Page loads (`http://localhost:5173/` opens in browser)
- [ ] Console clear of errors (F12 → Console tab is clean)

### Integration
- [ ] Both servers running simultaneously (Terminal 1: Django, Terminal 2: Vite)
- [ ] Frontend loads at `http://localhost:5173/`
- [ ] Backend accessible at `http://127.0.0.1:8000/`
- [ ] Admin panel accessible at `http://127.0.0.1:8000/admin/`
- [ ] Browser Network tab shows API requests to `/api/` with status 200 (or expected error codes)
- [ ] No CORS errors in browser console

### Database
- [ ] Database connection established (no "Unknown database" errors)
- [ ] Tables created (`mysql` → `USE careerflow_db;` → `SHOW TABLES;`)
- [ ] Admin panel shows Users table (`http://127.0.0.1:8000/admin/authentication/user/`)

### Ready to Develop
- [ ] Can create new feature branch (`git checkout -b feature/test-feature`)
- [ ] Can make code changes and see them reload (Vite hot reload)
- [ ] Can commit changes (`git add .` → `git commit -m "test"`)
- [ ] Understand Git workflow (feature → develop → main)

✅ **If all items are checked, your setup is complete and working!**

---

## Next Steps

Now that CareerFlow is running locally:

1. **Explore the codebase:**
   - Review `backend/apps/authentication/` for auth implementation
   - Review `frontend/src/` for React component structure
   - Read API documentation if available

2. **Start developing:**
   - Create a feature branch: `git checkout -b feature/your-feature`
   - Make changes in `frontend/src/` or `backend/apps/`
   - Test locally (both servers running)
   - Commit and push: `git push origin feature/your-feature`

3. **Collaborate:**
   - Create Pull Requests on GitHub
   - Request code reviews from teammates
   - Address feedback and iterate
   - Merge into `develop` when approved

4. **Keep learning:**
   - Review Django REST Framework docs: https://www.django-rest-framework.org/
   - Review React docs: https://react.dev/
   - Review Vite docs: https://vitejs.dev/

---

## Support

If you encounter issues:

1. **Check the Troubleshooting section** above (covers most common errors)
2. **Search GitHub Issues:** https://github.com/jubair65/CareerFlow/issues
3. **Ask your team** — describe the error and what you did
4. **Read error messages carefully** — they often explain the root cause

---

## Contributing

Thank you for contributing to CareerFlow! Please:

1. Follow this setup guide
2. Use the Git workflow described
3. Test locally before pushing
4. Write clear commit messages
5. Create detailed Pull Requests
6. Respond to code reviews respectfully

Happy coding! 🚀
