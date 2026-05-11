import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
CLINIC_EMAIL = os.getenv("CLINIC_EMAIL")

def send_email(to: str, subject: str, html: str):
    """Send email via Gmail SMTP"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Smile Dental <{GMAIL_USER}>"
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())
        print(f"Email sent to {to}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_appointment_confirmation(patient_name: str, patient_email: str,
                                   appointment_date: str, appointment_time: str,
                                   dentist: str, reason: str, insurance: str):
    """Send beautiful appointment confirmation to patient"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f8f7f4; margin: 0; padding: 40px 20px; }}
  .container {{ max-width: 560px; margin: 0 auto; }}
  .header {{ background: #1a6b5a; borderRadius: 12px 12px 0 0; padding: 32px 40px; text-align: center; border-radius: 12px 12px 0 0; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 22px; font-weight: 400; letter-spacing: 0.02em; }}
  .header p {{ color: rgba(255,255,255,0.75); margin: 8px 0 0; font-size: 14px; }}
  .body {{ background: #ffffff; padding: 40px; border-left: 1px solid #e8e6e1; border-right: 1px solid #e8e6e1; }}
  .greeting {{ font-size: 18px; color: #1a1917; margin-bottom: 8px; }}
  .subtext {{ color: #6b6860; font-size: 14px; line-height: 1.6; margin-bottom: 32px; }}
  .card {{ background: #f8f7f4; border-radius: 10px; padding: 24px; margin-bottom: 24px; }}
  .card-title {{ font-size: 11px; font-weight: 600; color: #9b9890; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 16px; }}
  .detail-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #e8e6e1; }}
  .detail-row:last-child {{ border-bottom: none; }}
  .detail-label {{ font-size: 13px; color: #6b6860; }}
  .detail-value {{ font-size: 13px; font-weight: 500; color: #1a1917; }}
  .emergency-note {{ background: #e8f3f0; border-radius: 8px; padding: 16px; margin-bottom: 24px; font-size: 13px; color: #0f6e56; line-height: 1.6; }}
  .cta {{ text-align: center; margin: 32px 0; }}
  .cta a {{ background: #1a6b5a; color: #fff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 500; display: inline-block; }}
  .footer {{ background: #f2f1ee; padding: 24px 40px; text-align: center; border-radius: 0 0 12px 12px; border: 1px solid #e8e6e1; border-top: none; }}
  .footer p {{ margin: 0; font-size: 12px; color: #9b9890; line-height: 1.8; }}
  .divider {{ height: 1px; background: #e8e6e1; margin: 24px 0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🦷 Appointment Confirmed</h1>
    <p>Smile Dental — Your smile is our priority</p>
  </div>
  <div class="body">
    <div class="greeting">Hi {patient_name},</div>
    <p class="subtext">Your appointment has been successfully booked. Here are your appointment details. Please save this email for your records.</p>

    <div class="card">
      <div class="card-title">Appointment Details</div>
      <div class="detail-row"><span class="detail-label">Date</span><span class="detail-value">{appointment_date}</span></div>
      <div class="detail-row"><span class="detail-label">Time</span><span class="detail-value">{appointment_time}</span></div>
      <div class="detail-row"><span class="detail-label">Dentist</span><span class="detail-value">{dentist}</span></div>
      <div class="detail-row"><span class="detail-label">Reason</span><span class="detail-value">{reason}</span></div>
      <div class="detail-row"><span class="detail-label">Insurance</span><span class="detail-value">{insurance}</span></div>
    </div>

    <div class="card">
      <div class="card-title">Clinic Information</div>
      <div class="detail-row"><span class="detail-label">Address</span><span class="detail-value">123 Smile Street, Suite 100</span></div>
      <div class="detail-row"><span class="detail-label">Phone</span><span class="detail-value">(555) 123-4567</span></div>
      <div class="detail-row"><span class="detail-label">Hours</span><span class="detail-value">Mon–Fri 9am–6pm, Sat 9am–2pm</span></div>
      <div class="detail-row"><span class="detail-label">Parking</span><span class="detail-value">Free parking available</span></div>
    </div>

    <div class="emergency-note">
      📋 <strong>What to bring:</strong> Photo ID, insurance card, completed new patient forms (if first visit). Please arrive 10 minutes early.
    </div>

    <div class="cta">
      <a href="https://maps.google.com/?q=123+Smile+Street">Get Directions →</a>
    </div>

    <div class="divider"></div>
    <p style="font-size:13px;color:#6b6860;text-align:center;">Need to reschedule? Call us at (555) 123-4567 or reply to this email. We require 24 hours notice for cancellations.</p>
  </div>
  <div class="footer">
    <p>Smile Dental · 123 Smile Street, Suite 100<br>
    This confirmation was sent by our AI receptionist Aria<br>
    © 2026 Smile Dental. All rights reserved.</p>
  </div>
</div>
</body>
</html>
"""
    return send_email(patient_email, f"✅ Appointment Confirmed — Smile Dental", html)


def send_clinic_notification(patient_name: str, patient_email: str,
                              patient_phone: str, appointment_date: str,
                              appointment_time: str, reason: str,
                              insurance: str, is_emergency: bool = False,
                              dob: str = "", allergies: str = "",
                              notes: str = ""):
    """Send notification to clinic front desk"""
    emergency_banner = """
    <div style="background:#fdf0ef;border:1px solid #f5c6c2;border-radius:8px;padding:16px;margin-bottom:24px;">
      <strong style="color:#c0392b;">⚠ EMERGENCY PATIENT</strong>
      <p style="color:#993c1d;margin:4px 0 0;font-size:13px;">This patient reported severe dental pain. Please prepare an emergency slot immediately.</p>
    </div>
    """ if is_emergency else ""

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f8f7f4; margin: 0; padding: 40px 20px; }}
  .container {{ max-width: 560px; margin: 0 auto; background: #fff; border-radius: 12px; border: 1px solid #e8e6e1; overflow: hidden; }}
  .header {{ background: #1a1917; padding: 24px 32px; }}
  .header h1 {{ color: #fff; margin: 0; font-size: 18px; font-weight: 500; }}
  .header p {{ color: rgba(255,255,255,0.5); margin: 4px 0 0; font-size: 12px; }}
  .body {{ padding: 32px; }}
  .card {{ background: #f8f7f4; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
  .card-title {{ font-size: 11px; font-weight: 600; color: #9b9890; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }}
  .row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e8e6e1; font-size: 13px; }}
  .row:last-child {{ border-bottom: none; }}
  .label {{ color: #6b6860; }}
  .value {{ font-weight: 500; color: #1a1917; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>New Appointment Booked</h1>
    <p>Via Aria AI Receptionist · {appointment_date} at {appointment_time}</p>
  </div>
  <div class="body">
    {emergency_banner}
    <div class="card">
      <div class="card-title">Patient Information</div>
      <div class="row"><span class="label">Full Name</span><span class="value">{patient_name}</span></div>
      <div class="row"><span class="label">Date of Birth</span><span class="value">{dob or 'Not provided'}</span></div>
      <div class="row"><span class="label">Phone</span><span class="value">{patient_phone}</span></div>
      <div class="row"><span class="label">Email</span><span class="value">{patient_email}</span></div>
      <div class="row"><span class="label">Insurance</span><span class="value">{insurance}</span></div>
      <div class="row"><span class="label">Allergies</span><span class="value">{allergies or 'None reported'}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Appointment Details</div>
      <div class="row"><span class="label">Date</span><span class="value">{appointment_date}</span></div>
      <div class="row"><span class="label">Time</span><span class="value">{appointment_time}</span></div>
      <div class="row"><span class="label">Reason</span><span class="value">{reason}</span></div>
      <div class="row"><span class="label">Emergency</span><span class="value">{'YES — URGENT' if is_emergency else 'No'}</span></div>
    </div>
    {f'<div class="card"><div class="card-title">Notes</div><p style="font-size:13px;color:#1a1917;margin:0">{notes}</p></div>' if notes else ''}
  </div>
</div>
</body>
</html>
"""
    subject = f"{'🚨 EMERGENCY: ' if is_emergency else '📅 New Appointment: '}{patient_name} — {appointment_date}"
    return send_email(CLINIC_EMAIL, subject, html)