# How to View Your Tables in Neon

There are several ways to view your tables in Neon PostgreSQL:

## Method 1: Neon Console (Web Dashboard) - Easiest Way

### Step 1: Access Neon Console
1. Go to [Neon Console](https://console.neon.tech)
2. Sign in to your Neon account
3. Select your project (the one you initialized with `npx neonctl@latest init`)

### Step 2: Navigate to Tables
1. In the left sidebar, click on **"Tables"** or **"Database"**
2. You'll see your database name (usually `neondb`)
3. Expand the database to see:
   - **Schemas** → **public** → **Tables**
   - You should see:
     - `users`
     - `checkinouts`
     - `alembic_version`

### Step 3: View Table Details
- Click on any table name to see:
  - Table structure (columns, data types)
  - Indexes
  - Constraints
  - Foreign keys
  - Row count

### Step 4: Query Data (SQL Editor)
1. Click on **"SQL Editor"** in the left sidebar
2. Write queries like:
   ```sql
   SELECT * FROM users;
   SELECT * FROM checkinouts;
   ```
3. Click **"Run"** to execute

## Method 2: Using Neon CLI

### List Tables via Command Line
```bash
# Connect to your database
npx neonctl@latest connection-string

# Then use psql or your preferred PostgreSQL client
psql "your-connection-string"

# Once connected, list tables:
\dt

# Or query:
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

## Method 3: Using SQL Query in Neon Console

### In Neon Console SQL Editor:

**List all tables:**
```sql
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**View table structure:**
```sql
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

**View table with row count:**
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

## Method 4: Using Python Script (Already Created)

Run the verification script we created:

```powershell
cd backend
.\venv\Scripts\python.exe verify_neon_tables.py
```

This will show you:
- All tables
- Table structures
- Indexes
- Foreign keys
- Row counts

## Method 5: Direct Database URL

1. In Neon Console, go to your project
2. Click on **"Connection Details"**
3. Copy the connection string
4. Use any PostgreSQL client (pgAdmin, DBeaver, TablePlus, etc.)
5. Connect and browse tables

## Quick Access Links

- **Neon Console**: https://console.neon.tech
- **Your Project**: Look for project name from `npx neonctl@latest init`
- **Database**: Usually named `neondb` or the name you chose

## What You Should See

When you navigate to Tables in Neon Console, you should see:

```
📁 public (schema)
  📊 users
    - id (integer, PK)
    - email (varchar, unique)
    - username (varchar, unique)
    - hashed_password (varchar)
    - full_name (varchar)
    - role (enum: admin, employee)
    - is_active (boolean)
    - created_at (timestamp)
    - updated_at (timestamp)
  
  📊 checkinouts
    - id (integer, PK)
    - user_id (integer, FK -> users.id)
    - check_in_time (timestamp)
    - check_out_time (timestamp)
    - latitude (float)
    - longitude (float)
    - device_info (varchar)
    - created_at (timestamp)
    - updated_at (timestamp)
  
  📊 alembic_version
    - version_num (varchar, PK)
```

## Tips

1. **SQL Editor**: Use the SQL Editor in Neon Console for quick queries
2. **Table Browser**: Click on table names to see structure and data
3. **Data Viewer**: Click "View Data" to see table contents
4. **Export**: You can export table data as CSV/JSON from the console

## Troubleshooting

If you don't see your tables:
1. Make sure you're in the correct project
2. Check you're looking at the `public` schema
3. Verify connection string is correct
4. Run: `alembic upgrade head` to ensure migrations are applied

