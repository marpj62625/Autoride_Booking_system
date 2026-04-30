# AutoRide System - Setup & Installation Guide

## Prerequisites
- Python 3.8 or higher  
- Supabase Account (PostgreSQL)
- pip (Python package manager)

## Installation Steps

### 1. Install Python Dependencies
```bash
cd AutorideSystem/backend
pip install -r requirements.txt
```

### 2. Configure Supabase Connection
Edit `backend/config.py` and update `SUPABASE_DB_URL` with your Supabase PostgreSQL connection string:
```python
# Example Format:
SUPABASE_DB_URL = 'postgresql://postgres.[PROJ_ID]:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres'
```

### 3. Set Up Database Schema
Run the database setup script to create all tables and insert mock data into your Supabase instance:
```bash
python setup_db.py
```

You should see output like:
```
Setting up Supabase PostgreSQL database...
Table 'admins' created or verified successfully.
Table 'users' created or verified successfully.
...
Mock vehicle data inserted successfully.
Database setup complete.
```

### 4. Run the Backend Server
```bash
python app.py
```

The server is currently configured to run on **Port 9999** to ensure compatibility with mobile network firewalls.
- **Backend API**: `http://127.0.0.1:9999`
- **Public Site**: [http://localhost:8080](http://localhost:8080) (Run `python -m http.server 8080` in `frontend/`)
- **Admin App**: [http://localhost:8081](http://localhost:8081) (Run `python -m http.server 8081` in `admin_app/`)

---

## 📱 Mobile Setup (Capacitor)
The Admin Mobile app is configured to talk to your local IP address.
1. Ensure your PC and Phone are on the **SAME Wi-Fi**.
2. Open `admin_mobile/www/index.html` and verify `API_BASE` matches your PC's IPv4 address (e.g., `http://192.168.1.14:9999`).
3. Run `npx cap sync` in the `admin_mobile` folder.
4. Open the project in **Android Studio** and click **Run**.

---

## Troubleshooting

### "Failed to fetch" on Mobile
- Ensure **Windows Defender Firewall** is allowing Port 9999.
- Check that `API_BASE` in the mobile code matches your computer's IP exactly.

### Database Connection Errors
- Verify your `SUPABASE_DB_URL` in `config.py` is correct.
- Ensure your Supabase project is "Active" and not paused.

### ModuleNotFoundError
- Ensure you installed requirements: `pip install -r requirements.txt`
- Check you're in the correct directory (`backend/`)

---

## API Endpoints Overview
Once running, the backend provides:
- **POST /register** - User registration
- **POST /login** - User login
- **GET /vehicles** - List all vehicles
- **POST /booking** - Create a new booking
- **GET /reports/** - Various reporting endpoints

Full API logic is located in the `backend/` directory.

---

## Development Notes
- All database state persists in your **Supabase Cloud** instance.
- Port **9999** is used to avoid standard port blocking on local networks.
- `[LEGACY] autoride.sql` in the `database/` folder is for schema reference only.
