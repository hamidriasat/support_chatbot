# Support Chatbot Frontend

A modern, dark-themed React chatbot UI built with Vite, Tailwind CSS, and real-time backend integration. Features automatic backend connection detection and responsive design.

## Features

- 🎨 **Dark Theme UI** — Modern dark interface with high contrast
- 🤖 **AI Chat** — Send and receive messages from FastAPI backend
- 🔌 **Connection Status** — Real-time indicator showing backend health
- ⚡ **Built with Vite** — Ultra-fast development and build times
- 📱 **Responsive Design** — Works on desktop and mobile

## Project Structure

```
src/
├── components/
│   ├── Chatpanel.jsx       # Main chat container
│   ├── Messagelist.jsx     # Message display area
│   ├── Message.jsx         # Individual message component
│   └── Chatinput.jsx       # Message input field
├── hooks/
│   └── Usechat.jsx         # Chat logic & state management
├── services/
│   └── Api.js              # Backend API communication
├── styles/
│   └── Globals.css         # Design tokens & theme
└── main.jsx                # Entry point
```

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm
- FastAPI backend running on `localhost:8000`

### 1. Install Dependencies

```bash
npm install
```

### 2. Create `.env` File

Create the new `.env` file in the project root:

```env
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173/`

## Status Indicator

The green/red dot in the header shows backend connection status:
- 🟢 **Green** — Backend connected and healthy
- 🔴 **Red** — Backend unreachable or error

The app checks connection every 5 seconds automatically.
