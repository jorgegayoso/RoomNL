#!/usr/bin/env python3
"""
Roommatch.nl Auto-Apply Monitor
Continuously monitors for new room listings and automatically applies when criteria are met.

Usage:
    python main.py           # Normal mode - fetches initial listings from API
    python main.py --test    # Test mode - loads initial listings from roommatch_listings.json

Configuration:
    Edit the CONFIG section below to set your preferences.

Requirements:
    pip install selenium webdriver-manager requests
"""

import time
import json
import argparse
from datetime import datetime
from typing import Optional
from listings import fetch_listings
from bot import apply_to_room
from notifier import send_application_email

# ============================================
# CONFIGURATION - CUSTOMIZE YOUR PREFERENCES
# ============================================

CONFIG = {
    # Monitoring settings
    "check_interval_seconds": 5,  # How often to check for new listings (in seconds)

    # Filter settings (set to None to disable a filter)
    "max_price": 750,  # Maximum total rent in EUR (e.g., 800.0) - set to None for no limit
    "min_price": None,  # Minimum total rent in EUR - set to None for no limit

    # Keyword filters (case-insensitive)
    "required_keywords": ["cornelis", "frogerstraat", "lallementstraat"],  # Room must contain at least ONE of these words (in address, city, or type)
    # Example: ["Amsterdam", "studio"]

    "excluded_keywords": [],  # Room must NOT contain ANY of these words
    # Example: ["shared", "Diemen"]

    # Location filters
    "allowed_cities": [],  # Only apply to rooms in these cities (empty = all cities)
    # Example: ["Amsterdam", "Amstelveen"]

    # Room type filters
    "allowed_types": [],  # Only apply to these room types (empty = all types)
    # Example: ["Studio", "Appartement"]

    # Auto-apply settings
    "auto_apply": True,  # Set to False to only notify without applying
    "max_applications_per_run": 3,  # Maximum number of applications per check cycle

    # Email notifications
    "send_email_notifications": True,  # Send email after each application attempt

    # Logging
    "verbose": True,  # Print detailed logs
}


# ============================================
# END OF CONFIGURATION
# ============================================


class RoommatchMonitor:
    """Monitors Roommatch for new listings and applies automatically."""

    def __init__(self, config: dict):
        self.config = config
        self.known_room_ids: set[str] = set()
        self.application_count = 0
        self.start_time = datetime.now()

    def get_url_key(self, room: dict) -> Optional[str]:
        """Extract url_key from room data (handles both normalized and raw formats)."""
        # First check if it's already at top level
        url_key = room.get("url_key") or room.get("urlKey")
        if url_key:
            return url_key

        # Check in _raw data
        raw = room.get("_raw", {})
        url_key = raw.get("urlKey") or raw.get("url_key")
        if url_key:
            return url_key

        return None

    def log(self, message: str, level: str = "INFO"):
        """Print a timestamped log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌",
            "NEW": "🆕",
            "APPLY": "🚀",
            "SKIP": "⏭️ ",
        }.get(level, "  ")
        print(f"[{timestamp}] {prefix} {message}")

    def room_matches_criteria(self, room: dict) -> tuple[bool, str]:
        """
        Check if a room matches the configured criteria.

        Returns:
            Tuple of (matches: bool, reason: str)
        """
        # Build searchable text from room data
        searchable_text = " ".join(filter(None, [
            str(room.get("address", "")),
            str(room.get("city", "")),
            str(room.get("type", "")),
            str(room.get("street", "")),
        ])).lower()

        # Price filters
        total_rent = room.get("total_rent")

        if self.config["max_price"] is not None and total_rent is not None:
            if total_rent > self.config["max_price"]:
                return False, f"Price €{total_rent:.2f} exceeds max €{self.config['max_price']:.2f}"

        if self.config["min_price"] is not None and total_rent is not None:
            if total_rent < self.config["min_price"]:
                return False, f"Price €{total_rent:.2f} below min €{self.config['min_price']:.2f}"

        # Required keywords (must contain at least ONE)
        found_keyword = False
        for keyword in self.config["required_keywords"]:
            if keyword.lower() in searchable_text:
                found_keyword = True
                break
        if not found_keyword:
            return False, "Missing at least one required keyword"

        # Excluded keywords (must not contain ANY)
        for keyword in self.config["excluded_keywords"]:
            if keyword.lower() in searchable_text:
                return False, f"Contains excluded keyword: '{keyword}'"

        # City filter
        if self.config["allowed_cities"]:
            city = str(room.get("city", "")).lower()
            allowed = [c.lower() for c in self.config["allowed_cities"]]
            if city not in allowed:
                return False, f"City '{room.get('city')}' not in allowed list"

        # Room type filter
        if self.config["allowed_types"]:
            room_type = str(room.get("type", "")).lower()
            allowed = [t.lower() for t in self.config["allowed_types"]]
            if not any(t in room_type for t in allowed):
                return False, f"Type '{room.get('type')}' not in allowed list"

        return True, "Matches all criteria"

    def format_room_info(self, room: dict) -> str:
        """Format room information for display."""
        parts = [f"{room.get('address', 'Unknown')}, {room.get('city', '')}"]

        if room.get("total_rent"):
            parts.append(f"€{room['total_rent']:.2f}/mo")
        if room.get("area"):
            parts.append(f"{room['area']}m²")
        if room.get("type"):
            parts.append(room["type"])

        return " | ".join(parts)

    def process_new_room(self, room: dict) -> bool:
        """
        Process a newly discovered room.

        Returns:
            True if application was successful or not attempted, False on failure.
        """
        room_id = room.get("id")
        url_key = self.get_url_key(room)
        room_info = self.format_room_info(room)

        self.log(f"New listing found: {room_info}", "NEW")

        # Check if room matches criteria
        matches, reason = self.room_matches_criteria(room)

        if not matches:
            self.log(f"Skipping: {reason}", "SKIP")
            return True

        self.log(f"Room matches criteria! {reason}", "SUCCESS")

        # Check if we should auto-apply
        if not self.config["auto_apply"]:
            self.log("Auto-apply disabled. Skipping application.", "INFO")
            if room.get("url"):
                self.log(f"View room: {room['url']}", "INFO")
            return True

        # Check if we have a url_key to apply with
        if not url_key:
            self.log(f"No url_key found for room {room_id}, cannot apply", "ERROR")
            # Send failure email
            if self.config.get("send_email_notifications"):
                send_application_email(room, success=False, error_message="No url_key found for room")
            return False

        # Apply to the room
        self.log(f"Applying to room {url_key}...", "APPLY")

        try:
            success = apply_to_room(url_key)

            if success:
                self.application_count += 1
                self.log(f"Successfully applied to room {url_key}!", "SUCCESS")

                # Send success email
                if self.config.get("send_email_notifications"):
                    send_application_email(room, success=True)

                return True
            else:
                self.log(f"Failed to apply to room {url_key}", "ERROR")

                # Send failure email
                if self.config.get("send_email_notifications"):
                    send_application_email(room, success=False, error_message="Application submission failed")

                return False

        except Exception as e:
            self.log(f"Error applying to room: {e}", "ERROR")

            # Send failure email with exception details
            if self.config.get("send_email_notifications"):
                send_application_email(room, success=False, error_message=str(e))

            return False

    def check_for_new_listings(self) -> int:
        """
        Fetch listings and process any new ones.

        Returns:
            Number of new listings found.
        """
        if self.config["verbose"]:
            self.log("Fetching listings from API...", "INFO")

        try:
            rooms = fetch_listings()
        except Exception as e:
            self.log(f"Error fetching listings: {e}", "ERROR")
            return 0

        if not rooms:
            if self.config["verbose"]:
                self.log("No rooms returned from API (possible server/network error). Keeping previous room list.",
                         "WARNING")
            # Don't update known_room_ids - keep the previous list for comparison
            return 0

        # Get current room IDs
        current_ids = {str(room.get("id")) for room in rooms if room.get("id")}

        # Failsafe: if we got 0 rooms but now have rooms again, compare against last known good list
        if len(current_ids) == 0:
            self.log("API returned empty room list. Keeping previous room list.", "WARNING")
            return 0

        # Find new rooms (not in our known set)
        new_ids = current_ids - self.known_room_ids

        if self.config["verbose"]:
            self.log(f"Found {len(rooms)} total rooms, {len(new_ids)} new", "INFO")

        # Process new rooms
        applications_this_cycle = 0
        max_apps = self.config["max_applications_per_run"]

        for room in rooms:
            room_id = str(room.get("id"))

            if room_id not in new_ids:
                continue

            # Add to known set immediately (even if we don't apply)
            self.known_room_ids.add(room_id)

            # Check application limit
            if applications_this_cycle >= max_apps:
                self.log(f"Reached max applications per cycle ({max_apps})", "INFO")
                break

            # Check if matches criteria before counting toward limit
            matches, _ = self.room_matches_criteria(room)
            if matches and self.config["auto_apply"]:
                self.process_new_room(room)
                applications_this_cycle += 1
            else:
                self.process_new_room(room)

        # Update known rooms with current valid list
        # Only update if we got a valid response (non-empty)
        self.known_room_ids = current_ids

        return len(new_ids)

    def run(self, test_mode: bool = False):
        """Main monitoring loop."""
        print("\n" + "=" * 70)
        print("🏠 ROOMMATCH AUTO-APPLY MONITOR")
        if test_mode:
            print("   ⚠️  TEST MODE - Loading initial listings from roommatch_listings.json")
        print("=" * 70)

        # Print configuration
        print("\n📋 Configuration:")
        print(f"   Check interval: {self.config['check_interval_seconds']} seconds")
        print(f"   Max price: {'€' + str(self.config['max_price']) if self.config['max_price'] else 'No limit'}")
        print(f"   Min price: {'€' + str(self.config['min_price']) if self.config['min_price'] else 'No limit'}")
        print(f"   Required keywords: {self.config['required_keywords'] or 'None'}")
        print(f"   Excluded keywords: {self.config['excluded_keywords'] or 'None'}")
        print(f"   Allowed cities: {self.config['allowed_cities'] or 'All'}")
        print(f"   Allowed types: {self.config['allowed_types'] or 'All'}")
        print(f"   Auto-apply: {'Yes' if self.config['auto_apply'] else 'No (notify only)'}")
        print(f"   Max apps per cycle: {self.config['max_applications_per_run']}")
        print(f"   Email notifications: {'Yes' if self.config.get('send_email_notifications') else 'No'}")

        print("\n" + "-" * 70)
        print("🚀 Starting monitor... Press Ctrl+C to stop")
        print("-" * 70 + "\n")

        # Initial fetch to populate known rooms
        if test_mode:
            self.log("Loading initial listings from roommatch_listings.json...", "INFO")
            try:
                with open("roommatch_listings.json", "r", encoding="utf-8") as f:
                    initial_rooms = json.load(f)
                if initial_rooms:
                    self.known_room_ids = {str(room.get("id")) for room in initial_rooms if room.get("id")}
                    self.log(f"Loaded {len(self.known_room_ids)} existing listings from JSON", "INFO")
                else:
                    self.log("No listings found in JSON file", "WARNING")
            except FileNotFoundError:
                self.log("roommatch_listings.json not found! Run listings.py first to generate it.", "ERROR")
                self.log("Or run without --test flag to fetch from API.", "ERROR")
                return
            except json.JSONDecodeError as e:
                self.log(f"Error parsing JSON file: {e}", "ERROR")
                return
        else:
            self.log("Performing initial fetch to establish baseline...", "INFO")
            try:
                initial_rooms = fetch_listings()
                if initial_rooms:
                    self.known_room_ids = {str(room.get("id")) for room in initial_rooms if room.get("id")}
                    self.log(f"Initialized with {len(self.known_room_ids)} existing listings", "INFO")
                else:
                    self.log("No initial listings found", "WARNING")
            except Exception as e:
                self.log(f"Error during initial fetch: {e}", "ERROR")

        # Main loop
        while True:
            try:
                time.sleep(self.config["check_interval_seconds"])

                new_count = self.check_for_new_listings()

                if new_count == 0 and self.config["verbose"]:
                    self.log("No new listings", "INFO")

            except KeyboardInterrupt:
                print("\n")
                self.log("Received interrupt signal. Shutting down...", "INFO")
                break
            except Exception as e:
                self.log(f"Unexpected error: {e}", "ERROR")
                time.sleep(10)  # Brief pause before retrying

        # Print summary
        print("\n" + "=" * 70)
        print("📊 SESSION SUMMARY")
        print("=" * 70)
        runtime = datetime.now() - self.start_time
        print(f"   Runtime: {runtime}")
        print(f"   Total applications: {self.application_count}")
        print(f"   Rooms tracked: {len(self.known_room_ids)}")
        print("=" * 70 + "\n")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Roommatch for new listings and auto-apply"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: load initial listings from roommatch_listings.json instead of fetching from API"
    )
    args = parser.parse_args()

    monitor = RoommatchMonitor(CONFIG)
    monitor.run(test_mode=args.test)


if __name__ == "__main__":
    main()
