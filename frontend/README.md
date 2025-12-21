# Frontend - Check-In/Check-Out System

Next.js frontend for the attendance tracking system.

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` with your backend API URL.

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to http://localhost:3000

## Build for Production

```bash
npm run build
npm start
```

## Pages

- `/login` - User login
- `/register` - User registration
- `/dashboard` - Main dashboard with check-in/out
- `/history` - Attendance history
- `/admin` - Admin dashboard (admin only)

