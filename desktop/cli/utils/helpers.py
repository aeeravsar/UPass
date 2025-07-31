import getpass
import sys
from typing import Optional
import re
from datetime import datetime

def get_password(prompt: str = "Master password: ") -> str:
    """Securely get password from user"""
    try:
        password = getpass.getpass(prompt)
        if not password:
            print("Password cannot be empty")
            sys.exit(1)
        return password
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)

def get_input(prompt: str, required: bool = True) -> Optional[str]:
    """Get input from user with optional validation"""
    try:
        value = input(prompt)
        if required and not value.strip():
            print("Input cannot be empty")
            return None
        return value.strip()
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)

def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or len(username) > 32:
        return False
    return re.match(r'^[a-zA-Z0-9]+$', username) is not None

def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    while True:
        try:
            response = input(f"{message} (y/N): ").strip().lower()
            if not response or response == 'n':
                return False
            elif response == 'y':
                return True
            else:
                print("Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print("\nAborted")
            return False

def print_error(message: str) -> None:
    """Print error message to stderr"""
    print(f"Error: {message}", file=sys.stderr)

def print_success(message: str) -> None:
    """Print success message"""
    print(f"✓ {message}")

def print_info(message: str) -> None:
    """Print info message"""
    print(f"• {message}")

def format_table(headers: list, rows: list) -> str:
    """Format data as a simple table"""
    if not rows:
        return "No entries found"
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Create separator
    separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    
    # Format header
    header = "|" + "|".join(f" {h:<{w}} " for h, w in zip(headers, widths)) + "|"
    
    # Format rows
    formatted_rows = []
    for row in rows:
        formatted_row = "|" + "|".join(f" {str(cell):<{w}} " for cell, w in zip(row, widths)) + "|"
        formatted_rows.append(formatted_row)
    
    return "\n".join([separator, header, separator] + formatted_rows + [separator])

def format_datetime(iso_datetime: str) -> str:
    """Format ISO datetime string to human-readable format"""
    try:
        # Parse ISO format like "2025-07-25T20:00:00Z"
        if iso_datetime.endswith('Z'):
            dt = datetime.fromisoformat(iso_datetime[:-1])
        else:
            dt = datetime.fromisoformat(iso_datetime)
        
        # Format as "Jul 25, 2025 8:00 PM"
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, AttributeError):
        # Fallback for invalid dates
        return iso_datetime

def format_date(iso_datetime: str) -> str:
    """Format ISO datetime string to just date"""
    try:
        if iso_datetime.endswith('Z'):
            dt = datetime.fromisoformat(iso_datetime[:-1])
        else:
            dt = datetime.fromisoformat(iso_datetime)
        
        # Format as "Jul 25, 2025"
        return dt.strftime("%b %d, %Y")
    except (ValueError, AttributeError):
        # Fallback for invalid dates
        return iso_datetime[:10] if len(iso_datetime) >= 10 else iso_datetime