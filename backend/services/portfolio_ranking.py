from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from backend.config import get_ranking_config

DOMAIN_KEYWORDS = {
    "AI / ML": {"ai", "ml", "machine-learning", "deep-learning", "llm", "nlp", "chatbot", "vision"},
    "Web Development": {"web", "frontend", "react", "nextjs", "html", "css", "javascript"},
    "Mobile": {"mobile", "android", "ios", "flutter", "swift", "kotlin", "react-native"},
    "Backend": {"backend", "api", "fastapi", "django", "flask", "node", "express", "rest"},
    "Systems": {"systems", "distributed", "operating-system", "compiler", "embedded", "networking"},
    "Security": {"security", "cybersecurity", "auth", "encryption", "vulnerability"},
    "Data": {"data", "analytics", "database", "sql", "etl", "visualization"},
    "Automation": {"automation", "workflow", "bot", "scraping", "integration", "webhook"},
    "Developer Tools": {"developer-tools", "cli", "developer", "testing", "linting", "devtools"},
}
SCORE_KEYS = ("technical_depth", "complexity", "originality", "impact", "engineering_quality", "maturity", "collaboration", "portfolio_fit")


class PortfolioRankingService:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or get_ranking_config()
        self.weights = self.config["weights"]

    def rank_portfolio(self, projects: Sequence[Dict[str, Any]], candidates: Sequence[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        eligible = [project for project in projects if self._is_eligible(project)]
        candidate_by_repo = {str(item.get("github_repo_id")): item for item in (candidates or [])}
        enriched = []
        for project in eligible:
            candidate = candidate_by_repo.get(str(project.get("github_repo_id")), {})
            domains = self.detect_domains(project, candidate)
            scores = self._scores(project, candidate)
            enriched.append({"project": project, "candidate": candidate, "domains": domains, "scores": scores})

        domain_counts = Counter(domain for item in enriched for domain in item["domains"])
        base_ranked = []
        for item in enriched:
            diversity_score = self._diversity_score(item["domains"], domain_counts)
            base_score = self._base_score(item["scores"])
            item.update({"similarity_score": 0.0, "similarity_penalty": 0.0, "diversity_score": diversity_score, "base_score": base_score})
            base_ranked.append(item)
        base_ranked.sort(key=lambda item: (-item["base_score"], str(item["project"].get("github_repo_id", ""))))

        ranked = []
        selected = []
        for item in base_ranked:
            similarity = self.similarity_with_portfolio(item["project"], [entry["project"] for entry in selected])
            similar_count = sum(1 for entry in selected if self._similarity(item["project"], entry["project"]) >= self.config["similarity_threshold"])
            penalty = self._similarity_penalty(similarity, similar_count)
            ranking_score = self._clamp(item["base_score"] + item["diversity_score"] * self.weights["diversity"] - penalty)
            item.update({"similarity_score": similarity, "similarity_penalty": penalty, "ranking_score": ranking_score})
            ranked.append(item)
            selected.append(item)

        ranked.sort(key=lambda item: (-item["ranking_score"], str(item["project"].get("github_repo_id", ""))))
        recommended_featured_limit = self.config["max_featured_projects"]
        recommendations = []
        for index, item in enumerate(ranked, start=1):
            project = item["project"]
            manual_rank = project.get("manual_rank")
            manual_featured = bool(project.get("manual_featured") or project.get("featured") and project.get("manually_featured"))
            recommended_rank = int(manual_rank) if manual_rank is not None else index
            recommended_featured = manual_featured or index <= recommended_featured_limit
            explanation = self._explanation(item, index, domain_counts)
            recommendations.append({
                "github_repo_id": project.get("github_repo_id"),
                "title": project.get("title"),
                "rank": index,
                "current_position": project.get("display_order"),
                "recommended_rank": recommended_rank,
                "ranking_score": item["ranking_score"],
                "recommended_featured": recommended_featured,
                "featured": bool(project.get("featured", False)),
                "manual_rank": manual_rank,
                "manual_featured": manual_featured,
                "domains": item["domains"],
                "diversity_score": item["diversity_score"],
                "similarity_score": item["similarity_score"],
                "similarity_penalty": item["similarity_penalty"],
                "explanation": explanation,
            })

        return {
            "ranked_projects": recommendations,
            "max_featured_projects": recommended_featured_limit,
            "eligible_project_count": len(eligible),
            "excluded_project_count": len(projects) - len(eligible),
        }

    def portfolio_health(self, projects: Sequence[Dict[str, Any]], candidates: Sequence[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        ranking = self.rank_portfolio(projects, candidates)
        items = ranking["ranked_projects"]
        if not items:
            return {"health_score": 0, "breadth_score": 0, "depth_score": 0, "diversity_score": 0, "redundancy_score": 100, "recommendations": ["Publish or approve projects to build a portfolio signal."], "domain_counts": {}}
        domains = Counter(domain for item in items for domain in item["domains"])
        breadth = self._clamp(len(domains) / min(6, max(1, len(items))) * 100)
        depth = self._average(item["ranking_score"] for item in items)
        diversity = self._clamp(sum(item["diversity_score"] for item in items) / len(items))
        redundancy = self._clamp(100 - self._average(item["similarity_penalty"] for item in items))
        quality = self._average(item["ranking_score"] for item in items)
        health = self._clamp(quality * 0.35 + breadth * 0.20 + depth * 0.20 + diversity * 0.15 + redundancy * 0.10)
        gaps = self.detect_gaps(domains, items)
        return {"health_score": health, "breadth_score": breadth, "depth_score": depth, "diversity_score": diversity, "redundancy_score": redundancy, "recommendations": gaps, "domain_counts": dict(domains)}

    @staticmethod
    def detect_domains(project: Dict[str, Any], candidate: Dict[str, Any] | None = None) -> List[str]:
        candidate = candidate or {}
        tokens = PortfolioRankingService._tokens([project.get("category"), project.get("title"), project.get("description"), project.get("topics"), project.get("technologies"), project.get("languages"), candidate.get("analysis"), candidate.get("topics")])
        matches = [domain for domain, keywords in DOMAIN_KEYWORDS.items() if tokens.intersection(keywords)]
        return matches or ["Other"]

    def similarity_with_portfolio(self, project: Dict[str, Any], others: Sequence[Dict[str, Any]]) -> float:
        if not others:
            return 0.0
        return max((self._similarity(project, other) for other in others), default=0.0)

    def _base_score(self, scores: Dict[str, float]) -> float:
        quality = self._average(scores[key] for key in SCORE_KEYS)
        return self._clamp(
            quality * self.weights["quality"]
            + scores["portfolio_fit"] * self.weights["fit"]
            + scores["technical_depth"] * self.weights["depth"]
            + scores["originality"] * self.weights["originality"]
            + scores["impact"] * self.weights["impact"]
            + scores["maturity"] * self.weights["maturity"]
            + scores["differentiation"] * self.weights["differentiation"]
        )

    @staticmethod
    def _diversity_score(domains: Sequence[str], domain_counts: Counter) -> float:
        if not domains:
            return 0.0
        rarity = sum(100.0 / max(1, domain_counts[domain]) for domain in domains) / len(domains)
        return round(min(100.0, rarity), 2)

    def _scores(self, project: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, float]:
        source = candidate.get("scores") or (candidate.get("analysis") or {}).get("scores") or (project.get("analysis") or {}).get("scores") or {}
        overall = project.get("overall_score") or candidate.get("overall_score") or (project.get("analysis") or {}).get("overall_score") or 0
        return {"technical_depth": self._number(source.get("technical_depth")), "complexity": self._number(source.get("complexity")), "originality": self._number(source.get("originality")), "impact": self._number(source.get("impact")), "engineering_quality": self._number(source.get("engineering_quality")), "maturity": self._number(source.get("maturity")), "collaboration": self._number(source.get("collaboration")), "portfolio_fit": self._number(source.get("portfolio_fit") or candidate.get("portfolio_fit_score")), "differentiation": self._number(candidate.get("differentiation_score") or source.get("originality") or overall)}

    def _explanation(self, item: Dict[str, Any], rank: int, domain_counts: Counter) -> str:
        domains = ", ".join(item["domains"])
        similar = "Similar projects exist, so diminishing returns were applied." if item["similarity_penalty"] else "No strong similarity penalty was detected."
        gap = "It broadens domain coverage." if any(domain_counts[domain] == 1 for domain in item["domains"]) else "It reinforces an existing domain with strong quality evidence."
        return f"Ranks #{rank} because it combines a calculated score of {item['ranking_score']:.1f} with {domains} representation. {gap} {similar}"

    def detect_gaps(self, domain_counts: Counter, items: Sequence[Dict[str, Any]]) -> List[str]:
        recommendations = []
        if not domain_counts.get("Mobile"):
            recommendations.append("No mobile project is represented.")
        if not domain_counts.get("Systems"):
            recommendations.append("No systems project is represented.")
        if domain_counts.get("Web Development", 0) >= 3:
            recommendations.append("The portfolio has a high concentration of web development projects.")
        elif domain_counts.get("Web Development", 0) >= 2:
            recommendations.append("The portfolio has multiple web development projects and may benefit from broader domain coverage.")
        if domain_counts.get("AI / ML") and sum(count for domain, count in domain_counts.items() if domain != "AI / ML") == 0:
            recommendations.append("AI representation is strong but non-AI representation is limited.")
        if self._average(item.get("scores", {}).get("collaboration", 0) for item in items) < 50:
            recommendations.append("There is little evidence of collaboration across the selected projects.")
        return recommendations

    def _similarity_penalty(self, similarity: float, previous_similar_count: int) -> float:
        if similarity < self.config["similarity_threshold"]:
            return 0.0
        return min(60.0, self.config["similarity_penalty"] * (previous_similar_count + 1) * (similarity / 100))

    @staticmethod
    def _similarity(left: Dict[str, Any], right: Dict[str, Any]) -> float:
        left_tokens = PortfolioRankingService._tokens([left.get("topics"), left.get("technologies"), left.get("languages"), left.get("category"), left.get("description")])
        right_tokens = PortfolioRankingService._tokens([right.get("topics"), right.get("technologies"), right.get("languages"), right.get("category"), right.get("description")])
        union = left_tokens | right_tokens
        return 100.0 * len(left_tokens & right_tokens) / len(union) if union else 0.0

    @staticmethod
    def _tokens(values: Iterable[Any]) -> Set[str]:
        tokens: Set[str] = set()
        for value in values:
            if isinstance(value, dict):
                values_to_read = value.keys()
            elif isinstance(value, (list, tuple, set)):
                values_to_read = value
            else:
                values_to_read = [value]
            for item in values_to_read:
                tokens.update(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(item).lower()))
        return tokens

    @staticmethod
    def _is_eligible(project: Dict[str, Any]) -> bool:
        status = str(project.get("status") or project.get("candidate_status") or "PUBLISHED").upper()
        return status in {"APPROVED", "PUBLISHED"}

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return max(0.0, min(100.0, float(value or 0)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _average(values: Iterable[float]) -> float:
        values = list(values)
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _clamp(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 2)
