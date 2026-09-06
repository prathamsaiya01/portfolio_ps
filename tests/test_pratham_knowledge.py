import asyncio
from unittest.mock import AsyncMock

import pytest

from backend.services.ai_provider import OllamaChatProvider
from backend.services.pratham_knowledge import FALLBACK_RESPONSE, get_trusted_context, select_categories


@pytest.mark.parametrize(("question", "category", "expected"), [
    ("What is Pratham's name?", "identity", "Pratham Saiya"),
    ("When was Pratham born?", "identity", "5 August 2008"),
    ("What does Pratham study?", "education", "Computer Engineering"),
    ("What did Pratham score in Semester 4?", "education", "94.11%"),
    ("What programming languages does Pratham know?", "technical_skills", "Python"),
    ("What is CareerMitra?", "projects", "decision-based roadmap"),
    ("What is NOVA?", "projects", "Smart Mirror"),
    ("Where did Pratham intern?", "internships", "CNK"),
    ("What was Pratham's role at Spectrum 4.0?", "leadership", "Technical Head"),
    ("Which hackathons has Pratham participated in?", "hackathons", "LoanWise"),
    ("What are Pratham's hobbies?", "hobbies", "Playing cricket"),
    ("Does Pratham's portfolio use automation?", "automation", "automation"),
])
def test_profile_retrieves_verified_context(question, category, expected):
    context = get_trusted_context(question)
    assert context is not None
    assert category in context
    assert expected.lower() in str(context[category]).lower()


def test_multi_category_question_retrieves_only_relevant_categories():
    categories = select_categories("Tell me about Pratham's technical skills and leadership experience.")
    assert "technical_skills" in categories
    assert "leadership" in categories


def test_age_question_retrieves_dob_without_hardcoding_an_age():
    context = get_trusted_context("How old is Pratham?")
    assert context == {"identity": context["identity"]}
    assert context["identity"]["date_of_birth"] == "5 August 2008"


@pytest.mark.parametrize(("follow_up", "prior_question", "category"), [
    ("Why did he make it?", "What is NOVA?", "projects"),
    ("What hardware does it use?", "What is NOVA?", "projects"),
    ("Is it completed?", "What is NOVA?", "projects"),
    ("Which one lasted longer?", "What are Pratham's internships?", "internships"),
])
def test_follow_up_uses_recent_verified_conversation_context(follow_up, prior_question, category):
    context = get_trusted_context(follow_up, [prior_question])
    assert context is not None
    assert category in context


@pytest.mark.parametrize("question", [
    "What is Pratham's favourite movie?",
    "What is Pratham's favourite food?",
    "What is Pratham's salary?",
])
def test_unsupported_information_has_no_context(question):
    assert get_trusted_context(question) is None


def test_unknown_question_returns_centralized_fallback_without_calling_llm():
    service = type("Service", (), {"generate_chat_response": AsyncMock()})()
    provider = OllamaChatProvider(service=service)
    assert asyncio.run(provider.chat("What is Pratham's favourite movie?")) == FALLBACK_RESPONSE
    service.generate_chat_response.assert_not_awaited()
