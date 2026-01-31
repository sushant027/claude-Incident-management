"""
Email utility for sending reminders
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from config import settings

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = None
) -> bool:
    """
    Send email via Gmail SMTP
    Returns True if successful, False otherwise
    """
    if not settings.email_enabled:
        print(f"Email disabled. Would send to {to_email}: {subject}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add text and HTML parts
        if body_text:
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
        
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)
        
        # Send via Gmail SMTP
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent to {to_email}: {subject}")
        return True
        
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_corrective_action_reminder(
    to_email: str,
    to_name: str,
    action_title: str,
    action_description: str,
    incident_id: int,
    incident_title: str,
    due_date: str,
    action_id: int
) -> bool:
    """
    Send reminder email for corrective action
    """
    subject = f"Reminder: Corrective Action Due - {action_title}"
    
    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #0066cc;">Corrective Action Reminder</h2>
        
        <p>Dear {to_name},</p>
        
        <p>This is a reminder that you have an open corrective action:</p>
        
        <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0;">
            <h3 style="margin-top: 0;">{action_title}</h3>
            <p><strong>Description:</strong> {action_description}</p>
            <p><strong>Due Date:</strong> {due_date}</p>
            <p><strong>Related Incident:</strong> #{incident_id} - {incident_title}</p>
        </div>
        
        <p>Please complete this action as soon as possible.</p>
        
        <p style="margin-top: 30px;">
            <a href="http://localhost:8000/incidents/{incident_id}" 
               style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                View Incident
            </a>
        </p>
        
        <p style="margin-top: 30px; font-size: 12px; color: #666;">
            This is an automated reminder from the Enterprise Incident Management Platform.
        </p>
    </body>
    </html>
    """
    
    body_text = f"""
Corrective Action Reminder

Dear {to_name},

This is a reminder that you have an open corrective action:

{action_title}
Description: {action_description}
Due Date: {due_date}
Related Incident: #{incident_id} - {incident_title}

Please complete this action as soon as possible.

---
This is an automated reminder from the Enterprise Incident Management Platform.
    """
    
    return send_email(to_email, subject, body_html, body_text)
