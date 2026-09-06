import os
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or default


def get_cors_origins() -> List[str]:
    raw = get_env("CORS_ORIGINS", "*") or "*"
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def get_settings() -> dict:
    return {
        "mongo_url": get_env("MONGO_URL"),
        "db_name": get_env("DB_NAME"),
        "cors_origins": get_cors_origins(),
        "github_token": get_env("GITHUB_TOKEN"),
        "github_username": get_env("GITHUB_USERNAME") or get_env("GITHUB_OWNER"),
        "github_api_base_url": get_env("GITHUB_API_BASE_URL", "https://api.github.com"),
        "github_webhook_secret": get_env("GITHUB_WEBHOOK_SECRET"),
        "github_app_id": get_env("GITHUB_APP_ID"),
        "github_client_id": get_env("GITHUB_CLIENT_ID"),
        "github_client_secret": get_env("GITHUB_CLIENT_SECRET"),
        "github_private_key": get_env("GITHUB_PRIVATE_KEY"),
        "ai_provider": get_env("AI_PROVIDER", "ollama"),
        "ollama_base_url": get_env("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model": get_env("OLLAMA_MODEL"),
        "cloud_ai_base_url": get_env("CLOUD_AI_BASE_URL"),
        "cloud_ai_api_key": get_env("CLOUD_AI_API_KEY"),
        "cloud_ai_model": get_env("CLOUD_AI_MODEL"),
        "elevenlabs_api_key": get_env("ELEVENLABS_API_KEY"),
        "elevenlabs_voice_id": get_env("ELEVENLABS_VOICE_ID"),
        "elevenlabs_model_id": get_env("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        "elevenlabs_output_format": get_env("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
        "tts_provider": get_env("TTS_PROVIDER", "elevenlabs"),
        "chatterbox_device": get_env("CHATTERBOX_DEVICE", "cpu"),
        "chatterbox_voice_path": get_env("CHATTERBOX_VOICE_PATH"),
        "admin_secret": get_env("ADMIN_SECRET"),
        "github_automation_trigger_secret": get_env("GITHUB_AUTOMATION_TRIGGER_SECRET"),
        "approval_secret": get_env("APPROVAL_SECRET") or get_env("ADMIN_SECRET"),
        "approval_token_ttl_hours": get_env("APPROVAL_TOKEN_TTL_HOURS", "48"),
        "frontend_base_url": get_env("FRONTEND_BASE_URL", "http://localhost:3000"),
        "email_provider": get_env("EMAIL_PROVIDER", "smtp"),
        "email_from": get_env("EMAIL_FROM"),
        "email_to": get_env("EMAIL_TO") or get_env("ADMIN_EMAIL"),
        "resend_api_key": get_env("RESEND_API_KEY"),
        "email_host": get_env("EMAIL_HOST"),
        "email_port": get_env("EMAIL_PORT", "587"),
        "email_username": get_env("EMAIL_USERNAME"),
        "email_password": get_env("EMAIL_PASSWORD"),
        "email_use_tls": get_env("EMAIL_USE_TLS", "true"),
        "analysis_ignore_max": get_env("ANALYSIS_IGNORE_MAX", "64"),
        "analysis_candidate_min": get_env("ANALYSIS_CANDIDATE_MIN", "85"),
        "technical_depth_weight": get_env("TECHNICAL_DEPTH_WEIGHT", "0.20"),
        "complexity_weight": get_env("COMPLEXITY_WEIGHT", "0.15"),
        "originality_weight": get_env("ORIGINALITY_WEIGHT", "0.15"),
        "impact_weight": get_env("IMPACT_WEIGHT", "0.15"),
        "engineering_quality_weight": get_env("ENGINEERING_QUALITY_WEIGHT", "0.15"),
        "maturity_weight": get_env("MATURITY_WEIGHT", "0.10"),
        "collaboration_weight": get_env("COLLABORATION_WEIGHT", "0.05"),
        "portfolio_fit_weight": get_env("PORTFOLIO_FIT_WEIGHT", "0.05"),
        "max_featured_projects": get_env("MAX_FEATURED_PROJECTS", "6"),
        "ranking_quality_weight": get_env("RANKING_QUALITY_WEIGHT", "0.35"),
        "ranking_fit_weight": get_env("RANKING_FIT_WEIGHT", "0.15"),
        "ranking_depth_weight": get_env("RANKING_DEPTH_WEIGHT", "0.12"),
        "ranking_originality_weight": get_env("RANKING_ORIGINALITY_WEIGHT", "0.10"),
        "ranking_impact_weight": get_env("RANKING_IMPACT_WEIGHT", "0.08"),
        "ranking_maturity_weight": get_env("RANKING_MATURITY_WEIGHT", "0.07"),
        "ranking_differentiation_weight": get_env("RANKING_DIFFERENTIATION_WEIGHT", "0.08"),
        "ranking_diversity_weight": get_env("RANKING_DIVERSITY_WEIGHT", "0.05"),
        "similarity_threshold": get_env("SIMILARITY_THRESHOLD", "65"),
        "similarity_penalty": get_env("SIMILARITY_PENALTY", "18"),
        "github_automation_enabled": get_env("GITHUB_AUTOMATION_ENABLED", "false"),
    }


def get_scoring_weights() -> dict:
    settings = get_settings()
    return {
        "technical_depth": float(settings.get("technical_depth_weight") or 0.20),
        "complexity": float(settings.get("complexity_weight") or 0.15),
        "originality": float(settings.get("originality_weight") or 0.15),
        "impact": float(settings.get("impact_weight") or 0.15),
        "engineering_quality": float(settings.get("engineering_quality_weight") or 0.15),
        "maturity": float(settings.get("maturity_weight") or 0.10),
        "collaboration": float(settings.get("collaboration_weight") or 0.05),
        "portfolio_fit": float(settings.get("portfolio_fit_weight") or 0.05),
    }


def get_analysis_thresholds() -> dict:
    settings = get_settings()
    return {
        "ignore_max": int(float(settings.get("analysis_ignore_max") or 64)),
        "candidate_min": int(float(settings.get("analysis_candidate_min") or 85)),
    }


def get_approval_token_ttl_seconds() -> int:
    settings = get_settings()
    return max(300, int(float(settings.get("approval_token_ttl_hours") or 48) * 3600))


def get_ranking_config() -> dict:
    settings = get_settings()
    return {
        "max_featured_projects": max(1, int(float(settings.get("max_featured_projects") or 6))),
        "similarity_threshold": max(0, min(100, int(float(settings.get("similarity_threshold") or 65)))),
        "similarity_penalty": max(0, min(100, int(float(settings.get("similarity_penalty") or 18)))),
        "weights": {
            "quality": float(settings.get("ranking_quality_weight") or 0.35),
            "fit": float(settings.get("ranking_fit_weight") or 0.15),
            "depth": float(settings.get("ranking_depth_weight") or 0.12),
            "originality": float(settings.get("ranking_originality_weight") or 0.10),
            "impact": float(settings.get("ranking_impact_weight") or 0.08),
            "maturity": float(settings.get("ranking_maturity_weight") or 0.07),
            "differentiation": float(settings.get("ranking_differentiation_weight") or 0.08),
            "diversity": float(settings.get("ranking_diversity_weight") or 0.05),
        },
    }
