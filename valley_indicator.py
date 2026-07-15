#!/usr/bin/env python3
"""
XFCE Systray Status Indicator - Stable Version
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class ValleyIndicator:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.scheduler_script = self.script_dir / "scheduler.py"
        self.schedules_json = self.script_dir / "schedules.json"
        self.update_interval = 30
        self.dialog = None
        
        self.current_status = {
            'indicator': '🟢',
            'state': 'NORMAL',
            'message': 'Safe to proceed',
            'remaining': 'N/A',
            'next_window': 'N/A',
            'local_time': '--:--'
        }
        
        self.create_status_icon()
        self.fetch_status()
        GLib.timeout_add_seconds(self.update_interval, self.update_timer)
        
    def create_status_icon(self):
        """Create status icon using system icons (stable)"""
        try:
            self.status_icon = Gtk.StatusIcon()
            self.status_icon.set_visible(True)
            
            # Use system icons that always work
            self.status_icon.set_from_icon_name('gtk-apply')
            self.status_icon.set_tooltip_text('Loading...')
            
            self.status_icon.connect('activate', self.on_click)
            self.status_icon.connect('popup-menu', self.on_right_click)
            print("Status icon created")
        except Exception as e:
            print(f"CRITICAL: Could not create status icon: {e}")
            sys.exit(1)
    
    def update_icon(self):
        """Update icon using system icons"""
        try:
            indicator = self.current_status.get('indicator', '🟢')
            
            # Use system icons that always work
            if indicator == '🔴':
                self.status_icon.set_from_icon_name('gtk-dialog-warning')
            else:
                self.status_icon.set_from_icon_name('gtk-apply')
            
            # Tooltip
            status = self.current_status
            tooltip = f"{status['indicator']} {status['state']}"
            if status['remaining'] != 'N/A':
                tooltip += f" - {status['remaining']} left"
            self.status_icon.set_tooltip_text(tooltip)
            
        except Exception as e:
            print(f"Icon update error: {e}")
    
    def fetch_status(self):
        """Get status from scheduler"""
        try:
            cmd = [sys.executable, str(self.scheduler_script), str(self.schedules_json)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout:
                try:
                    status = json.loads(result.stdout)
                    self.current_status.update(status)
                except:
                    pass
        except Exception as e:
            print(f"Fetch error: {e}")
        
        GLib.idle_add(self.update_icon)
    
    def update_timer(self):
        threading.Thread(target=self.fetch_status, daemon=True).start()
        return True
    
    def on_click(self, widget):
        if self.dialog and self.dialog.get_visible():
            self.dialog.present()
            return
        self.show_status_dialog()
    
    def on_right_click(self, widget, button, activate_time):
        menu = Gtk.Menu.new()
        
        # Status header
        status_text = f"{self.current_status['indicator']} {self.current_status['state']}"
        item = Gtk.MenuItem.new_with_label(status_text)
        item.set_sensitive(False)
        menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem.new())
        
        # Details
        item = Gtk.MenuItem.new_with_label("📊 Details")
        item.connect('activate', self.on_click)
        menu.append(item)
        
        # Refresh
        item = Gtk.MenuItem.new_with_label("🔄 Refresh")
        item.connect('activate', lambda x: threading.Thread(target=self.fetch_status, daemon=True).start())
        menu.append(item)
        
        # Edit Schedule
        item = Gtk.MenuItem.new_with_label("✏️ Edit Schedule")
        item.connect('activate', self.on_edit_json)
        menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem.new())
        
        # Quit
        item = Gtk.MenuItem.new_with_label("🚪 Quit")
        item.connect('activate', self.on_quit)
        menu.append(item)
        
        menu.show_all()
        menu.popup(None, None, None, None, button, activate_time)
    
    def on_edit_json(self, widget):
        try:
            subprocess.Popen(['xdg-open', str(self.schedules_json)])
        except:
            subprocess.Popen(['gedit', str(self.schedules_json)])
    
    def on_quit(self, widget):
        Gtk.main_quit()
    
    def show_status_dialog(self):
        """Show clean status dialog with edit option"""
        if self.dialog:
            self.dialog.destroy()
        
        self.dialog = Gtk.Dialog(
            title="Deepseek Valley Status",
            parent=None,
            flags=0
        )
        
        # Add buttons
        self.dialog.add_buttons(
            "✏️ Edit Schedule", Gtk.ResponseType.HELP,
            "Close", Gtk.ResponseType.CLOSE
        )
        
        self.dialog.set_default_size(350, 300)
        self.dialog.set_resizable(False)
        self.dialog.set_border_width(20)
        self.dialog.connect('destroy', lambda x: setattr(self, 'dialog', None))
        
        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
        
        # Header
        header_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 15)
        header_box.set_halign(Gtk.Align.CENTER)
        
        indicator = Gtk.Label.new(self.current_status.get('indicator', '🟢'))
        indicator.set_markup(f"<span size='xx-large'>{self.current_status.get('indicator', '🟢')}</span>")
        header_box.pack_start(indicator, False, False, 0)
        
        state = self.current_status.get('state', 'NORMAL')
        state_label = Gtk.Label.new(state)
        state_label.set_markup(f"<b><span size='x-large'>{state}</span></b>")
        header_box.pack_start(state_label, False, False, 0)
        
        main_box.pack_start(header_box, False, False, 0)
        
        # Divider
        divider = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(divider, False, False, 5)
        
        # Info grid
        grid = Gtk.Grid.new()
        grid.set_row_spacing(8)
        grid.set_column_spacing(20)
        grid.set_halign(Gtk.Align.CENTER)
        
        # Get status info
        current_state = self.current_status.get('state', 'NORMAL')
        remaining = self.current_status.get('remaining', 'N/A')
        next_window = self.current_status.get('next_window', 'N/A')
        
        # Clear label for remaining
        if current_state == 'VALLEY':
            remaining_label = f"⏱️ VALLEY Remaining"
            remaining_icon = "🔴"
        else:
            remaining_label = f"⏱️ Until Next VALLEY"
            remaining_icon = "🟢"
        
        # Next window display
        next_display = next_window
        
        info_items = [
            (remaining_label, f"{remaining_icon} {remaining}" if remaining != 'N/A' else remaining),
            ("📅 Next VALLEY", next_display),
            ("📝 Status", self.current_status.get('message', ''))
        ]
        
        for i, (label_text, value) in enumerate(info_items):
            label = Gtk.Label.new(label_text)
            label.set_halign(Gtk.Align.END)
            label.set_markup(f"<b>{label_text}</b>")
            grid.attach(label, 0, i, 1, 1)
            
            value_label = Gtk.Label.new(str(value))
            value_label.set_halign(Gtk.Align.START)
            value_label.set_selectable(True)
            grid.attach(value_label, 1, i, 1, 1)
        
        main_box.pack_start(grid, False, False, 0)
        
        # Footer
        footer = Gtk.Label.new(f"Updated: {datetime.now().strftime('%I:%M:%S %p')}")
        footer.set_markup(f"<small>Updated: {datetime.now().strftime('%I:%M:%S %p')}</small>")
        footer.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(footer, False, False, 5)
        
        self.dialog.vbox.pack_start(main_box, True, True, 0)
        self.dialog.show_all()
        
        response = self.dialog.run()
        if response == Gtk.ResponseType.HELP:
            self.on_edit_json(None)
        
        self.dialog.destroy()
        self.dialog = None

def main():
    import fcntl
    lock_file = Path.home() / ".valley_indicator.lock"
    try:
        f = open(lock_file, 'w')
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(os.getpid()))
        f.flush()
    except:
        print("Already running", file=sys.stderr)
        sys.exit(1)
    
    try:
        app = ValleyIndicator()
        Gtk.main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            fcntl.lockf(f, fcntl.LOCK_UN)
            f.close()
            lock_file.unlink()
        except:
            pass

if __name__ == "__main__":
    main()