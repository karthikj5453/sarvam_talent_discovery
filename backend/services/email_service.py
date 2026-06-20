"""
Email Notification Service
Sends transactional emails using SMTP (configured via environment variables).
Falls back silently if SMTP is not configured so the app never breaks.

Security: Uses SMTP_SSL (port 465) by default for enforced TLS.
STARTTLS (port 587) is supported via SMTP_USE_SSL=false in .env.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    """Returns True only if SMTP credentials are properly set."""
    return bool(
        settings.SMTP_HOST
        and settings.SMTP_USER
        and settings.SMTP_PASSWORD
        and settings.SMTP_HOST not in ("", "your_smtp_host")
    )


def _send(to_email: str, subject: str, html_body: str) -> bool:
    """Internal: send one HTML email. Returns True on success."""
    if not _is_configured():
        logger.info("[Email] SMTP not configured -- skipping email to %s: %s", to_email, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        if settings.SMTP_USE_SSL:
            # SMTP_SSL: connects with TLS from the start (port 465) — enforced, no downgrade
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        else:
            # STARTTLS (port 587) — with explicit verification the upgrade succeeded
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                code, _ = server.starttls()
                if code != 220:
                    raise RuntimeError(f"STARTTLS failed with code {code}")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info("[Email] Sent '%s' to %s", subject, to_email)
        return True
    except Exception as e:
        logger.warning("[Email] Failed to send email to %s: %s", to_email, e)
        return False


# ─── TEMPLATES ────────────────────────────────────────────────

def send_application_received(candidate_name: str, candidate_email: str, job_title: str) -> bool:
    """Email to candidate confirming their application was received."""
    subject = f"Application received -- {job_title}"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#0f172a;color:#e2e8f0;border-radius:12px;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;padding:10px 20px;">
          <span style="color:#fff;font-weight:800;font-size:18px;">Sarvam Talent</span>
        </div>
      </div>
      <h2 style="color:#fff;font-size:22px;font-weight:700;margin-bottom:12px;">Hi {candidate_name}, we got your application!</h2>
      <p style="color:#94a3b8;line-height:1.6;">You've successfully applied for <strong style="color:#a5b4fc">{job_title}</strong>. Your AI-powered screening session has been initialized.</p>
      <p style="color:#94a3b8;line-height:1.6;">The system will evaluate you across <strong>7 competency dimensions</strong> using your voice responses &mdash; in any Indian language you're comfortable with.</p>
      <div style="background:#1e293b;border-radius:8px;padding:16px;margin:24px 0;border-left:4px solid #6366f1;">
        <p style="color:#c7d2fe;margin:0;font-size:14px;"><strong>Speak naturally</strong> &mdash; Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, or Punjabi are all supported.</p>
      </div>
      <p style="color:#64748b;font-size:13px;margin-top:32px;text-align:center;">Powered by Sarvam AI &amp; Google Gemini 2.0</p>
    </div>
    """
    return _send(candidate_email, subject, html)


def send_screening_complete(candidate_name: str, candidate_email: str, job_title: str, total_score: float | None = None) -> bool:
    """Email to candidate once their AI evaluation is complete."""
    score_text = f"{total_score:.1f}/10" if total_score is not None else "being processed"
    subject = f"Your screening results are in -- {job_title}"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#0f172a;color:#e2e8f0;border-radius:12px;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;padding:10px 20px;">
          <span style="color:#fff;font-weight:800;font-size:18px;">Sarvam Talent</span>
        </div>
      </div>
      <h2 style="color:#fff;font-size:22px;font-weight:700;margin-bottom:12px;">Screening complete, {candidate_name}!</h2>
      <p style="color:#94a3b8;line-height:1.6;">Your AI screening for <strong style="color:#a5b4fc">{job_title}</strong> has been evaluated.</p>
      <div style="background:#1e293b;border-radius:8px;padding:20px;margin:24px 0;text-align:center;">
        <p style="color:#94a3b8;margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:0.06em;">Overall Score</p>
        <p style="color:#34d399;font-size:36px;font-weight:900;margin:0;">{score_text}</p>
      </div>
      <p style="color:#94a3b8;line-height:1.6;">The hiring team will review your profile and reach out if you're shortlisted. Thank you for your time!</p>
      <p style="color:#64748b;font-size:13px;margin-top:32px;text-align:center;">Powered by Sarvam AI &amp; Google Gemini 2.0</p>
    </div>
    """
    return _send(candidate_email, subject, html)


def send_hr_new_candidate_alert(hr_email: str, candidate_name: str, job_title: str, total_score: float | None = None, dashboard_url: str = "") -> bool:
    """Alert HR when a new candidate completes their screening and is evaluated."""
    score_text = f"{total_score:.1f}/10" if total_score is not None else "Pending"
    score_color = "#34d399" if (total_score or 0) >= 6.0 else "#a5b4fc"
    subject = f"New screened candidate: {candidate_name} -- {job_title}"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#0f172a;color:#e2e8f0;border-radius:12px;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;padding:10px 20px;">
          <span style="color:#fff;font-weight:800;font-size:18px;">Sarvam HR Dashboard</span>
        </div>
      </div>
      <h2 style="color:#fff;font-size:20px;font-weight:700;margin-bottom:12px;">New candidate evaluated</h2>
      <div style="background:#1e293b;border-radius:8px;padding:20px;margin:16px 0;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="color:#64748b;font-size:13px;padding:6px 0;">Candidate</td><td style="color:#fff;font-weight:600;text-align:right;">{candidate_name}</td></tr>
          <tr><td style="color:#64748b;font-size:13px;padding:6px 0;">Applied Role</td><td style="color:#a5b4fc;font-weight:600;text-align:right;">{job_title}</td></tr>
          <tr><td style="color:#64748b;font-size:13px;padding:6px 0;">AI Score</td><td style="color:{score_color};font-size:20px;font-weight:800;text-align:right;">{score_text}</td></tr>
        </table>
      </div>
      {f'<div style="text-align:center;margin-top:24px;"><a href="{dashboard_url}" style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:700;font-size:15px;">View in Dashboard</a></div>' if dashboard_url else ''}
      <p style="color:#64748b;font-size:13px;margin-top:32px;text-align:center;">Sarvam Talent Discovery Engine</p>
    </div>
    """
    return _send(hr_email, subject, html)


def send_status_update(candidate_name: str, candidate_email: str, job_title: str, new_status: str) -> bool:
    """Notify candidate when their application status changes (shortlisted, offered, rejected)."""
    status_messages = {
        "shortlisted": ("Great news! You've been shortlisted", "#34d399", "Congratulations! The hiring team has reviewed your AI screening and shortlisted you for the next round."),
        "offered":     ("You've received an offer!", "#fbbf24", "Congratulations! The hiring team is excited to extend you an offer. They will be in touch with the details shortly."),
        "rejected":    ("Your application status update", "#94a3b8", "Thank you for your time and effort in completing the screening. After careful review, the team has decided to move forward with other candidates for this role."),
        "interviewing":("Next round scheduled", "#a5b4fc", "The hiring team wants to speak with you! They will reach out to schedule your next interview round."),
    }
    emoji, color, message = status_messages.get(new_status, ("Application update", "#94a3b8", f"Your application status has been updated to: {new_status}"))
    subject = f"{emoji} -- {job_title}"
    html = f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#0f172a;color:#e2e8f0;border-radius:12px;">
      <h2 style="color:{color};font-size:22px;font-weight:700;margin-bottom:12px;">{emoji}</h2>
      <p style="color:#94a3b8;line-height:1.6;">Hi <strong style="color:#fff">{candidate_name}</strong>,</p>
      <p style="color:#94a3b8;line-height:1.6;">{message}</p>
      <p style="color:#94a3b8;line-height:1.6;">Role applied: <strong style="color:#a5b4fc">{job_title}</strong></p>
      <p style="color:#64748b;font-size:13px;margin-top:32px;text-align:center;">Sarvam Talent Discovery Engine</p>
    </div>
    """
    return _send(candidate_email, subject, html)
