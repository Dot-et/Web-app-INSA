# Real-Time Collaborative Document Editor

A production-ready collaborative document editor built with Flask, Socket.IO, and Quill.js. Supports real-time collaboration, version history, comments, and document sharing.

## 🚀 Features

### Core Features
- **Authentication**: Email/password with Google OAuth integration
- **Document Management**: Create, rename, delete, duplicate documents
- **Rich Text Editing**: Bold, italic, underline, headings, lists, links, images
- **Real-Time Collaboration**: Live document editing with multiple users
- **Presence Awareness**: See who's currently viewing the document
- **Auto-Save**: Automatically saves changes without a save button
- **Version History**: View and restore previous versions
- **Comments**: Add, reply, resolve, and delete comments
- **Sharing & Permissions**: Share with viewer, commenter, or editor permissions

### Security Features
- Password hashing with bcrypt
- Account lockout after 5 failed attempts (30 minutes)
- Session management with device tracking
- CSRF protection
- SQL injection prevention (SQLAlchemy)

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask 3.0.3
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Real-Time**: Flask-SocketIO with Socket.IO
- **Authentication**: Flask-Login, bcrypt, Authlib (Google OAuth)
- **Server**: Gunicorn (production) / Eventlet (WebSocket)

### Frontend
- **Templating**: Jinja2
- **Rich Text Editor**: Quill.js
- **Real-Time Client**: Socket.IO client
- **Styling**: Custom CSS with responsive design
- **Icons**: Font Awesome 6

## 📋 Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)
- Git

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd collaborative-document-editor