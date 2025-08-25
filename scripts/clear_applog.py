"""
Script to clear the application's log file (app.log).

This is useful for development and debugging to get a clean log.
"""
import os

log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log'))

try:
    with open(log_file_path, 'w') as f:
        f.write('')
    print(f"Log file '{log_file_path}' cleared successfully.")
except IOError as e:
    print(f"Error clearing log file '{log_file_path}': {e}")
