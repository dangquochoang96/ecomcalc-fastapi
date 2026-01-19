from typing import List
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        # Configure your email service here (SMTP, SendGrid, etc.)
        pass
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        """
        Send an email
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            html: Whether the body is HTML
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Add your email sending logic here
            logger.info(f"Sending email to {to} with subject: {subject}")
            # Example: Use smtplib, SendGrid, AWS SES, etc.
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_welcome_email(self, email: str, username: str) -> bool:
        """Send a welcome email to a new user"""
        subject = "Welcome to Our Platform!"
        body = f"Hello {username},\n\nWelcome to our platform!"
        return await self.send_email([email], subject, body)
    
    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send a password reset email"""
        subject = "Password Reset Request"
        body = f"Click here to reset your password: {reset_token}"
        return await self.send_email([email], subject, body)
