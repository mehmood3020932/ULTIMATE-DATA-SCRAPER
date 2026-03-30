# services/notification-service/app/services/email_service.py

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import settings

# Setup Jinja2
env = Environment(loader=FileSystemLoader(settings.TEMPLATE_DIR))


class EmailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_addr = settings.EMAIL_FROM
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
    ):
        """Send templated email."""
        template = env.get_template(f"email/{template_name}.html")
        html_content = template.render(**context)
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to_email
        
        msg.attach(MIMEText(html_content, "html"))
        
        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            start_tls=True,
        )
    
    async def send_job_completion(self, to_email: str, job_id: str, success: bool):
        """Send job completion notification."""
        await self.send_email(
            to_email=to_email,
            subject=f"Scraping Job {'Completed' if success else 'Failed'}",
            template_name="job_complete",
            context={
                "job_id": job_id,
                "success": success,
                "dashboard_url": f"https://app.example.com/jobs/{job_id}",
            },
        )