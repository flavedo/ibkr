import json
import logging
import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from app.schemas.earnings_settings import EarningsPushSettings, TestSendResponse
from app.schemas.market_sentiment import MarketSentimentResponse
from app.services.financial_calendar_service import (
    _screen_earnings,
    _fetch_earnings_detail,
)
from app.services.market_sentiment_service import MarketSentimentService

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "data"
_CONFIG_FILE = _CONFIG_DIR / "earnings_push_settings.json"


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> EarningsPushSettings:
    _ensure_config_dir()
    if not _CONFIG_FILE.exists():
        return EarningsPushSettings()
    try:
        data = json.loads(_CONFIG_FILE.read_text())
        return EarningsPushSettings(**data)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to load settings: %s", exc)
        return EarningsPushSettings()


def save_settings(settings: EarningsPushSettings) -> EarningsPushSettings:
    _ensure_config_dir()
    _CONFIG_FILE.write_text(settings.model_dump_json(indent=2))
    logger.info("Earnings push settings saved")

    from app.core.earnings_scheduler import reschedule_push
    reschedule_push()

    return settings


def _build_html_table(events: list[dict[str, Any]]) -> str:
    rows = []
    for item in events:
        tag = "⚠️" if item.get("is_estimate", True) else "✅"
        eps_avg = item.get("eps_avg")
        eps_low = item.get("eps_low")
        eps_high = item.get("eps_high")
        rev_avg = item.get("rev_avg")

        eps_avg_str = f"${eps_avg:.2f}" if eps_avg is not None else "N/A"
        eps_range = (
            f"${eps_low:.2f}~${eps_high:.2f}"
            if eps_low is not None and eps_high is not None
            else "N/A"
        )
        rev_avg_str = (
            f"${rev_avg / 1e9:.2f}B" if rev_avg and rev_avg >= 1e9 else
            f"${rev_avg / 1e6:.1f}M" if rev_avg else "N/A"
        )
        mcap = item.get("mcap", 0)
        mcap_str = (
            f"${mcap / 1e12:.1f}T" if mcap >= 1e12 else
            f"${mcap / 1e9:.1f}B" if mcap >= 1e9 else
            f"${mcap / 1e6:.0f}M" if mcap >= 1e6 else
            f"${mcap}"
        )

        rows.append(f"""\
<tr>
  <td>{tag}</td>
  <td><b>{item.get('symbol', '')}</b></td>
  <td>{item.get('name', '')[:30]}</td>
  <td>{mcap_str}</td>
  <td>{item.get('date', '')}</td>
  <td>{eps_avg_str}</td>
  <td>{eps_range}</td>
  <td>{rev_avg_str}</td>
</tr>""")

    table_body = "\n".join(rows)
    return f"""\
<h2 style="color:#56d5ff;margin-top:28px">📈 今日美股财报日历</h2>
<p style="color:#8a9bb5">{date.today().isoformat()} 推送</p>
<table style="width:100%;border-collapse:collapse;font-size:14px">
<thead>
<tr style="background:rgba(62,169,255,0.12);color:#8a9bb5">
<th style="padding:8px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)"></th>
<th style="padding:8px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)">代码</th>
<th style="padding:8px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)">公司</th>
<th style="padding:8px;text-align:right;border-bottom:1px solid rgba(129,160,207,0.15)">市值</th>
<th style="padding:8px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)">日期</th>
<th style="padding:8px;text-align:right;border-bottom:1px solid rgba(129,160,207,0.15)">EPS均值</th>
<th style="padding:8px;text-align:right;border-bottom:1px solid rgba(129,160,207,0.15)">EPS范围</th>
<th style="padding:8px;text-align:right;border-bottom:1px solid rgba(129,160,207,0.15)">营收均值</th>
</tr>
</thead>
<tbody>
{table_body}
</tbody>
</table>
<p style="color:#5a6b85;font-size:12px;margin-top:16px">由 ibkr_show 自动推送 · 数据来源 Yahoo Finance</p>"""


def _build_sentiment_html(sentiment: MarketSentimentResponse) -> str:
    vix = sentiment.vix_value
    fg = sentiment.fear_greed_value

    vix_label = ""
    vix_color = "#8a9bb5"
    for r in sentiment.vix_ranges:
        if r.is_current:
            vix_label = f"{r.label} {r.sentiment}"
            vix_color = r.color
            break

    fg_label = ""
    fg_color = "#8a9bb5"
    for r in sentiment.fear_greed_ranges:
        if r.is_current:
            fg_label = f"{r.label} {r.sentiment}"
            fg_color = r.color
            break

    vix_display = f"{vix:.2f}" if vix is not None else "N/A"
    fg_display = str(fg) if fg is not None else "N/A"

    return f"""\
<div style="margin-bottom:28px">
  <h2 style="color:#56d5ff;margin-bottom:16px">🌡️ 今日美股情绪观察</h2>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <thead>
      <tr style="background:rgba(62,169,255,0.12);color:#8a9bb5">
        <th style="padding:10px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)">指标</th>
        <th style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.15)">数值</th>
        <th style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.15)">区间</th>
        <th style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.15)">情绪</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.15)">策略参考</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding:10px;border-bottom:1px solid rgba(129,160,207,0.08)"><b>VIX 恐慌指数</b></td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08)">{vix_display}</td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08);color:{vix_color}">{vix_label}</td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08)"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{vix_color};vertical-align:middle;margin-right:4px"></span>{sentiment.vix_level}</td>
        <td style="padding:10px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.08);color:#8a9bb5">{next((r.strategy for r in sentiment.vix_ranges if r.is_current), "")}</td>
      </tr>
      <tr>
        <td style="padding:10px;border-bottom:1px solid rgba(129,160,207,0.08)"><b>恐惧与贪婪指数</b></td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08)">{fg_display}</td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08);color:{fg_color}">{fg_label}</td>
        <td style="padding:10px;text-align:center;border-bottom:1px solid rgba(129,160,207,0.08)"><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{fg_color};vertical-align:middle;margin-right:4px"></span>{sentiment.fear_greed_level}</td>
        <td style="padding:10px;text-align:left;border-bottom:1px solid rgba(129,160,207,0.08);color:#8a9bb5">{next((r.strategy for r in sentiment.fear_greed_ranges if r.is_current), "")}</td>
      </tr>
    </tbody>
  </table>
</div>"""


def _send_email(
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    sender_email: str,
    target_email: str,
    subject: str,
    html_body: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = target_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Try SMTP_SSL first (port 465), fall back to STARTTLS (port 587/25)
    last_error: Exception | None = None

    for use_ssl in ([True, False] if smtp_port == 465 else [False, True]):
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

            with server:
                server.set_debuglevel(1)
                server.ehlo()
                if not use_ssl and server.has_extn("STARTTLS"):
                    ctx = ssl.create_default_context()
                    server.starttls(context=ctx)
                    server.ehlo()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, [target_email], msg.as_string())
                logger.info("Email sent via %s port %d (ssl=%s)", smtp_server, smtp_port, use_ssl)
                return
        except smtplib.SMTPServerDisconnected as exc:
            last_error = exc
            logger.warning("SMTP %s port %d (ssl=%s) failed: %s", smtp_server, smtp_port, use_ssl, exc)
            continue
        except Exception as exc:
            last_error = exc
            logger.warning("SMTP %s port %d (ssl=%s) failed: %s", smtp_server, smtp_port, use_ssl, exc)
            continue

    raise RuntimeError(f"Email send failed after all attempts") from last_error


def test_send(
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    sender_email: str,
    target_email: str,
) -> TestSendResponse:
    try:
        html = """\
<html><body style="font-family:sans-serif;background:#0a1220;color:#e8edf5;padding:20px">
<h2 style="color:#56d5ff">✅ 测试邮件</h2>
<p>如果收到此邮件，说明财报日历推送的邮件配置正确。</p>
<p style="color:#8a9bb5;font-size:12px">发送时间: %s</p>
</body></html>""" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        _send_email(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            sender_email=sender_email,
            target_email=target_email,
            subject="📧 [ibkr_show] 财报日历推送测试",
            html_body=html,
        )
        return TestSendResponse(success=True, message="测试邮件发送成功")
    except Exception as exc:
        logger.exception("Test send failed")
        return TestSendResponse(success=False, message=str(exc))


def trigger_daily_push() -> TestSendResponse:
    settings = load_settings()
    if not settings.enabled:
        return TestSendResponse(success=False, message="推送功能未开启")

    if not all([settings.smtp_server, settings.smtp_username, settings.smtp_password,
                settings.sender_email, settings.target_email]):
        return TestSendResponse(success=False, message="邮件配置不完整")

    try:
        today = date.today()
        end = today + timedelta(days=7)
        logger.info("Fetching earnings %s ~ %s for daily push", today, end)

        sentiment = MarketSentimentService().get_sentiment()
        sentiment_html = _build_sentiment_html(sentiment)

        stocks = _screen_earnings(today, end)
        if not stocks:
            body = f"""\
<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a1220;color:#e8edf5;padding:20px">
{sentiment_html}
<p style="color:#8a9bb5;margin-top:20px">今日无财报数据</p>
<p style="color:#5a6b85;font-size:12px;margin-top:16px">由 ibkr_show 自动推送 · 数据来源 Yahoo Finance</p>
</body>
</html>"""
            _send_email(
                smtp_server=settings.smtp_server,
                smtp_port=settings.smtp_port,
                smtp_username=settings.smtp_username,
                smtp_password=settings.smtp_password,
                sender_email=settings.sender_email,
                target_email=settings.target_email,
                subject=f"🌡️ [{today}] 美股情绪观察",
                html_body=body,
            )
            return TestSendResponse(success=True, message="今日无财报数据，已推送情绪观察")

        enriched = []
        for s in stocks:
            detail = _fetch_earnings_detail(s["symbol"])
            if detail and detail.get("date"):
                enriched.append({**s, **detail})

        enriched.sort(key=lambda x: (x.get("date", ""), -x.get("mcap", 0)))
        earnings_html = _build_html_table(enriched)
        body = f"""\
<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a1220;color:#e8edf5;padding:20px">
{sentiment_html}
{earnings_html}
</body>
</html>"""
        _send_email(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            sender_email=settings.sender_email,
            target_email=settings.target_email,
            subject=f"🌡️ [{today}] 美股情绪观察 & 财报日历 ({len(enriched)} 家公司)",
            html_body=body,
        )
        return TestSendResponse(success=True, message=f"推送成功，共 {len(enriched)} 家公司")
    except Exception as exc:
        logger.exception("Daily push failed")
        return TestSendResponse(success=False, message=str(exc))
