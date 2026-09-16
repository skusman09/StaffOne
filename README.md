# StaffOne — Modern HRMS & Workforce Management SaaS

> **StaffOne Showcase:** A full-stack HRMS and Workforce Management SaaS. Features include payroll, onboarding, and attendance tracking built with Next.js, FastAPI, and Astro.

StaffOne is a comprehensive, multi-tenant SaaS platform designed to streamline core HR operations, payroll processing, and employee engagement. 

*Note: The source code for this project is hosted in private repositories to protect proprietary code. This repository serves as an architectural overview and feature showcase.*

---

## 🔗 Live Deployments
*   **Web Application (Next.js):** [staffone.pages.dev](https://staffone.pages.dev/)
*   **Marketing Portal (Astro):** [staffoneportal.pages.dev](https://staffoneportal.pages.dev/)

---

## 🏗️ Tech Stack & Architecture

*   **Frontend Web App:** Built using Next.js and Tailwind CSS, deployed seamlessly on Cloudflare Pages.
*   **Backend REST API:** Engineered with Python and FastAPI, utilizing SQLAlchemy and Alembic for database management. The backend is hosted on Render.
*   **Background Processing:** Leverages Redis and RQ for asynchronous job scheduling, email processing, and background tasks.
*   **Marketing Portal:** High-performance, SEO-optimized static site built with Astro and hosted on Cloudflare Pages.

---

## 🚀 Key Features & Modules

*   **Time & Attendance:** Automated working day calculations, comprehensive leave policies, and comp-off management.
*   **Payroll & Compensation:** Dynamic salary calculation engines with automated PDF and Excel report generation.
*   **Employee Lifecycle:** Dedicated modules for onboarding workflows, organization structuring (departments/locations), and audit logging.
*   **Engagement & Communications:** Built-in pulse surveys to gauge employee sentiment and transactional email delivery powered by Brevo.

---

## 📸 Application Previews

<!-- Create an 'assets' folder in your repository and upload your images there -->

| Employee Dashboard | Payroll Generation | Leave Approvals |
| :---: | :---: | :---: |
| <img src="assets/dashboard.png" width="250" alt="Dashboard Preview" /> | <img src="assets/payroll.png" width="250" alt="Payroll Preview" /> | <img src="assets/leaves.png" width="250" alt="Leave Management Preview" /> |
