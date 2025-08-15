# tools/email_tools.py
import logging
import asyncio
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
from livekit.agents import function_tool, RunContext

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    JARVIS Email Transmission System. Execute immediately when commanded to send emails.
    
    MANDATORY USAGE: Use this tool every time the user mentions:
    - "send an email" 
    - "email this/that to"
    - "forward to"
    - "send this information to"
    - Any variation of email sending requests
    
    Args:
        to_email: Target recipient email address
        subject: Message subject line  
        message: Email body content
        cc_email: Optional carbon copy recipient
    
    Sir expects immediate execution when email transmission is requested.
    """
    try:
        # Log that the email function was called
        logging.info(f"send_email function called: to={to_email}, subject='{subject}'")
        print(f"EMAIL TOOL CALLED: Sending to {to_email}")

        # Validate credentials first
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Validate email format
        if not to_email or '@' not in to_email:
            return "Email sending failed: Invalid recipient email address."
        
        # Run the email sending with proper async handling and timeout
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                _send_email_sync, 
                gmail_user, 
                gmail_password, 
                to_email, 
                subject, 
                message, 
                cc_email
            ),
            timeout=30.0  # Increased timeout
        )
        
        return result
        
    except asyncio.TimeoutError:
        logging.error("Email sending timed out")
        return "Email sending failed: Operation timed out. Please try again."
    except Exception as e:
        logging.error(f"Error in async email wrapper: {e}")
        return f"An error occurred while sending email: {str(e)}"

def _send_email_sync(gmail_user: str, gmail_password: str, to_email: str, 
                    subject: str, message: str, cc_email: Optional[str] = None) -> str:
    """Synchronous email sending function with retry logic."""
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # Gmail SMTP configuration
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add CC if provided
            recipients = [to_email]
            if cc_email:
                msg['Cc'] = cc_email
                recipients.append(cc_email)
            
            # Attach message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to Gmail SMTP server with timeout
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.starttls()
            server.login(gmail_user, gmail_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(gmail_user, recipients, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {to_email}")
            return f"Email sent successfully to {to_email}"
            
        except smtplib.SMTPAuthenticationError:
            logging.error("Gmail authentication failed")
            return "Email sending failed: Authentication error. Please check your Gmail app password."
        except smtplib.SMTPException as e:
            logging.error(f"SMTP error occurred: {e}")
            if retry_count < max_retries:
                retry_count += 1
                logging.info(f"Retrying email send (attempt {retry_count}/{max_retries})")
                time.sleep(2)  # Wait before retry
                continue
            return f"Email sending failed: SMTP error - {str(e)}"
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            if retry_count < max_retries:
                retry_count += 1
                logging.info(f"Retrying email send (attempt {retry_count}/{max_retries})")
                time.sleep(2)  # Wait before retry
                continue
            return f"An error occurred while sending email: {str(e)}"
    
    return "Email sending failed after multiple attempts."