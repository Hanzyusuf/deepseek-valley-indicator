#!/usr/bin/env python3
"""
Scheduler using zoneinfo - Proper UTC to Local conversion
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
            
            # Parse periods
            self.parsed_periods = []
            default_period = None
            
            for period in self.periods:
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
            
            if not default_period and self.parsed_periods:
                self.parsed_periods[0]['is_default'] = True
                
        except Exception as e:
            print(f"Error loading schedule: {e}", file=sys.stderr)
            self.parsed_periods = self.get_default_periods()
            self.timezone_str = 'UTC'
    
    def get_default_periods(self):
        """Fallback default periods"""
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
        """Get system local timezone"""
        try:
            with open('/etc/timezone', 'r') as f:
                return f.read().strip()
        except:
            try:
                import time
                return time.tzname[0]
            except:
                return 'UTC'
    
    def get_current_status(self):
        """Get current status - handles periods crossing midnight"""
        # Get UTC time
        utc_tz = ZoneInfo('UTC')
        utc_now = datetime.now(utc_tz)
        utc_time = utc_now.time()
        utc_date = utc_now.date()
        
        # Get local time for display
        local_tz_str = self.get_local_timezone()
        try:
            local_tz = ZoneInfo(local_tz_str)
        except:
            local_tz = ZoneInfo('UTC')
            local_tz_str = 'UTC'
        
        local_now = utc_now.astimezone(local_tz)
        local_time = local_now.time()
        local_date = local_now.date()
        
        # Get day of week in UTC
        utc_day = utc_now.strftime('%A').lower()
        
        # Find matching period using UTC time
        matched_period = None
        
        for period in self.parsed_periods:
            if utc_day in period['days']:
                start = period['start']
                end = period['end']
                
                # Check if period crosses midnight
                if start > end:
                    # Period crosses midnight (e.g., 10:30 PM to 3:00 AM)
                    # Current time is in period if: time >= start OR time <= end
                    if utc_time >= start or utc_time <= end:
                        matched_period = period
                        break
                else:
                    # Normal period (no midnight crossing)
                    if start <= utc_time <= end:
                        matched_period = period
                        break
        
        # If no match, use default
        if matched_period is None:
            for period in self.parsed_periods:
                if period.get('is_default', False):
                    matched_period = period
                    break
            if matched_period is None and self.parsed_periods:
                matched_period = self.parsed_periods[0]
        
        # Calculate remaining time
        remaining = "N/A"
        
        # Check if current period is VALLEY
        is_valley = matched_period['type'] == 'peak'
        start = matched_period['start']
        end = matched_period['end']
        crosses_midnight = start > end
        
        if is_valley:
            if crosses_midnight:
                # Period crosses midnight
                if utc_time >= start:
                    # Time is in the first part (e.g., 10:30 PM to 11:59 PM)
                    # End is at the end time (e.g., 3:00 AM next day)
                    end_datetime = datetime.combine(utc_date, end) + timedelta(days=1)
                    end_utc = end_datetime.replace(tzinfo=utc_tz)
                    remaining_seconds = (end_utc - utc_now).total_seconds()
                    remaining = self.format_time_remaining(remaining_seconds)
                else:
                    # Time is in the second part (e.g., 12:00 AM to 3:00 AM)
                    end_datetime = datetime.combine(utc_date, end)
                    end_utc = end_datetime.replace(tzinfo=utc_tz)
                    remaining_seconds = (end_utc - utc_now).total_seconds()
                    remaining = self.format_time_remaining(remaining_seconds)
            else:
                # Normal period
                if utc_time <= end:
                    remaining_seconds = self.time_to_seconds(end) - self.time_to_seconds(utc_time)
                    remaining = self.format_time_remaining(remaining_seconds)
                else:
                    remaining = "0m"
        else:
            # In NORMAL - show time until next VALLEY
            next_valley = self.find_next_valley_utc(utc_time, utc_day, utc_date)
            if next_valley:
                period, days_ahead = next_valley
                period_start = period['start']
                period_end = period['end']
                
                # Determine when the next valley starts
                if period_start > period_end:
                    # Valley crosses midnight
                    # Start is today (or tomorrow)
                    start_date = utc_date + timedelta(days=days_ahead)
                    start_utc = datetime.combine(start_date, period_start)
                    start_utc_aware = start_utc.replace(tzinfo=utc_tz)
                    time_until = start_utc_aware - utc_now
                    remaining = self.format_time_remaining(time_until.total_seconds())
                else:
                    start_date = utc_date + timedelta(days=days_ahead)
                    start_utc = datetime.combine(start_date, period_start)
                    start_utc_aware = start_utc.replace(tzinfo=utc_tz)
                    time_until = start_utc_aware - utc_now
                    remaining = self.format_time_remaining(time_until.total_seconds())
        
        # Calculate next window
        next_window = "N/A"
        
        if is_valley:
            # Show when VALLEY ends
            if crosses_midnight:
                if utc_time >= start:
                    # Ends tomorrow at end time
                    end_datetime = datetime.combine(utc_date, end) + timedelta(days=1)
                else:
                    # Ends today at end time
                    end_datetime = datetime.combine(utc_date, end)
                end_local = end_datetime.replace(tzinfo=utc_tz).astimezone(local_tz)
                next_window = f"Ends at {end_local.strftime('%I:%M %p')}"
            else:
                end_datetime = datetime.combine(utc_date, end)
                end_local = end_datetime.replace(tzinfo=utc_tz).astimezone(local_tz)
                next_window = f"Ends at {end_local.strftime('%I:%M %p')}"
        else:
            # Find next VALLEY
            next_period = self.find_next_valley_utc(utc_time, utc_day, utc_date)
            if next_period:
                period, days_ahead = next_period
                period_date = utc_date + timedelta(days=days_ahead)
                period_utc = datetime.combine(period_date, period['start'])
                period_local = period_utc.replace(tzinfo=utc_tz).astimezone(local_tz)
                
                # Use LOCAL date to determine Today/Tomorrow
                if period_local.date() == local_date:
                    next_window = f"Today at {period_local.strftime('%I:%M %p')}"
                elif period_local.date() == local_date + timedelta(days=1):
                    next_window = f"Tomorrow at {period_local.strftime('%I:%M %p')}"
                else:
                    day_name = period_local.strftime('%A')
                    next_window = f"{day_name} at {period_local.strftime('%I:%M %p')}"
            else:
                next_window = "No VALLEY periods scheduled"
        
        # Build status
        indicator = "🔴" if is_valley else "🟢"
        state = matched_period['name']
        message = matched_period['message']
        
        return {
            "indicator": indicator,
            "state": state,
            "message": message,
            "remaining": remaining,
            "next_window": next_window,
            "utc_time": utc_now.strftime('%I:%M %p UTC'),
            "local_time": local_now.strftime('%I:%M %p'),
            "local_date": local_now.strftime('%B %d, %Y')
        }
    
    def find_next_valley_utc(self, current_utc_time, current_utc_day, current_utc_date):
        """Find next VALLEY period using UTC - only finds peak periods"""
        future_periods = []
        
        # Check today - only VALLEY periods
        for period in self.parsed_periods:
            if period['type'] == 'peak':  # Only look for VALLEY
                if current_utc_day in period['days'] and period['start'] > current_utc_time:
                    future_periods.append((period, 0))
        
        # Check next 7 days
        if not future_periods:
            for days_ahead in range(1, 8):
                next_date = current_utc_date + timedelta(days=days_ahead)
                next_day = next_date.strftime('%A').lower()
                for period in self.parsed_periods:
                    if period['type'] == 'peak':  # Only look for VALLEY
                        if next_day in period['days']:
                            future_periods.append((period, days_ahead))
                if future_periods:
                    break
        
        if future_periods:
            future_periods.sort(key=lambda x: (x[1], x[0]['start']))
            return future_periods[0]
        
        return None
    
    @staticmethod
    def time_to_seconds(t):
        return t.hour * 3600 + t.minute * 60 + t.second
    
    @staticmethod
    def format_time_remaining(seconds):
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
    json_path = None
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    
    manager = ScheduleManager(json_path)
    status = manager.get_current_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()