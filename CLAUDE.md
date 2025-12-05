# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based multi-screen display management system for Raspberry Pi devices. It allows remote control of multiple screens through a centralized web interface using WebSocket communication (Flask-SocketIO).

**Core functionality:**
- Central management interface (`/`) for controlling screens
- Display client interface (`/display`) for Raspberry Pi devices
- Real-time bidirectional communication via Socket.IO
- Content library management (web pages, videos, images, YouTube)
- Playlist creation and scheduling
- Time-based content scheduling per screen

## Running the Application

### Development Server

```bash
# Install dependencies (Flask and Flask-SocketIO are required)
pip install flask flask-socketio

# Run the server
python gestion_raspberry.py
```

The server runs on `http://0.0.0.0:5000` by default.

### Accessing the Interfaces

1. **Management Interface**: `http://SERVER_IP:5000/`
2. **Display Client** (on Raspberry Pi):
   ```bash
   chromium-browser --kiosk --noerrdialogs \
     "http://SERVER_IP:5000/display?id=ecran1&name=Cuisine&location=RDC"
   ```

URL parameters for display client:
- `id` (required): Unique screen identifier
- `name` (optional): Display name for the screen
- `location` (optional): Physical location label

## Architecture

### Backend Structure

**Main application:** `gestion_raspberry.py`
- Flask application with Socket.IO integration
- Event-driven architecture for real-time communication
- Persistent storage using JSON files in `data/` directory

**Data persistence:**
- `data/screens.json` - Screen registry (id, name, location)
- `data/content.json` - Content library entries
- `data/playlists.json` - Playlist definitions with items and durations
- `data/schedules.json` - Time-based scheduling per screen

**In-memory state:**
- `screens` dict - Active screen connections (includes runtime status, sid, last_seen)
- `content_library` list - All available content items
- `playlists` dict - Playlist definitions with items
- `schedules` dict - Screen-specific time schedules

### Frontend Structure

**Templates:**
- `templates/manager.html` - Management interface with modals for content/playlist/schedule management
- `templates/display.html` - Display client that registers with server and shows content

**Static assets:**
- `static/css/style.css` - Management interface styles
- `static/css/player.css` - Display client styles

### Socket.IO Events

**Client → Server:**
- `register_screen` - Screen connects and identifies itself
- `get_state` - Request current system state
- `add_content` / `update_content` / `delete_content` - Content library management
- `display_content` - Show specific content on a screen
- `clear_screen` - Clear content from a screen
- `bulk_display` - Display content on multiple screens
- `create_playlist` / `update_playlist` / `delete_playlist` - Playlist management
- `start_playlist` - Manually trigger a playlist on a screen
- `update_schedule` - Set time-based schedule for a screen

**Server → Client:**
- `state_update` - Broadcast full state to all clients
- `show_content` - Command display client to show content
- `clear_content` - Command display client to clear display
- `start_playlist` - Command display client to start playlist
- `update_schedule` - Send schedule to specific display client
- `send_full_playlist_list` - Send all playlists to display client

### Content Types

The system supports four content types:
- `url` - Web pages (embedded in iframe)
- `video` - Video files (HTML5 video element)
- `image` - Image files (img element)
- `youtube` - YouTube videos (embedded player with autoplay)

Each content item has:
- `id` - Unique identifier (timestamp)
- `name` - Display name
- `type` - Content type (url/video/image/youtube)
- `url` - Content URL
- `duration` - Display duration in seconds (0 = infinite)

### Playlist System

Playlists are collections of content items with individual durations:
- Each playlist has a unique ID, name, and creation timestamp
- Playlist items include the content object and a duration override
- Display clients cycle through playlist items automatically
- Schedules link time ranges to playlist IDs for automated playback

### Scheduling Logic

Display clients check schedules every 30 seconds:
1. Current time is compared against schedule entries (HH:MM format)
2. If current time falls within a schedule entry's start/end range, the associated playlist launches
3. Only one active playlist per screen at a time
4. Schedule entries are checked in order; first match wins

## Development Notes

### Adding New Content Types

To add a new content type, modify:
1. `templates/manager.html` - Add option to content type dropdown
2. `templates/display.html` - Add rendering logic in `showContent()` function
3. Content structure remains the same (id, name, type, url, duration)

### WebSocket State Management

- All clients receive `state_update` broadcasts when data changes
- Display clients store their screen ID from URL parameters
- Server tracks screen connections via Socket.IO session IDs (`sid`)
- Disconnections automatically update screen status to 'offline'

### Data Persistence Pattern

Each data type follows this pattern:
1. Modify in-memory structure
2. Call corresponding `save_*()` function
3. Broadcast `state_update` to all clients
4. Update specific clients if needed (e.g., send schedule to display client)

### Security Considerations

- Secret key is hardcoded (`votre-cle-secrete-ici`) - should be changed for production
- CORS is fully open (`cors_allowed_origins="*"`) - restrict for production
- No authentication or authorization implemented
- Display clients trust all server commands without validation
