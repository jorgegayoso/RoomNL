#!/usr/bin/env python3
"""
Roommatch.nl Auto-Apply Script - Corrected Flow Version
This script logs in and applies to a room by ID, following the exact browser flow.

Usage:
    python apply_roommatch_v2.py <dwelling_id> <toewijzing_id>

Example:
    python apply_roommatch_v2.py 124885 117816
"""

import os
import requests
import json
import re
import sys
from getpass import getpass
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup


class RoommatchClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip",
        })
        self.logged_in = False
        self.base_url = "https://www.roommatch.nl"

    def login(self, username, password):
        """Log in to Roommatch via ROOM.nl SSO"""
        print("\n[1] Logging in...")

        try:
            sso_url = f"{self.base_url}/portal/sso/frontend/start"
            print(f"    → Starting SSO")

            response = self.session.get(sso_url, allow_redirects=True, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')

            if not form:
                print("    ✗ Could not find login form")
                return False

            # Extract authRequestID and CSRF token
            auth_request_id = response.url.split('authRequestID=')[-1].split('&')[
                0] if 'authRequestID=' in response.url else None
            csrf_input = form.find('input', attrs={'name': 'gorilla.csrf.Token'})
            csrf_token = csrf_input.get('value') if csrf_input else None

            if not auth_request_id or not csrf_token:
                print("    ✗ Missing required form data")
                return False

            # Submit username
            loginname_url = "https://sso.room.nl/ui/login/loginname"
            form_data = {
                'gorilla.csrf.Token': csrf_token,
                'authRequestID': auth_request_id,
                'loginName': username
            }

            response = self.session.post(loginname_url, data=form_data, allow_redirects=True, timeout=30)

            # Get new CSRF token for password step
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')
            if not form:
                print("    ✗ Could not find password form")
                return False

            csrf_input = form.find('input', attrs={'name': 'gorilla.csrf.Token'})
            csrf_token = csrf_input.get('value') if csrf_input else None

            if not csrf_token:
                print("    ✗ Missing CSRF token for password")
                return False

            # Submit password
            password_url = "https://sso.room.nl/ui/login/password"
            form_data = {
                'gorilla.csrf.Token': csrf_token,
                'authRequestID': auth_request_id,
                'loginName': username,
                'password': password
            }

            response = self.session.post(password_url, data=form_data, allow_redirects=True, timeout=30)

            if "roommatch.nl" in response.url:
                print("    ✓ Login successful!")
                self.logged_in = True
                return True
            else:
                print(f"    ✗ Login failed")
                return False

        except Exception as e:
            print(f"    ✗ Error during login: {e}")
            return False

    def get_dwelling_object(self, dwelling_id):
        """Fetch the dwelling object details - required to establish context"""
        print(f"\n[2] Fetching dwelling object {dwelling_id}...")

        try:
            url = f"{self.base_url}/portal/object/frontend/getobject/format/json"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/aanbod/studentenwoningen/",
                "Origin": self.base_url,
            }

            data = {"id": str(dwelling_id)}

            response = self.session.post(url, data=data, headers=headers, timeout=30)

            if response.status_code == 200:
                print(f"    ✓ Got dwelling object")
                try:
                    result = json.loads(response.text)
                    # Save for debugging
                    with open(f"dwelling_{dwelling_id}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    return result
                except:
                    print(f"    ⚠ Could not parse response as JSON")
                    return True
            else:
                print(f"    ✗ Failed (HTTP {response.status_code})")
                return None

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def get_reageer_configuration(self, dwelling_id):
        """Fetch the reageer (react) configuration - may be required before applying"""
        print(f"\n[3] Fetching reageer configuration...")

        try:
            url = f"{self.base_url}/portal/object/frontend/getreageerconfiguration/format/json"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Referer": f"{self.base_url}/aanbod/studentenwoningen/details/{dwelling_id}",
            }

            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                print(f"    ✓ Got reageer configuration")
                try:
                    result = json.loads(response.text)
                    # Save for debugging
                    with open(f"reageer_config_{dwelling_id}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)

                    # Check if we can react
                    if 'reageerConfiguration' in result:
                        config = result['reageerConfiguration']
                        if 'elements' in config and '__hash__' in config['elements']:
                            hash_token = config['elements']['__hash__'].get('initialData')
                            if hash_token:
                                print(f"    ✓ Found hash in reageer config: {hash_token}")
                                return hash_token
                    return result
                except Exception as e:
                    print(f"    ⚠ Could not parse response: {e}")
                    return True
            else:
                print(f"    ⚠ Failed (HTTP {response.status_code}) - continuing anyway")
                return None

        except Exception as e:
            print(f"    ⚠ Error: {e} - continuing anyway")
            return None

    def get_hash_token(self, dwelling_id):
        """Get the __hash__ token from the form submit configuration endpoint"""
        print(f"\n[4] Getting security hash token...")

        try:
            config_url = f"{self.base_url}/portal/core/frontend/getformsubmitonlyconfiguration/format/json"

            headers = {
                "Accept": "application/json, text/plain, */*",
                "Referer": f"{self.base_url}/aanbod/studentenwoningen/details/{dwelling_id}",
            }

            print(f"    → Fetching form config...")
            response = self.session.get(config_url, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"    ✗ Failed to fetch config (HTTP {response.status_code})")
                return None

            print(f"    ✓ Got response ({len(response.content)} bytes)")

            try:
                data = response.json()

                # Save for debugging
                with open("hash_config.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                hash_token = None

                # Path 1: Direct in form.elements.__hash__.initialData
                if 'form' in data and 'elements' in data['form']:
                    if '__hash__' in data['form']['elements']:
                        hash_data = data['form']['elements']['__hash__']
                        if 'initialData' in hash_data:
                            hash_token = hash_data['initialData']
                            print(f"    ✓ Found hash in form.elements.__hash__.initialData")

                # Path 2: Search through entire JSON for initialData with 32-char hex
                if not hash_token:
                    json_str = json.dumps(data)
                    matches = re.findall(r'"initialData"\s*:\s*"([a-f0-9]{32})"', json_str)
                    if matches:
                        hash_token = matches[0]
                        print(f"    ✓ Found hash via regex search")

                if hash_token and len(hash_token) == 32:
                    print(f"    ✓ Hash: {hash_token}")
                    return hash_token
                else:
                    print(f"    ✗ No valid hash found")
                    return None

            except json.JSONDecodeError as e:
                print(f"    ✗ Failed to parse JSON: {e}")
                return None

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None

    def apply_to_room(self, dwelling_id, toewijzing_id):
        """Apply to a room following the exact browser flow"""
        print(f"\n{'=' * 70}")
        print(f"Starting application process for room {dwelling_id}")
        print(f"{'=' * 70}")

        if not self.logged_in:
            print("    ✗ Not logged in!")
            return False

        try:
            # Step 1: Get dwelling object (establishes context)
            dwelling = self.get_dwelling_object(dwelling_id)
            if dwelling is None:
                print("    ⚠ Could not fetch dwelling object - continuing anyway")

            # Step 2: Get reageer configuration (may provide hash or validate eligibility)
            reageer_hash = self.get_reageer_configuration(dwelling_id)

            # Step 3: Get the form hash token
            hash_token = self.get_hash_token(dwelling_id)

            # Use reageer hash if available and form hash failed
            if not hash_token and isinstance(reageer_hash, str) and len(reageer_hash) == 32:
                hash_token = reageer_hash
                print(f"    → Using hash from reageer configuration")

            if not hash_token:
                print("    ✗ Cannot proceed without hash token!")
                return False

            # Step 4: Submit application
            print(f"\n[5] Submitting application...")
            print(f"    → Hash: {hash_token}")

            application_data = {
                "_id_": "Portal_Form_SubmitOnly",
                "__hash__": hash_token,
                "add": str(toewijzing_id),
                "dwellingId": str(dwelling_id)
            }

            apply_url = f"{self.base_url}/portal/object/frontend/react/format/json"

            # Match browser headers exactly as shown in Image 15
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/aanbod/studentenwoningen/details/{dwelling_id}",
            }

            encoded_data = urlencode(application_data)
            print(f"    → URL: {apply_url}")
            print(f"    → Data: {encoded_data[:80]}...")
            print(f"    → Content-Length: {len(encoded_data)}")

            # Save request for debugging
            with open(f"request_{dwelling_id}.json", "w", encoding="utf-8") as f:
                json.dump({
                    "url": apply_url,
                    "headers": headers,
                    "data": application_data,
                    "encoded_body": encoded_data,
                    "cookies": {k: v for k, v in self.session.cookies.items()}
                }, f, indent=2)

            response = self.session.post(
                apply_url,
                data=application_data,
                headers=headers,
                timeout=30
            )

            print(f"    → Response status: {response.status_code}")
            print(f"    → Response length: {len(response.content)} bytes")

            if response.status_code == 200:
                try:
                    result = response.json()

                    # Save response
                    with open(f"response_{dwelling_id}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)

                    success = result.get('success')
                    reaction_id = result.get('reactionId')
                    reaction_data = result.get('reactionData', {})
                    messages = result.get('messages', [])

                    if success:
                        print(f"\n    ✅ SUCCESS!")
                        if reaction_id:
                            print(f"    ✅ Reaction ID: {reaction_id}")
                        if reaction_data:
                            print(f"    ✅ Number of reactions: {reaction_data.get('numberOfReactions', 'N/A')}")

                        if messages:
                            for msg in messages:
                                msg_clean = re.sub('<[^<]+?>', '', str(msg))
                                print(f"    📧 {msg_clean[:200]}")

                        return True
                    else:
                        print(f"\n    ❌ Application Failed (success=false)")

                        # Try to find error in angular service data
                        angular_data = result.get('sAngularServiceData')
                        if angular_data:
                            try:
                                angular_json = json.loads(angular_data)
                                print(f"    ℹ Portal config received but no specific error")
                            except:
                                pass

                        if messages:
                            for msg in messages:
                                msg_clean = re.sub('<[^<]+?>', '', str(msg))
                                print(f"    Message: {msg_clean}")

                        # Check reaction data for clues
                        if reaction_data:
                            kan_reageren = reaction_data.get('kanReageren')
                            is_passend = reaction_data.get('isPassend')
                            if kan_reageren is False:
                                print(f"    ⚠ kanReageren is False - you may not be eligible to apply")
                            if is_passend is False:
                                print(f"    ⚠ isPassend is False - room may not match your profile")

                        return False

                except json.JSONDecodeError:
                    print(f"    ⚠ Response is not valid JSON")
                    print(f"    Raw: {response.text[:200]}")
                    return False
            else:
                print(f"    ❌ HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    print("=" * 70)
    print("Roommatch.nl Auto-Apply Script v2")
    print("=" * 70)

    # Get IDs
    if len(sys.argv) < 3:
        dwelling_id = input("\nDwelling ID: ").strip()
        toewijzing_id = input("Toewijzing ID: ").strip()
    else:
        dwelling_id = sys.argv[1].strip()
        toewijzing_id = sys.argv[2].strip()

    if not dwelling_id.isdigit() or not toewijzing_id.isdigit():
        print("✗ Invalid IDs - must be numeric")
        return

    print(f"\n🎯 Target: Room {dwelling_id} (Assignment {toewijzing_id})")

    # Login
    print("\n" + "-" * 70)
    username = os.environ.get("ROOMMATCH_USERNAME") or input("Username: ").strip()
    password = os.environ.get("ROOMMATCH_PASSWORD") or getpass("Password: ")

    if not username or not password:
        print("✗ Credentials required!")
        return

    # Ask for mode
    print("\nMode:")
    print("  1 = Full flow (detailed, with dwelling fetch)")
    print("  2 = Quick flow (minimal requests)")

    client = RoommatchClient()

    if not client.login(username, password):
        print("\n✗ LOGIN FAILED")
        return

    # Apply
    success = client.apply_to_room(dwelling_id, toewijzing_id)

    print("\n" + "=" * 70)
    if success:
        print("✅ APPLICATION SUCCESSFUL!")
        print("=" * 70)
        print("\n🎉 Your application has been submitted!")
        print("   Check 'Mijn reacties' on Roommatch to verify")
    else:
        print("❌ APPLICATION FAILED")
        print("=" * 70)
        print("\nPossible reasons:")
        print("  - You've already applied to this room")
        print("  - The application period has closed")
        print("  - You don't meet the requirements")
        print("  - You've reached the max number of active applications (5)")
        print("  - The hash token expired (try again quickly)")


if __name__ == "__main__":
    main()