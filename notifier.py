#!/usr/bin/env python3
"""
Email Notification Module for Roommatch Auto-Apply
Sends email notifications when applications are submitted or fail.

Usage:
    from notifier import send_application_email

Configuration:
    Edit the EMAIL_CONFIG section below with your email settings.

    For Gmail:
    - Enable 2FA on your Google account
    - Generate an App Password: https://myaccount.google.com/apppasswords
    - Use the App Password as SMTP_PASSWORD

Requirements:
    No additional packages required (uses built-in smtplib)
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

# ============================================
# CONFIGURATION - SET VIA ENVIRONMENT VARIABLES
# ============================================

EMAIL_CONFIG = {
    # SMTP Server Settings
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,

    # Authentication (from environment variables)
    "smtp_username": os.environ.get("SMTP_USERNAME", ""),
    "smtp_password": os.environ.get("SMTP_PASSWORD", ""),

    # Email Addresses (from environment variables)
    "from_email": os.environ.get("SMTP_USERNAME", ""),
    "to_email": os.environ.get("NOTIFY_EMAIL", ""),

    # Optional Settings
    "subject_prefix": "[Roommatch]",
    "include_raw_data": False,
}


# ============================================
# END OF CONFIGURATION
# ============================================


def format_room_html(room: dict) -> str:
    """Format room information as HTML for email body."""

    # Extract basic info
    address = room.get("address", "Unknown address")
    city = room.get("city", "")
    total_rent = room.get("total_rent")
    area = room.get("area")
    rooms = room.get("rooms")
    room_type = room.get("type", "")
    available_from = room.get("available_from", "")
    deadline = room.get("deadline", "")
    url = room.get("url", "")
    url_key = room.get("url_key") or room.get("_raw", {}).get("urlKey", "")

    # Format price
    price_str = f"€{total_rent:,.2f}/month" if total_rent else "Not specified"

    # Format area
    area_str = f"{area} m²" if area else "Not specified"

    # Format dates
    if available_from:
        try:
            if "T" in str(available_from):
                available_from = available_from.split("T")[0]
        except:
            pass

    if deadline:
        try:
            if "T" in str(deadline):
                deadline = deadline.split("T")[0]
        except:
            pass

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
            📍 {address}, {city}
        </h2>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; width: 40%;">💰 Total Rent</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{price_str}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">📐 Area</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{area_str}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">🚪 Rooms</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{rooms if rooms else 'Not specified'}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">🏠 Type</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{room_type if room_type else 'Not specified'}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">📅 Available From</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{available_from if available_from else 'Not specified'}</td>
            </tr>
            <tr>
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">⏰ Deadline</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{deadline if deadline else 'Not specified'}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">🔑 URL Key</td>
                <td style="padding: 12px; border: 1px solid #dee2e6;">{url_key}</td>
            </tr>
        </table>

        {f'<p><a href="{url}" style="display: inline-block; background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">🔗 View Listing</a></p>' if url else ''}
    </div>
    """

    return html


def format_room_text(room: dict) -> str:
    """Format room information as plain text for email body."""

    address = room.get("address", "Unknown address")
    city = room.get("city", "")
    total_rent = room.get("total_rent")
    area = room.get("area")
    rooms = room.get("rooms")
    room_type = room.get("type", "")
    available_from = room.get("available_from", "")
    deadline = room.get("deadline", "")
    url = room.get("url", "")
    url_key = room.get("url_key") or room.get("_raw", {}).get("urlKey", "")

    price_str = f"€{total_rent:,.2f}/month" if total_rent else "Not specified"
    area_str = f"{area} m²" if area else "Not specified"

    text = f"""
ROOM DETAILS
{'=' * 50}

📍 Address: {address}, {city}

💰 Total Rent: {price_str}
📐 Area: {area_str}
🚪 Rooms: {rooms if rooms else 'Not specified'}
🏠 Type: {room_type if room_type else 'Not specified'}
📅 Available From: {available_from if available_from else 'Not specified'}
⏰ Deadline: {deadline if deadline else 'Not specified'}
🔑 URL Key: {url_key}

🔗 View Listing: {url if url else 'Not available'}

{'=' * 50}
"""

    return text


def send_application_email(
        room: dict,
        success: bool,
        error_message: Optional[str] = None,
        config: Optional[dict] = None
) -> bool:
    """
    Send an email notification about an application attempt.

    Args:
        room: Dictionary containing room information
        success: Whether the application was successful
        error_message: Optional error message if application failed
        config: Optional config override (uses EMAIL_CONFIG if not provided)

    Returns:
        True if email was sent successfully, False otherwise
    """

    cfg = config or EMAIL_CONFIG

    # Check if email is configured
    if not cfg["smtp_username"] or not cfg["smtp_password"]:
        print("[Email] ⚠️  Email not configured. Set SMTP_USERNAME, SMTP_PASSWORD, and NOTIFY_EMAIL environment variables.")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    address = room.get("address", "Unknown")
    city = room.get("city", "")

    # Build subject line
    status_emoji = "✅" if success else "❌"
    status_text = "SUCCESS" if success else "FAILED"
    subject = f"{cfg['subject_prefix']} {status_emoji} Application {status_text}: {address}, {city}"

    # Build HTML body
    if success:
        status_html = """
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong>✅ APPLICATION SUBMITTED SUCCESSFULLY</strong>
            <p style="margin: 5px 0 0 0;">The bot has automatically applied to this room.</p>
        </div>
        """
    else:
        error_detail = f"<p style='margin: 5px 0 0 0;'><strong>Error:</strong> {error_message}</p>" if error_message else ""
        status_html = f"""
        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong>❌ APPLICATION FAILED</strong>
            <p style="margin: 5px 0 0 0;">The bot attempted to apply but encountered an error.</p>
            {error_detail}
        </div>
        """

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2c3e50; text-align: center;">🏠 Roommatch Application Notification</h1>

            <p style="color: #666; text-align: center; font-size: 14px;">
                {timestamp}
            </p>

            {status_html}

            {format_room_html(room)}

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

            <p style="color: #999; font-size: 12px; text-align: center;">
                This is an automated message from the Roommatch Auto-Apply Bot.
            </p>
        </div>
    </body>
    </html>
    """

    # Build plain text body
    status_text_body = "✅ APPLICATION SUBMITTED SUCCESSFULLY" if success else f"❌ APPLICATION FAILED\nError: {error_message or 'Unknown error'}"

    text_body = f"""
ROOMMATCH APPLICATION NOTIFICATION
{'=' * 50}

Timestamp: {timestamp}

STATUS: {status_text_body}

{format_room_text(room)}

This is an automated message from the Roommatch Auto-Apply Bot.
"""

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from_email"]
    msg["To"] = cfg["to_email"]

    # Attach both plain text and HTML versions
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    # Send email
    try:
        print(f"[Email] Sending notification to {cfg['to_email']}...")

        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg["smtp_server"], cfg["smtp_port"])

        server.login(cfg["smtp_username"], cfg["smtp_password"])
        server.sendmail(cfg["from_email"], cfg["to_email"], msg.as_string())
        server.quit()

        print(f"[Email] ✅ Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[Email] ❌ Authentication failed. Check your username and password.")
        print("[Email]    For Gmail, make sure you're using an App Password.")
        return False
    except smtplib.SMTPException as e:
        print(f"[Email] ❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[Email] ❌ Error sending email: {e}")
        return False


def test_email_config():
    """Send a test email to verify configuration."""

    test_room = {
        "id": 12345,
        "url_key": "12345-test-street-123-amsterdam",
        "address": "Test Street 123",
        "city": "Amsterdam",
        "total_rent": 750.00,
        "area": 25,
        "rooms": 1,
        "type": "Studio",
        "available_from": "2025-01-01",
        "deadline": "2024-12-15",
        "url": "https://www.roommatch.nl/aanbod/studentenwoningen/details/12345-test-street-123-amsterdam",
    }

    print("=" * 50)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 50)
    print(f"\nSMTP Server: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
    print(f"From: {EMAIL_CONFIG['from_email']}")
    print(f"To: {EMAIL_CONFIG['to_email']}")
    print(f"TLS: {EMAIL_CONFIG['use_tls']}")
    print("\nSending test email...")

    success = send_application_email(test_room, success=True)

    if success:
        print("\n✅ Test email sent! Check your inbox.")
    else:
        print("\n❌ Failed to send test email. Check your configuration.")

    return success


if __name__ == "__main__":
    test_email_config()
