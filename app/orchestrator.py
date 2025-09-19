from __future__ import annotations
import asyncio
import logging
from typing import Dict, List

from models.types import InputEvent, ModelResponse, ResponsePacket

from .adapters.base import BaseAdapter, AdapterError
from .adapters.gpt import GPTAdapter
from .adapters.deepseek import DeepSeekAdapter
from .adapters.gemini import GeminiAdapter
from .adapters.copilot import CopilotAdapter
from .pipelines.dialectic_engine import DialecticEngine
from .pipelines.internal_monologue import InternalMonologue
from .pipelines.bias_detector import BiasDetector
from .pipelines.conflict_analyzer import ConflictAnalyzer
from .pipelines.response_synthesizer import ResponseSynthesizer
from .memory import MemoryStore
from .config import get_settings

logger = logging.getLogger("smartcore.orchestrator")


ADAPTER_REGISTRY: Dict[str, BaseAdapter] = {
    "gpt": GPTAdapter(),
    "deepseek": DeepSeekAdapter(),
    "gemini": GeminiAdapter(),
    "copilot": CopilotAdapter(),
}


class Orchestrator:
    """Coordinates the multi-model cognitive workflow."""

    def __init__(self, memory: MemoryStore):
        self.settings = get_settings()
        self.memory = memory
        self.dialectic = DialecticEngine()
        self.monologue = InternalMonologue(depth=2)
        self.bias_detector = BiasDetector()
        self.conflict_analyzer = ConflictAnalyzer()
        self.synthesizer = ResponseSynthesizer()

    async def handle(self, event: InputEvent, context: dict | None = None) -> ResponsePacket:
        prompt = event.value
        model_responses = await self._gather_model_responses(prompt)
        internal_reflections = self.monologue.reflect(prompt, model_responses)
        full_responses = model_responses + internal_reflections

        dialectic = self.dialectic.analyze(full_responses)
        bias_report = self.bias_detector.evaluate(full_responses)
        conflict_report = self.conflict_analyzer.analyze(full_responses)

        intent = self._infer_intent(event, dialectic, conflict_report)
        packet = self.synthesizer.synthesize(
            prompt=prompt,
            intent=intent,
            responses=full_responses,
            dialectic=dialectic,
            bias=bias_report,
            conflict=conflict_report,
            context=context,
        )
        self.memory.append_observation(event, full_responses)
        return packet

    async def _gather_model_responses(self, prompt: str) -> List[ModelResponse]:
        tasks = []
        context = {"prompt": prompt}
        for name in self.settings.active_models:
            adapter = ADAPTER_REGISTRY.get(name)
            if not adapter:
                continue
            tasks.append(self._call_adapter(adapter, prompt, context))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        responses: List[ModelResponse] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("adapter_error", exc_info=result)
                continue
            responses.append(ModelResponse.model_validate(result))
        return responses

    async def _call_adapter(self, adapter: BaseAdapter, prompt: str, context: Dict[str, str]) -> Dict[str, str]:
        payload = await adapter.ask(prompt, context)
        payload.setdefault("model", adapter.name)
        return payload

    @staticmethod
    def _infer_intent(event: InputEvent, dialectic, conflict) -> str:
        if event.type == "audio":
            return "report_sound"
        if conflict.severity > 0.5:
            return "highlight_conflict"
        if dialectic.contradictions:
            return "mediate_contradiction"
        return "inform"
