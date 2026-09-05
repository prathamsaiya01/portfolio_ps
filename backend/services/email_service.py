from __future__ import annotations

import html
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional
from urllib.parse import quote

from backend.config import get_settings
from backend.services.approval_token_service import ApprovalTokenService


class EmailDeliveryError(RuntimeError):
    """Raised when configured email delivery cannot complete."""


class EmailService:
    def __init__(self, settings: Optional[Dict[str, Any]] = None, token_service: Optional[ApprovalTokenService] = None):
        self.settings = settings or get_settings()
        self.token_service = token_service or ApprovalTokenService()

    async def send_candidate_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        provider = str(self.settings.get("email_provider") or "smtp").lower()
        if provider != "smtp":
            raise EmailDeliveryError("Email provider is not supported")

        recipient = self.settings.get("email_to")
        sender = self.settings.get("email_from")
        host = self.settings.get("email_host")
        if not recipient or not sender or not host:
            raise EmailDeliveryError("Email delivery is not configured")

        tokens = {
            action: self.token_service.create_token(str(candidate.get("candidate_id")), action)
            for action in ("APPROVE", "REJECT", "REVIEW")
        }
        base_url = str(self.settings.get("frontend_base_url") or "http://localhost:3000").rstrip("/")
        links = {action: f"{base_url}/approval/{quote(token, safe='')}" for action, token in tokens.items()}
        message = self._build_message(candidate, links, sender, recipient)
        try:
            self._send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailDeliveryError("Email delivery failed") from exc

        return {"tokens": tokens, "recipient": recipient}

    def _send_message(self, message: EmailMessage) -> None:
        host = str(self.settings["email_host"])
        port = int(self.settings.get("email_port") or 587)
        username = self.settings.get("email_username")
        password = self.settings.get("email_password")
        use_tls = str(self.settings.get("email_use_tls", "true")).lower() not in {"0", "false", "no"}
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if use_tls:
                smtp.starttls()
            if username:
                smtp.login(username, password or "")
            smtp.send_message(message)

    @staticmethod
    def _text(value: Any, fallback: str = "Not recorded") -> str:
        if value is None or value == "":
            return fallback
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) or fallback
        return str(value)

    def _build_message(self, candidate: Dict[str, Any], links: Dict[str, str], sender: str, recipient: str) -> EmailMessage:
        name = self._text(candidate.get("suggested_title") or candidate.get("repository_name"), "Untitled project")
        repository = self._text(candidate.get("full_name") or candidate.get("repository_name"))
        description = self._text(candidate.get("suggested_description") or candidate.get("description"))
        scores = candidate.get("scores") or {}
        evidence = candidate.get("evidence") or []
        evidence_text = "\n".join(f"- {self._text(item)}" for item in evidence) or "- Not recorded"
        subject = f"New Portfolio Candidate - {name}"
        text = (
            f"Portfolio recommendation: {name}\n\n"
            "This project is a recommendation for future portfolio publication. It has not been published.\n\n"
            f"Repository: {repository}\n"
            f"Suggested description: {description}\n"
            f"Overall score: {self._text(candidate.get('overall_score'))}\n"
            f"Candidate priority: {self._text(candidate.get('candidate_priority'))}\n"
            f"Technical depth: {self._text(scores.get('technical_depth'))}\n"
            f"Originality: {self._text(scores.get('originality'))}\n"
            f"Impact: {self._text(scores.get('impact'))}\n"
            f"Portfolio fit: {self._text(scores.get('portfolio_fit') or candidate.get('portfolio_fit_score'))}\n"
            f"Duplicate risk: {self._text(candidate.get('duplicate_risk'))}\n"
            f"Why it stands out: {self._text(candidate.get('differentiation_reason'))}\n\n"
            f"Key evidence:\n{evidence_text}\n\n"
            f"Approve: {links['APPROVE']}\nReject: {links['REJECT']}\nReview later: {links['REVIEW']}"
        )
        safe_name = html.escape(name)
        safe_repository = html.escape(repository)
        safe_description = html.escape(description)
        safe_evidence = "".join(f"<li>{html.escape(self._text(item))}</li>" for item in evidence) or "<li>Not recorded</li>"
        html_body = f"""
        <html><body style=\"font-family:Arial,sans-serif;color:#17211e;line-height:1.5\">
        <h2>New portfolio candidate: {safe_name}</h2>
        <p><strong>Recommendation for future publication.</strong> This project has not been published.</p>
        <p><strong>Repository:</strong> {safe_repository}</p>
        <p>{safe_description}</p>
        <table cellpadding=\"8\"><tr><td>Overall score</td><td>{html.escape(self._text(candidate.get('overall_score')))}</td></tr>
        <tr><td>Candidate priority</td><td>{html.escape(self._text(candidate.get('candidate_priority')))}</td></tr>
        <tr><td>Technical depth</td><td>{html.escape(self._text(scores.get('technical_depth')))}</td></tr>
        <tr><td>Originality</td><td>{html.escape(self._text(scores.get('originality')))}</td></tr>
        <tr><td>Impact</td><td>{html.escape(self._text(scores.get('impact')))}</td></tr>
        <tr><td>Portfolio fit</td><td>{html.escape(self._text(scores.get('portfolio_fit') or candidate.get('portfolio_fit_score')))}</td></tr>
        <tr><td>Duplicate risk</td><td>{html.escape(self._text(candidate.get('duplicate_risk')))}</td></tr></table>
        <p><strong>Why it stands out:</strong> {html.escape(self._text(candidate.get('differentiation_reason')))}</p>
        <p><strong>Key evidence</strong></p><ul>{safe_evidence}</ul>
        <p><a href=\"{html.escape(links['APPROVE'])}\">YES - ADD TO PORTFOLIO</a></p>
        <p><a href=\"{html.escape(links['REJECT'])}\">NO - REJECT</a></p>
        <p><a href=\"{html.escape(links['REVIEW'])}\">REVIEW LATER</a></p>
        </body></html>
        """
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient
        message.set_content(text)
        message.add_alternative(html_body, subtype="html")
        return message
