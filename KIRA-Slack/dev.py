#!/usr/bin/env python3
"""Development server with hot reload."""

import subprocess
import sys
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class HotReloadHandler(FileSystemEventHandler):
    """Handler for file system events that restarts the server."""
    
    def __init__(self):
        self.process = None
        self.start_server()
    
    def start_server(self):
        """Start the server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        print("🚀 Starting server...")
        self.process = subprocess.Popen(
            ["uv", "run", "python", "-m", "app.main"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Only restart for Python files
        if not event.src_path.endswith('.py'):
            return
            
        print(f"📝 File changed: {event.src_path}")
        print("🔄 Restarting server...")
        self.start_server()


def main():
    """Main function to start the hot reload development server."""
    print("🔥 Hot reload development server starting...")
    print("📁 Watching for changes in app/ directory")
    print("⏹️  Press Ctrl+C to stop")
    
    # Create event handler and observer
    handler = HotReloadHandler()
    observer = Observer()
    
    # Watch the app directory
    app_path = Path("app")
    if app_path.exists():
        observer.schedule(handler, str(app_path), recursive=True)
    else:
        print("❌ app/ directory not found")
        return 1
    
    # Start observer
    observer.start()
    
    try:
        observer.join()
    except KeyboardInterrupt:
        print("\n🛑 Stopping development server...")
        if handler.process:
            handler.process.terminate()
            handler.process.wait()
        observer.stop()
        observer.join()
        print("✅ Server stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())