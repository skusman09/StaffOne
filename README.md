# Check-In/Check-Out System

A full-stack attendance tracking application built with FastAPI backend and Next.js frontend.

## 🏗 Tech Stack

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL (SQLite for local development)
- JWT Authentication (access + refresh tokens)
- Alembic for migrations
- Pydantic schemas
- Role-based access control (admin, employee)

### Frontend
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Axios
- TanStack React Query
- JWT token handling

## 📁 Project Structure

```
checkinout/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── database.py           # Database configuration
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── routes/               # API route handlers
│   │   ├── services/             # Business logic
│   │   ├── core/                 # Core configuration
│   │   └── utils/                # Utility functions
│   ├── alembic/                  # Database migrations
│   ├── requirements.txt          # Python dependencies
│   └── .env.example              # Environment variables example
├── frontend/
│   ├── app/                      # Next.js app directory
│   ├── components/               # React components
│   ├── lib/                      # Utility libraries
│   ├── package.json              # Node dependencies
│   └── .env.example              # Environment variables example
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- PostgreSQL (optional, SQLite is used by default)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the following:
   ```env
   DATABASE_URL=sqlite:///./checkinout.db
   SECRET_KEY=your-secret-key-change-in-production-use-a-long-random-string
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

6. **Run database migrations (optional, tables are auto-created):**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

   The API will be available at `http://localhost:8001`
   - API Documentation: `http://localhost:8001/docs`
   - Alternative docs: `http://localhost:8001/redoc`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env.local` file:**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` and ensure:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## 📝 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get tokens
- `GET /auth/me` - Get current user info

### Attendance
- `POST /attendance/check-in` - Check in for the day
- `POST /attendance/check-out` - Check out for the day
- `GET /attendance/my-today` - Get today's check-in/out status
- `GET /attendance/history` - Get attendance history

### Admin (Admin only)
- `GET /admin/users` - Get all users
- `GET /admin/attendance` - Get all attendance records

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. After login, you'll receive:
- `access_token`: Short-lived token (30 minutes by default)
- `refresh_token`: Long-lived token (7 days by default)

Include the access token in requests:
```
Authorization: Bearer <access_token>
```

## 🎯 Features

### User Features
- User registration and login
- Check-in/Check-out with geolocation support
- View today's attendance status
- View attendance history
- Protected routes

### Admin Features
- View all users
- View all attendance records
- Filter attendance by user

### Business Rules
- One check-in per day
- Check-out only if checked-in
- Prevents duplicate check-in/check-out actions
- Proper error handling and validation

## 🧪 Testing the Application

1. **Start both backend and frontend servers**

2. **Register a new user:**
   - Navigate to `http://localhost:3000/register`
   - Fill in the registration form
   - You'll be redirected to login

3. **Login:**
   - Navigate to `http://localhost:3000/login`
   - Enter your credentials
   - You'll be redirected to the dashboard

4. **Check-in:**
   - On the dashboard, click "Check In"
   - You'll see today's check-in time

5. **Check-out:**
   - After checking in, click "Check Out"
   - You'll see both check-in and check-out times

6. **View History:**
   - Click "View Attendance History" on the dashboard
   - See all your past attendance records

7. **Admin Access:**
   - To create an admin user, you'll need to manually update the database or use the API directly
   - Admin users can access `/admin` to view all users and attendance

## 🗄 Database Models

### User
- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `full_name`: Optional full name
- `role`: Enum (admin, employee)
- `is_active`: Boolean flag
- `created_at`: Timestamp
- `updated_at`: Timestamp

### CheckInOut
- `id`: Primary key
- `user_id`: Foreign key to User
- `check_in_time`: Check-in timestamp
- `check_out_time`: Check-out timestamp (nullable)
- `latitude`: Optional latitude
- `longitude`: Optional longitude
- `device_info`: Optional device information
- `created_at`: Timestamp
- `updated_at`: Timestamp

## 🔧 Configuration

### Backend Environment Variables
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration (default: 7)
- `CORS_ORIGINS`: Comma-separated list of allowed origins

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8001)

## 📦 Production Deployment

### Backend
1. Set `DATABASE_URL` to your PostgreSQL connection string
2. Generate a strong `SECRET_KEY`
3. Update `CORS_ORIGINS` with your frontend domain
4. Use a production ASGI server like Gunicorn with Uvicorn workers:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Frontend
1. Update `NEXT_PUBLIC_API_URL` to your backend URL
2. Build the application:
   ```bash
   npm run build
   ```
3. Start the production server:
   ```bash
   npm start
   ```

## 🐛 Troubleshooting

### Backend Issues
- **Database errors**: Ensure the database file/database exists and is accessible
- **Import errors**: Make sure you're in the backend directory and virtual environment is activated
- **Port already in use**: Change the port in the uvicorn command

### Frontend Issues
- **API connection errors**: Check that `NEXT_PUBLIC_API_URL` matches your backend URL
- **CORS errors**: Ensure backend `CORS_ORIGINS` includes your frontend URL
- **Build errors**: Delete `node_modules` and `.next` folder, then reinstall dependencies

## 📄 License

This project is open source and available for use.

## 👤 Author

Built with ❤️ for attendance tracking

