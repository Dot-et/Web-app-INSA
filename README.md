# 🔐 Secure Authentication System

Welcome to my complete authentication system! I built this from the ground up to handle everything from user registration to session management with robust security features.

## 📋 Project Overview

This is a **full-featured authentication system** that allows users to securely create accounts, sign in, and manage their sessions. It's built with Flask and implements industry-standard security practices to protect user data and prevent common attacks.

### ✨ What This System Can Do

- **Create secure accounts** with strong password requirements
- **Sign in** with email/password or Google OAuth
- **Stay logged in** with secure session management
- **Protect** against brute-force attacks and suspicious logins
- **View and manage** all active sessions across devices
- **Logout** from single devices or all devices at once

---

## 🎯 Key Security Features

### 1. Strong Password Protection
- Passwords must be at least 12 characters long
- Must include uppercase, lowercase, numbers, and special characters
- Passwords are hashed using **bcrypt** (industry standard)

### 2. Brute-Force Defense
- Locks accounts after **5 failed login attempts**
- Accounts are locked for **30 minutes** after lockout
- Failed attempts are tracked and logged

### 3. Google OAuth Integration
- Users can sign in securely with their Google account
- No password needed for Google users
- Creates local accounts automatically on first login

### 4. Session Management
- Short-lived sessions (7 days)
- Each session is tracked with IP address and device info
- Users can view all active sessions and revoke any session
- "Remember Me" functionality for extended sessions

### 5. Suspicious Activity Detection
- Tracks login IP addresses and user agents
- Detects logins from new IP addresses
- Alerts users about suspicious login attempts

---

## 🛠️ Technology Stack

| Technology | Purpose |
|-----------|---------|
| **Flask** | Web framework |
| **SQLAlchemy** | Database ORM |
| **bcrypt** | Password hashing |
| **Authlib** | Google OAuth integration |
| **Flask-Login** | Session management |
| **SQLite** | Database (development) |

---

## 🚀 How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/Dot-et/Web-app-INSA.git
cd Web-app-INSA
