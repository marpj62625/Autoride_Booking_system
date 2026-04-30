# Supabase Database Setup Guide

This guide describes how to initialize your Supabase PostgreSQL database for the AutoRide system.

## 1. Credentials
Ensure your `backend/config.py` contains the correct `SUPABASE_DB_URL`. You can find this in your Supabase Project Settings under **Database > Connection String**.

## 2. Table Creation & Initial Data
To create all necessary tables and insert initial mock data, run the setup script:

```bash
cd AutorideSystem/backend
python setup_db.py
```

This script will:
- Create core tables (`users`, `vehicles`, `bookings`, `drivers`, etc.)
- Create enterprise feature tables (`pickup_instructions`, `contact_queries`, etc.)
- Insert initial mock vehicles for testing.

## 3. Applying Updates
If you are coming from an older version of the system and need to apply the latest database schema updates (like enterprise features or account freezing), run the update script:

```bash
python update_db.py
```

## 4. Testing Connectivity
To verify that your Python environment can successfully communicate with Supabase, run the test script:

```bash
python test_db.py
```

## Legacy Notes
- Old MySQL references have been removed as the system is now fully synchronized with PostgreSQL/Supabase.
