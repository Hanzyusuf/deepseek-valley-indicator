#!/usr/bin/env python3
"""
Scheduler using zoneinfo (Python 3.9+) - No external dependencies.
Reads time periods from JSON with timezone support
Converts to local timezone automatically
"""

import json
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

class ScheduleManager:
    def __init__(self, json_path=None):
        if json_path is None:
            json_path = Path(__file__).parent / "schedules.json"
        self.json_path = json_path
        self.load_schedule()
        
    def load_schedule(self):
        """Load and parse the JSON schedule"""
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            
            self.timezone_str = data.get('timezone', 'UTC')
            self.periods = data.get('periods', [])
            
            # Validate and parse periods
            self.parsed_periods = []
            default_period = None
            
            for period in self.periods:
                # Parse days
                days = period.get('days', [])
                if 'all' in days:
                    days = ['monday', 'tuesday', 'wednesday', 'thursday', 
                           'friday', 'saturday', 'sunday']
                
                # Parse times in 12-hour format
                start_time = datetime.strptime(period['start'], '%I:%M %p').time()
                end_time = datetime.strptime(period['end'], '%I:%M %p').time()
                
                parsed = {
                    'name': period['name'],
                    'type': period.get('type', ''),
                    'days': [day.lower() for day in days],
                    'start': start_time,
                    'end': end_time,
                    'message': period.get('message', ''),
                    'is_default': period.get('default', False)
                }
                
                self.parsed_periods.append(parsed)
                
                if parsed['is_default']:
                    default_period = parsed
            
            # Set default period if not specified
            if not default_period and self.parsed_periods:
                self.parsed_periods[0]['is_default'] = True
                
        except Exception as e:
            print(f"Error loading schedule: {e}", file=sys.stderr)
            # Fallback to default periods
            self.parsed_periods = self.get_default_periods()
            self.timezone_str = 'UTC'
    
    def get_default_periods(self):
        """Fallback default periods if JSON fails"""
        return [
            {
                'name': 'VALLEY',
                'type': 'peak',
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'start': datetime.strptime('09:00 AM', '%I:%M %p').time(),
                'end': datetime.strptime('10:30 AM', '%I:%M %p').time(),
                'message': '🔴 Peak hour - Avoid tokens',
                'is_default': False
            },
            {
                'name': 'NORMAL',
                'type': 'safe',
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                        'saturday', 'sunday'],
                'start': datetime.strptime('12:00 AM', '%I:%M %p').time(),
                'end': datetime.strptime('11:59 PM', '%I:%M %p').time(),
                'message': '🟢 Normal - Safe to proceed',
                'is_default': True
            }
        ]
    
    def get_local_timezone(self):
        """Get the system's local timezone"""
        try:
            # Read from /etc/timezone (Linux)
            with open('/etc/timezone', 'r') as f:
                return f.read().strip()
        except:
            try:
                # Fallback: use timezone from environment
                import time
                return time.tzname[0]
            except:
                return 'UTC'
    
    def get_current_status(self):
        """
        Get current status based on the schedule
        Returns dict with: indicator, state, message, remaining, next_window
        """
        # Get current time in the schedule's timezone
        try:
            schedule_tz = ZoneInfo(self.timezone_str)
            schedule_time = datetime.now(schedule_tz)
        except Exception as e:
            print(f"Timezone error: {e}, falling back to UTC", file=sys.stderr)
            schedule_time = datetime.now(ZoneInfo('UTC'))
        
        # Convert to local timezone for display
        local_tz_str = self.get_local_timezone()
        try:
            local_tz = ZoneInfo(local_tz_str)
            local_time = schedule_time.astimezone(local_tz)
        except:
            # Fallback to UTC if local timezone fails
            local_time = schedule_time.astimezone(ZoneInfo('UTC'))
        
        current_time = local_time.time()
        current_day = local_time.strftime('%A').lower()
        current_date = local_time.date()
        
        # Find matching period
        matched_period = None
        
        # Check each period
        for period in self.parsed_periods:
            if current_day in period['days']:
                if period['start'] <= current_time <= period['end']:
                    matched_period = period
                    break
        
        # If no match found, use default
        if matched_period is None:
            for period in self.parsed_periods:
                if period.get('is_default', False):
                    matched_period = period
                    break
            # If still no default, use first period
            if matched_period is None and self.parsed_periods:
                matched_period = self.parsed_periods[0]
        
        # Calculate remaining time
        remaining = "N/A"
        if matched_period:
            end_time = matched_period['end']
            if current_time <= end_time:
                remaining_seconds = self.time_to_seconds(end_time) - self.time_to_seconds(current_time)
                remaining = self.format_time_remaining(remaining_seconds)
            else:
                remaining = "0m"
        
        # Calculate next window
        next_window = "N/A"
        if matched_period and current_time <= matched_period['end']:
            # Current period is active, show when it ends
            next_window = f"Ends at {matched_period['end'].strftime('%I:%M %p')}"
        else:
            # Find next period
            next_period = self.find_next_period(current_time, current_day, current_date)
            if next_period:
                next_window = self.format_next_window(next_period, current_date, current_time)
            else:
                next_window = "No more periods today"
        
        # Build status
        indicator = "🔴" if matched_period['type'] == 'peak' else "🟢"
        state = matched_period['name']
        message = matched_period['message']
        
        return {
            "indicator": indicator,
            "state": state,
            "message": message,
            "remaining": remaining,
            "next_window": next_window,
            "timezone": self.timezone_str,
            "local_time": local_time.strftime('%I:%M %p'),
            "local_timezone": local_tz_str
        }
    
    def find_next_period(self, current_time, current_day, current_date):
        """Find the next upcoming period"""
        # Check today's remaining periods
        future_periods = []
        for period in self.parsed_periods:
            if current_day in period['days'] and period['start'] > current_time:
                future_periods.append((period, 0))  # 0 = today
        
        # Check tomorrow and beyond
        if not future_periods:
            days_ahead = 1
            while days_ahead <= 7:  # Look up to 7 days ahead
                next_date = current_date + timedelta(days=days_ahead)
                next_day = next_date.strftime('%A').lower()
                for period in self.parsed_periods:
                    if next_day in period['days']:
                        future_periods.append((period, days_ahead))
                if future_periods:
                    break
                days_ahead += 1
        
        if future_periods:
            # Sort by days ahead, then by start time
            future_periods.sort(key=lambda x: (x[1], x[0]['start']))
            return future_periods[0]
        
        return None
    
    def format_next_window(self, period_data, current_date, current_time):
        """Format the next window description"""
        period, days_ahead = period_data
        
        if days_ahead == 0:
            # Today
            return f"Today at {period['start'].strftime('%I:%M %p')}"
        elif days_ahead == 1:
            # Tomorrow
            return f"Tomorrow at {period['start'].strftime('%I:%M %p')}"
        else:
            # Specific day
            day_name = (current_date + timedelta(days=days_ahead)).strftime('%A')
            return f"{day_name} at {period['start'].strftime('%I:%M %p')}"
    
    @staticmethod
    def time_to_seconds(t):
        """Convert time object to seconds since midnight"""
        return t.hour * 3600 + t.minute * 60 + t.second
    
    @staticmethod
    def format_time_remaining(seconds):
        """Format seconds into human-readable string"""
        if seconds <= 0:
            return "0m"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return f"{minutes}m"

def main():
    """Main function to output status"""
    # Allow custom JSON path as argument
    json_path = None
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    manager = ScheduleManager(json_path)
    status = manager.get_current_status()
    
    # Output as JSON
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()