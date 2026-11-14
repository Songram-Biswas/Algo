# AlgoHub 🦉💻

A gamified Data Structures & Algorithms (DSA) learning platform and progress tracker. AlgoHub not only helps you master the **Blind 75** and **NeetCode 150** curriculums with interactive visual tracers but also actively guilt-trips you into maintaining your daily coding streak using an unhinged, Duolingo-style AI reminder system.

## ✨ Features

* **Curated Learning Tracks:** Seamlessly track your progress across the NeetCode 150 and Blind 75 problem sets.
* **Interactive Visual Tracers:** Custom step-by-step algorithmic visualizations and pointer animations that break down complex data structures in real-time.
* **Comprehensive Solutions:** Built-in optimal Python 3 solutions, in-depth approach explanations, and Big-O Time/Space complexity analyses for every problem.
* **Passive-Aggressive AI Reminders (Duolingo-Style):** 
  * Tracks user local timezones dynamically.
  * Triggers daily at 9:00 PM (local time) if a user hasn't solved a problem and their streak is at risk.
  * Uses **Google Gemini 2.5 Flash** to generate chaotic, all-caps, highly contextual guilt-trip emails demanding they save their streak.
* **Secure Authentication & Data:** Powered by Supabase Auth and PostgreSQL, ensuring secure user data and progress tracking.

## 🛠 Tech Stack

* **Frontend:** HTML5, CSS3 (Tailwind/Custom), Vanilla JavaScript
* **Backend:** Vercel Serverless Functions (Node.js)
* **Database & Auth:** Supabase (PostgreSQL, Row Level Security)
* **AI Integration:** Google Gemini 2.5 Flash API
* **Email Dispatch:** Nodemailer via secure Gmail SMTP (App Passwords)
* **Automation:** Vercel Cron Jobs

## 🚀 Local Setup & Installation

### 1. Prerequisites
You will need the following accounts and keys to run AlgoHub locally:
* [Supabase](https://supabase.com/) Account (Project URL, Anon Key, Service Role Key)
* [Google AI Studio](https://aistudio.google.com/) Account (Gemini API Key)
* A dedicated Gmail Account with **2-Step Verification** enabled and an **App Password** generated.

### 2. Clone the Repository
```bash
git clone [https://github.com/yourusername/algohub.git](https://github.com/yourusername/algohub.git)
cd algohub
npm install

3. Environment Variables
Create a .env file in the root directory and configure your secrets (do not commit this file):

Code snippet
# AI Tutor & Generator: Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Auth & Database
SUPABASE_URL=[https://your-project-id.supabase.co](https://your-project-id.supabase.co)
SUPABASE_ANON_KEY=your_anon_key_here

# Supabase Admin (Required for background Cron jobs to fetch user data safely)
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Gmail SMTP for Streak Reminders
GMAIL_USER=your_dedicated_email@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password

4. Run the Development Server
Use Vercel CLI to run the project locally exactly how it will run in production:

Bash
vercel dev
The application will be available at http://localhost:3000.


🧪 Testing the Cron Jobs Locally
AlgoHub includes a custom testing script to simulate the Vercel Cron job environment locally without needing to wait for the scheduled time or hitting production limits.

To test the dynamic timezone logic and email dispatch:

Bash
npm run test:cron
Note: The script outputs the evaluation logs and the generated AI persona message directly in the terminal before attempting to send the email via Nodemailer.

☁️ Deployment
This project is optimized for deployment on Vercel.

Push your code to GitHub.

Import the repository into your Vercel Dashboard.

Add all the environment variables from your .env file into the Vercel Project Settings > Environment Variables.

Deploy.

Important Note for Vercel Hobby Tier:
The vercel.json file is configured to run the streak reminder cron job once daily (e.g., 0 15 * * *) to comply with Vercel's free-tier limitations.

🤝 Contributing
Pull requests are welcome! If you'd like to add new algorithms, enhance the visual tracers, or make the AI owl even more passive-aggressive, feel free to fork the repository and submit a PR.
