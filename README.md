# Digital Signage System

A Flask-based multi-screen display management system for Raspberry Pi devices. Control multiple screens remotely through a centralized web interface using real-time WebSocket communication.

## Features

- **Centralized Management**: Control all screens from a single web interface
- **Real-time Communication**: Bidirectional updates via Socket.IO
- **Content Library**: Manage web pages, videos, images, and YouTube content
- **Playlist System**: Create and schedule content playlists
- **Time-based Scheduling**: Automate content display based on time ranges
- **Multi-screen Support**: Manage multiple Raspberry Pi displays simultaneously

## Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or use the installation script:
```bash
bash install.sh
```

2. Run the server:
```bash
python gestion_raspberry.py
```

The server will start on `http://0.0.0.0:5000`

### Accessing the Interfaces

**Management Interface**: Navigate to `http://SERVER_IP:5000/` in your browser

**Display Client** (on Raspberry Pi):
```bash
chromium-browser --kiosk --noerrdialogs \
  "http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC"
```

URL parameters:
- `id` (required): Unique screen identifier
- `name` (optional): Display name
- `location` (optional): Physical location label

## Content Types

The system supports:
- **URL**: Web pages (embedded in iframe)
- **Video**: Video files (HTML5 video player)
- **Image**: Image files
- **YouTube**: YouTube videos with autoplay

## Architecture

### Backend
- Flask application with Socket.IO for real-time communication
- JSON-based persistent storage in `data/` directory
- Event-driven architecture for screen management

### Frontend
- Management interface: `templates/manager.html`
- Display client: `templates/display.html`
- Responsive design with real-time updates

### Data Persistence
- `data/screens.json` - Screen registry
- `data/content.json` - Content library
- `data/playlists.json` - Playlist definitions
- `data/schedules.json` - Time-based schedules

## Documentation

- [CLAUDE.md](CLAUDE.md) - Detailed development guide
- [YOUTUBE_API_SETUP.md](YOUTUBE_API_SETUP.md) - YouTube API configuration
- [PROCEDURE_COMPLETE.md](PROCEDURE_COMPLETE.md) - Setup procedures

## License

This project is open source and available for educational and commercial use.
