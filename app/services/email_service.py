import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import os

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@atcdrive.com')
    
    def send_password_reset_email(self, to_email: str, reset_token: str, username: str):
        """Send password reset email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "ATC Drive - Password Reset Request"
            
            # Create HTML body
            reset_url = f"http://localhost:3000/reset-password?token={reset_token}&email={to_email}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">ATC Drive</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Password Reset Request</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hello {username},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        We received a request to reset your password for your ATC Drive account. 
                        If you didn't make this request, you can safely ignore this email.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; 
                                  padding: 15px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  display: inline-block; 
                                  font-weight: bold;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6; font-size: 14px;">
                        This link will expire in 1 hour. If you're having trouble clicking the button, 
                        copy and paste this URL into your browser:
                    </p>
                    
                    <p style="background: #e9ecef; padding: 15px; border-radius: 5px; word-break: break-all; font-size: 12px; color: #495057;">
                        {reset_url}
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        If you didn't request this password reset, please ignore this email. 
                        Your password will remain unchanged.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                return True
            else:
                # For development, just print the email
                print(f"=== PASSWORD RESET EMAIL ===")
                print(f"To: {to_email}")
                print(f"Subject: ATC Drive - Password Reset Request")
                print(f"Reset URL: {reset_url}")
                print(f"===============================")
                return True
                
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str):
        """Send welcome email to new users"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Welcome to ATC Drive!"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Welcome to ATC Drive!</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Your secure file storage solution</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hello {username},</h2>
                    
                    <p style="color: #666; line-height: 1.6;">
                        Welcome to ATC Drive! Your account has been successfully created. 
                        You can now start uploading, organizing, and sharing your files securely.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/login" 
                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                  color: white; 
                                  padding: 15px 30px; 
                                  text-decoration: none; 
                                  border-radius: 25px; 
                                  display: inline-block; 
                                  font-weight: bold;
                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                            Get Started
                        </a>
                    </div>
                    
                    <p style="color: #666; line-height: 1.6;">
                        If you have any questions or need assistance, please don't hesitate to contact our support team.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            if self.smtp_username and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                return True
            else:
                print(f"=== WELCOME EMAIL ===")
                print(f"To: {to_email}")
                print(f"Subject: Welcome to ATC Drive!")
                print(f"===============================")
                return True
                
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

email_service = EmailService()


