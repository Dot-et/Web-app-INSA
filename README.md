# 🔐 My Flask Authentication System

## 🧑‍💻 A Journey into Web Security

*"I built this because I wanted to understand how websites actually keep our data safe."*

---

## 📖 The Story Behind This Project

### Why I Built This

Let me be honest — I used to login to websites without thinking about what happens behind the scenes. I'd type my password, click "Sign In," and magically I'd be in. But then I started wondering:

**How does a website actually know it's really me?**
**How do they stop hackers from guessing my password?**
**What happens when I check "Remember Me"?**

So I decided to build my own authentication system from scratch. No tutorials copying-pasting — I wanted to actually understand every line of code.

### What I Learned (The Hard Way)

This project taught me:
- **Security is hard**. Every "simple" feature has security implications.
- **Google OAuth is amazing** but also frustrating to set up the first time.
- **Deployment is a whole other skill** (Python 3.14 caused me major headaches!).
- **Error messages are actually your friends** (even when they don't feel like it).

---

## ✨ What My App Can Do

### For Users Like You

| Feature | What It Does | Why You'll Love It |
|---------|--------------|-------------------|
| **Register** | Create an account with username & email | Quick and easy |
| **Login** | Secure sign-in with your password | Your data stays safe |
| **Google Login** | Sign in with your Google account | No more passwords! |
| **Dashboard** | See your profile and active sessions | You're in control |
| **Sessions** | View and revoke login sessions | See where you're logged in |

### The Security Stuff (That I'm Proud Of)

| Security Feature | Why It Matters |
|------------------|----------------|
| **Strong Passwords** | I made sure passwords can't be easily guessed (12+ chars, mixed case, numbers, special chars) |
| **Brute Force Protection** | After 5 wrong attempts, the account locks for 30 minutes — no automated guessing here! |
| **Password Hashing** | Passwords are never stored in plain text. bcrypt makes them unreadable even if someone gets the database. |
| **Session Tracking** | You can see all your active sessions and revoke any you don't recognize. |

---

## 🎯 What Makes This Project Special

### For Me (Personal Growth)

| What I Learned | Why It Matters |
|----------------|----------------|
| **Flask Framework** | I can now build web apps from scratch |
| **Authentication** | I understand how login systems actually work |
| **Security Best Practices** | I know how to protect user data |
| **Deployment** | I can put apps on the internet |
| **Git & GitHub** | I can manage code professionally |
| **Problem Solving** | I debugged endless errors (Python 3.14 was a nightmare!) |

### For My Portfolio

This project shows:
- ✅ I can build a **complete web application**
- ✅ I understand **security fundamentals**
- ✅ I can **deploy to production**
- ✅ I write **documented, maintainable code**
- ✅ I can **integrate third-party services** (Google OAuth)

---

## 🛠️ How I Built It

### The Tech Stack (In Plain English)

| Technology | What It Does | Why I Chose It |
|------------|--------------|----------------|
| **Flask** | The web framework that handles requests | Simple, lightweight, perfect for learning |
| **SQLAlchemy** | Talks to the database | I didn't want to write raw SQL |
| **bcrypt** | Hashes passwords | Industry standard, very secure |
| **Authlib** | Handles Google OAuth | Made Google login possible |
| **Jinja2** | Renders HTML templates | Flask uses it by default |
| **SQLite** | The database | Simple, no setup needed |


