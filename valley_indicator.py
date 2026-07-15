#!/usr/bin/env python3
"""
XFCE Systray Status Indicator for Valley/Normal periods
With daemon mode, better UI, and JSON menu option
"""

import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GLib, Gio

class ValleyIndicator:
    def __init__(self):
        # Configuration
        self.script_dir = Path(__file__).parent
        self.scheduler_script = self.script_dir / "scheduler.py"
        self.schedules_json = self.script_dir / "schedules.json"
        self.update_interval = 30
        
        self.current_status = {
            'indicator': '🟢',
            'state': 'NORMAL',
            'message': 'Loading...',
            'remaining': 'N/A',
            'next_window': 'N/A',
            'timezone': 'UTC',
            'local_time': '--:--'
        }
        
        # Create the status icon
        self.create_status_icon()
        
        # Initial status fetch
        self.fetch_status()
        
        # Start periodic updates
        GLib.timeout_add_seconds(self.update_interval, self.update_timer)
        
    def create_status_icon(self):
        """Create the status icon with better visuals"""
        try:
            self.status_icon = Gtk.StatusIcon()
            self.status_icon.set_visible(True)
            
            # Use emoji directly as icon for better visibility
            self.status_icon.set_from_icon_name('dialog-information')
            self.status_icon.set_tooltip_text('Loading...')
            
            # Connect signals
            self.status_icon.connect('activate', self.on_click)
            self.status_icon.connect('popup-menu', self.on_right_click)
            
            print("Status icon created successfully")
        except Exception as e:
            print(f"Error creating status icon: {e}")
            sys.exit(1)
    
    def create_colorful_icon(self, color_type):
        """Create a custom colored icon using a label approach"""
        # Since GTK StatusIcon doesn't easily support custom drawing,
        # we'll use emoji + tooltip for better visibility
        # Or use system icons with better mapping
        try:
            if color_type == '🔴':
                # Use a more visible red icon
                self.status_icon.set_from_icon_name('weather-storm')
            else:
                # Use a more visible green icon
                self.status_icon.set_from_icon_name('weather-clear')
        except:
            # Fallback to standard icons
            if color_type == '🔴':
                self.status_icon.set_from_icon_name('dialog-error')
            else:
                self.status_icon.set_from_icon_name('dialog-ok')
    
    def update_icon(self):
        """Update the icon based on current status"""
        try:
            indicator = self.current_status.get('indicator', '🟢')
            
            # Better icon mapping
            if indicator == '🔴':
                # Try different icon names for better visibility
                icon_names = ['weather-storm', 'dialog-error', 'dialog-warning', 'process-stop']
                for icon_name in icon_names:
                    try:
                        self.status_icon.set_from_icon_name(icon_name)
                        break
                    except:
                        continue
            else:
                icon_names = ['weather-clear', 'dialog-ok', 'dialog-information', 'process-completed']
                for icon_name in icon_names:
                    try:
                        self.status_icon.set_from_icon_name(icon_name)
                        break
                    except:
                        continue
            
            # Update tooltip with better formatting
            tooltip = f"""
{indicator} {self.current_status['state']}
━━━━━━━━━━━━━━━━━━━━
📝 {self.current_status['message']}
⏱️ Remaining: {self.current_status['remaining']}
📅 Next: {self.current_status['next_window']}
🕐 Local: {self.current_status['local_time']}
            """.strip()
            self.status_icon.set_tooltip_text(tooltip)
            
        except Exception as e:
            print(f"Error updating icon: {e}")
    
    def fetch_status(self):
        """Run scheduler and get status"""
        try:
            cmd = [
                sys.executable,
                str(self.scheduler_script),
                str(self.schedules_json)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    status = json.loads(result.stdout)
                    self.current_status.update(status)
                except json.JSONDecodeError as e:
                    print(f"JSON parse error: {e}")
            else:
                print(f"Scheduler error: {result.stderr}")
                self.current_status['message'] = "Error reading schedule"
                
        except Exception as e:
            print(f"Error fetching status: {e}")
            self.current_status['message'] = f"Error: {str(e)}"
        
        # Update UI
        GLib.idle_add(self.update_icon)
    
    def update_timer(self):
        """Timer callback"""
        threading.Thread(target=self.fetch_status, daemon=True).start()
        return True
    
    def on_click(self, widget):
        """Handle left click - show beautiful status dialog"""
        self.show_status_dialog()
    
    def on_right_click(self, widget, button, activate_time):
        """Handle right click - show enhanced menu"""
        menu = Gtk.Menu.new()
        
        # Header with current status
        status_text = f"{self.current_status['indicator']} {self.current_status['state']}"
        status_item = Gtk.MenuItem.new_with_label(status_text)
        status_item.set_sensitive(False)
        
        # Style the status item (bold)
        status_item.get_child().set_markup(f"<b>{status_text}</b>")
        menu.append(status_item)
        
        # Separator
        sep = Gtk.SeparatorMenuItem.new()
        menu.append(sep)
        
        # Show Details
        details_item = Gtk.MenuItem.new_with_label("📊 Show Details")
        details_item.connect('activate', self.on_show_details)
        menu.append(details_item)
        
        # Edit JSON
        json_item = Gtk.MenuItem.new_with_label("✏️ Edit Schedule")
        json_item.connect('activate', self.on_edit_json)
        menu.append(json_item)
        
        # Open JSON location
        open_item = Gtk.MenuItem.new_with_label("📂 Open Schedule Folder")
        open_item.connect('activate', self.on_open_folder)
        menu.append(open_item)
        
        # Separator
        sep2 = Gtk.SeparatorMenuItem.new()
        menu.append(sep2)
        
        # Refresh
        refresh_item = Gtk.MenuItem.new_with_label("🔄 Refresh")
        refresh_item.connect('activate', self.on_refresh)
        menu.append(refresh_item)
        
        # Quit
        quit_item = Gtk.MenuItem.new_with_label("🚪 Quit")
        quit_item.connect('activate', self.on_quit)
        menu.append(quit_item)
        
        menu.show_all()
        menu.popup(None, None, None, None, button, activate_time)
    
    def on_show_details(self, widget):
        """Show detailed status"""
        self.show_status_dialog()
    
    def on_edit_json(self, widget):
        """Open JSON file in default editor"""
        try:
            # Try to open with default editor
            subprocess.Popen(['xdg-open', str(self.schedules_json)])
            # Or use specific editors:
            # subprocess.Popen(['gedit', str(self.schedules_json)])
            # subprocess.Popen(['nano', str(self.schedules_json)])
        except Exception as e:
            print(f"Error opening editor: {e}")
            # Fallback: show in terminal
            print(f"Please edit: {self.schedules_json}")
    
    def on_open_folder(self, widget):
        """Open folder containing the JSON file"""
        try:
            folder = self.schedules_json.parent
            subprocess.Popen(['xdg-open', str(folder)])
        except Exception as e:
            print(f"Error opening folder: {e}")
    
    def on_refresh(self, widget):
        """Refresh status"""
        threading.Thread(target=self.fetch_status, daemon=True).start()
    
    def on_quit(self, widget):
        """Quit application"""
        print("Quitting...")
        Gtk.main_quit()
    
    def show_status_dialog(self):
        """Show a beautiful status dialog"""
        dialog = Gtk.Dialog(
            title="Valley Status",
            parent=None,
            flags=0
        )
        dialog.set_default_size(350, 300)
        dialog.set_border_width(10)
        
        # Add buttons
        dialog.add_buttons(
            "Close", Gtk.ResponseType.CLOSE,
            "Refresh", Gtk.ResponseType.ACCEPT,
            "Edit Schedule", Gtk.ResponseType.HELP
        )
        
        # Main content box
        content_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        
        # Status indicator (big emoji)
        indicator_label = Gtk.Label.new(self.current_status['indicator'])
        indicator_label.set_markup(f"<span size='x-large'>{self.current_status['indicator']}</span>")
        content_box.pack_start(indicator_label, False, False, 0)
        
        # Status grid with nice formatting
        grid = Gtk.Grid.new()
        grid.set_row_spacing(8)
        grid.set_column_spacing(15)
        
        fields = [
            ("📌 State", "state"),
            ("📝 Message", "message"),
            ("⏱️ Remaining", "remaining"),
            ("📅 Next Window", "next_window"),
            ("🌐 Timezone", "timezone"),
            ("🕐 Local Time", "local_time")
        ]
        
        for i, (label_text, key) in enumerate(fields):
            # Label
            label = Gtk.Label.new(label_text)
            label.set_halign(Gtk.Align.END)
            label.set_markup(f"<b>{label_text}</b>")
            grid.attach(label, 0, i, 1, 1)
            
            # Value
            value = self.current_status.get(key, 'N/A')
            value_label = Gtk.Label.new(str(value))
            value_label.set_halign(Gtk.Align.START)
            value_label.set_selectable(True)
            grid.attach(value_label, 1, i, 1, 1)
        
        content_box.pack_start(grid, False, False, 0)
        
        # Last updated
        last_updated = Gtk.Label.new(f"Last updated: {datetime.now().strftime('%I:%M:%S %p')}")
        last_updated.set_markup("<small>Last updated: {}</small>".format(
            datetime.now().strftime('%I:%M:%S %p')
        ))
        content_box.pack_start(last_updated, False, False, 5)
        
        dialog.vbox.pack_start(content_box, True, True, 0)
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            threading.Thread(target=self.fetch_status, daemon=True).start()
        elif response == Gtk.ResponseType.HELP:
            self.on_edit_json(None)
        dialog.destroy()

def daemonize():
    """Run in background (daemon mode)"""
    try:
        # Fork and detach from terminal
        if os.fork() > 0:
            sys.exit(0)
        os.setsid()
        if os.fork() > 0:
            sys.exit(0)
        
        # Close file descriptors
        sys.stdout.close()
        sys.stderr.close()
        sys.stdin.close()
        
        # Redirect to /dev/null
        fd = os.open(os.devnull, os.O_RDWR)
        os.dup2(fd, 0)
        os.dup2(fd, 1)
        os.dup2(fd, 2)
        os.close(fd)
    except Exception as e:
        print(f"Daemonize error: {e}")

def main():
    # Check for --daemon flag
    if '--daemon' in sys.argv:
        daemonize()
    
    # Single instance check
    import fcntl
    lock_file = Path.home() / ".valley_indicator.lock"
    try:
        f = open(lock_file, 'w')
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(os.getpid()))
        f.flush()
    except:
        print("Another instance is already running", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create the indicator
        indicator = ValleyIndicator()
        
        # Run GTK main loop
        Gtk.main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            fcntl.lockf(f, fcntl.LOCK_UN)
            f.close()
            if lock_file.exists():
                lock_file.unlock()
                lock_file.unlink()
        except:
            pass

if __name__ == "__main__":
    main()