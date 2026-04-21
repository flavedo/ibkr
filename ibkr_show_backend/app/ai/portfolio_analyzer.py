from app.ai.llm_client import LLMClient
from app.ai.prompt_builder import build_portfolio_prompt


class PortfolioAnalyzer:
    """Placeholder analyzer reserved for future AI-driven insights."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def analyze(self, summary: str) -> str:
        prompt = build_portfolio_prompt(summary)
        return self.llm_client.generate(prompt)
