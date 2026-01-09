"""
Multi-channel notification service.

Sends alerts via email, SMS, Slack, Teams, and webhooks.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from typing import Dict, List
import structlog

from config import settings

logger = structlog.get_logger()


class Notifier:
    """
    Multi-channel notification sender.

    Delivers alerts through configured notification channels.
    """

    def __init__(self):
        self.smtp_configured = bool(settings.smtp_host and settings.smtp_user)
        self.slack_configured = bool(settings.slack_webhook_url)
        self.teams_configured = bool(settings.teams_webhook_url)

    async def send_alert(
        self,
        alert: Dict,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """
        Send alert through specified channels.

        Args:
            alert: Alert data
            channels: List of channels (email, slack, teams, sms)
                     If None, sends to all configured channels

        Returns:
            Dictionary of channel: success status
        """
        if channels is None:
            channels = self._get_default_channels(alert.get("severity"))

        results = {}

        for channel in channels:
            try:
                if channel == "email" and self.smtp_configured:
                    results["email"] = await self.send_email(alert)
                elif channel == "slack" and self.slack_configured:
                    results["slack"] = await self.send_slack(alert)
                elif channel == "teams" and self.teams_configured:
                    results["teams"] = await self.send_teams(alert)
                else:
                    results[channel] = False
                    logger.warning(f"{channel}_not_configured")

            except Exception as e:
                logger.error(f"{channel}_send_error", error=str(e))
                results[channel] = False

        return results

    async def send_email(self, alert: Dict) -> bool:
        """
        Send alert via email.

        Args:
            alert: Alert data

        Returns:
            Success status
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = alert.get("title", "Ground Operations Alert")
            msg["From"] = settings.alert_from_email
            msg["To"] = settings.smtp_user  # In production, use recipient list

            # Create email body
            text = self._format_email_text(alert)
            html = self._format_email_html(alert)

            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info("email_sent", title=alert.get("title"))
            return True

        except Exception as e:
            logger.error("email_send_error", error=str(e))
            return False

    async def send_slack(self, alert: Dict) -> bool:
        """
        Send alert to Slack via webhook.

        Args:
            alert: Alert data

        Returns:
            Success status
        """
        try:
            severity_colors = {
                "info": "#36a64f",
                "warning": "#ff9800",
                "critical": "#f44336"
            }

            payload = {
                "attachments": [{
                    "color": severity_colors.get(alert.get("severity"), "#gray"),
                    "title": alert.get("title"),
                    "text": alert.get("message"),
                    "fields": [
                        {
                            "title": "Flight",
                            "value": alert.get("flight_number", "N/A"),
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.get("severity", "unknown").upper(),
                            "short": True
                        }
                    ],
                    "footer": "Ground Operations Platform",
                    "ts": alert.get("triggered_at", "").timestamp() if isinstance(alert.get("triggered_at"), datetime) else 0
                }]
            }

            # Add recommended actions if present
            if alert.get("recommended_actions"):
                actions_text = "\n".join(f"• {action}" for action in alert["recommended_actions"])
                payload["attachments"][0]["fields"].append({
                    "title": "Recommended Actions",
                    "value": actions_text,
                    "short": False
                })

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info("slack_sent", title=alert.get("title"))
            return True

        except Exception as e:
            logger.error("slack_send_error", error=str(e))
            return False

    async def send_teams(self, alert: Dict) -> bool:
        """
        Send alert to Microsoft Teams via webhook.

        Args:
            alert: Alert data

        Returns:
            Success status
        """
        try:
            severity_colors = {
                "info": "00ff00",
                "warning": "ff9800",
                "critical": "ff0000"
            }

            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": alert.get("title"),
                "themeColor": severity_colors.get(alert.get("severity"), "808080"),
                "title": alert.get("title"),
                "sections": [{
                    "activityTitle": "Ground Operations Alert",
                    "activitySubtitle": alert.get("triggered_at", "").isoformat() if isinstance(alert.get("triggered_at"), datetime) else "",
                    "facts": [
                        {"name": "Flight", "value": alert.get("flight_number", "N/A")},
                        {"name": "Severity", "value": alert.get("severity", "unknown").upper()},
                        {"name": "Message", "value": alert.get("message", "")}
                    ]
                }]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.teams_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info("teams_sent", title=alert.get("title"))
            return True

        except Exception as e:
            logger.error("teams_send_error", error=str(e))
            return False

    def _get_default_channels(self, severity: str) -> List[str]:
        """Get default notification channels based on severity."""
        if severity == "critical":
            return ["email", "slack", "teams"]
        elif severity == "warning":
            return ["slack", "teams"]
        else:
            return ["slack"]

    def _format_email_text(self, alert: Dict) -> str:
        """Format alert as plain text email."""
        text = f"""
Ground Operations Alert
=======================

{alert.get('title', 'Alert')}

{alert.get('message', '')}

Severity: {alert.get('severity', 'unknown').upper()}
Flight: {alert.get('flight_number', 'N/A')}
"""
        if alert.get("recommended_actions"):
            text += "\nRecommended Actions:\n"
            for action in alert["recommended_actions"]:
                text += f"  • {action}\n"

        text += "\n---\nGround Operations Intelligence Platform"
        return text

    def _format_email_html(self, alert: Dict) -> str:
        """Format alert as HTML email."""
        severity_colors = {
            "info": "#4caf50",
            "warning": "#ff9800",
            "critical": "#f44336"
        }
        color = severity_colors.get(alert.get("severity"), "#gray")

        html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <div style="border-left: 4px solid {color}; padding-left: 20px;">
      <h2>{alert.get('title', 'Alert')}</h2>
      <p>{alert.get('message', '')}</p>
      <p><strong>Severity:</strong> {alert.get('severity', 'unknown').upper()}</p>
      <p><strong>Flight:</strong> {alert.get('flight_number', 'N/A')}</p>
"""
        if alert.get("recommended_actions"):
            html += "      <h3>Recommended Actions:</h3><ul>"
            for action in alert["recommended_actions"]:
                html += f"<li>{action}</li>"
            html += "</ul>"

        html += """
    </div>
    <p style="color: #666; font-size: 12px; margin-top: 20px;">
      Ground Operations Intelligence Platform
    </p>
  </body>
</html>
"""
        return html
