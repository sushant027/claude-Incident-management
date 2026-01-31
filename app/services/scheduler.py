"""
Email reminder scheduler for corrective actions
"""
import os
import sys
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from app.models import CorrectiveActionStatus
from app.models.corrective_action import CorrectiveAction
from app.utils.email import send_corrective_action_reminder
from app.utils.audit_log import log_audit
from app.models import AuditAction
from config import settings


def is_main_process():
    """
    Check if we're running in the main process.
    On Windows with uvicorn multiprocessing, we only want the scheduler
    to run in one process to avoid conflicts.
    """
    # Check for common multiprocessing indicators
    import multiprocessing
    current = multiprocessing.current_process()
    return current.name == 'MainProcess' or 'SpawnProcess' not in current.name


class ReminderScheduler:
    """
    Background scheduler for sending email reminders
    """

    def __init__(self):
        self.scheduler = None
        self._started = False

    def _init_scheduler(self):
        """Initialize the scheduler if not already done"""
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                self.send_reminders,
                'cron',
                hour=settings.EMAIL_REMINDER_HOUR,
                minute=settings.EMAIL_REMINDER_MINUTE,
                id='corrective_action_reminders',
                replace_existing=True
            )

    def start(self):
        """Start the scheduler"""
        # Only start in main process to avoid multiple schedulers
        if not is_main_process():
            return

        try:
            self._init_scheduler()
            if self.scheduler and not self.scheduler.running:
                self.scheduler.start()
                self._started = True
                print(f"Email reminder scheduler started (runs daily at {settings.EMAIL_REMINDER_HOUR}:{settings.EMAIL_REMINDER_MINUTE:02d})")
        except Exception as e:
            print(f"Warning: Could not start email scheduler: {e}")

    def shutdown(self):
        """Shutdown the scheduler"""
        if not self._started:
            return

        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                print("Email reminder scheduler stopped")
        except Exception as e:
            print(f"Warning: Error shutting down scheduler: {e}")
        finally:
            self._started = False
    
    def send_reminders(self):
        """
        Send email reminders for open corrective actions
        This runs daily
        """
        print(f"Running corrective action reminders at {datetime.now()}")
        
        db = SessionLocal()
        try:
            # Get all open and in-progress corrective actions
            actions = db.query(CorrectiveAction).filter(
                CorrectiveAction.status.in_([
                    CorrectiveActionStatus.OPEN,
                    CorrectiveActionStatus.IN_PROGRESS
                ])
            ).all()
            
            sent_count = 0
            failed_count = 0
            
            for action in actions:
                # Check if owner exists and has email
                if not action.owner or not action.owner.email:
                    continue
                
                # Send reminder
                success = send_corrective_action_reminder(
                    to_email=action.owner.email,
                    to_name=action.owner.name,
                    action_title=action.title,
                    action_description=action.description,
                    incident_id=action.incident_id,
                    incident_title=action.incident.title if action.incident else "N/A",
                    due_date=action.due_date.isoformat() if action.due_date else "N/A",
                    action_id=action.id
                )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Log reminder
                log_audit(
                    db=db,
                    entity_type="CORRECTIVE_ACTION",
                    entity_id=action.id,
                    action=AuditAction.UPDATE,
                    description=f"Email reminder sent to {action.owner.email}" if success else "Email reminder failed",
                    performed_by_id=None,  # System action
                    metadata={
                        "reminder_sent": success,
                        "recipient": action.owner.email
                    }
                )
            
            print(f"Reminders sent: {sent_count}, Failed: {failed_count}")
            
        except Exception as e:
            print(f"Error sending reminders: {str(e)}")
        finally:
            db.close()
    
    def send_test_reminder(self):
        """Send a test reminder immediately (for testing)"""
        print("Sending test reminders...")
        self.send_reminders()

# Global scheduler instance
reminder_scheduler = ReminderScheduler()
