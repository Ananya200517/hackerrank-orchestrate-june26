from __future__ import annotations

from dataclasses import dataclass, field

from anthropic import Anthropic
from openai import OpenAI

from pipeline.image_utils import encode_image_base64
from pipeline.models import ClaimContext, ImageReference
from pipeline.perception import build_perception_system_prompt, build_perception_user_prompt
from pipeline.prompts import build_system_prompt, build_user_prompt
from pipeline.settings import Settings


@dataclass
class VLMUsageStats:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    images_processed: int = 0
    errors: int = 0


@dataclass
class VLMClient:
    settings: Settings
    provider: str
    usage: VLMUsageStats = field(default_factory=VLMUsageStats)

    def __post_init__(self) -> None:
        self.provider = self.provider.strip().lower()
        api_key = self.settings.api_key_for_provider(self.provider)
        self.model = self.settings.model_for_provider(self.provider)

        if self.provider == "openai":
            self._openai = OpenAI(
                api_key=api_key,
                timeout=self.settings.request_timeout_seconds,
                max_retries=0,
            )
        else:
            self._anthropic = Anthropic(
                api_key=api_key,
                timeout=self.settings.request_timeout_seconds,
                max_retries=0,
            )

    def analyze_claim(self, context: ClaimContext) -> str:
        system_prompt = build_system_prompt(context)
        user_prompt = build_user_prompt(context)

        if self.provider == "openai":
            return self._analyze_openai(system_prompt, user_prompt, context.claim.images)
        return self._analyze_anthropic(system_prompt, user_prompt, context.claim.images)

    def analyze_perception(self, context: ClaimContext) -> str:
        system_prompt = build_perception_system_prompt(context)
        user_prompt = build_perception_user_prompt(context)

        if self.provider == "openai":
            return self._analyze_openai(system_prompt, user_prompt, context.claim.images)
        return self._analyze_anthropic(system_prompt, user_prompt, context.claim.images)

    def _analyze_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        images: tuple[ImageReference, ...],
    ) -> str:
        content: list[dict] = [{"type": "text", "text": user_prompt}]
        for image in images:
            mime_type, encoded = encode_image_base64(image.absolute_path)
            content.append({"type": "text", "text": f"Image ID: {image.image_id}"})
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                }
            )
            self.usage.images_processed += 1

        response = self._openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1500,
        )
        self.usage.requests += 1
        if response.usage is not None:
            self.usage.input_tokens += response.usage.prompt_tokens or 0
            self.usage.output_tokens += response.usage.completion_tokens or 0

        message = response.choices[0].message.content
        if not message:
            raise RuntimeError("OpenAI returned an empty response.")
        return message

    def _analyze_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        images: tuple[ImageReference, ...],
    ) -> str:
        content: list[dict] = [{"type": "text", "text": user_prompt}]
        for image in images:
            mime_type, encoded = encode_image_base64(image.absolute_path)
            content.append({"type": "text", "text": f"Image ID: {image.image_id}"})
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": encoded,
                    },
                }
            )
            self.usage.images_processed += 1

        response = self._anthropic.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
            temperature=0,
            max_tokens=1500,
        )
        self.usage.requests += 1
        self.usage.input_tokens += response.usage.input_tokens
        self.usage.output_tokens += response.usage.output_tokens

        text_blocks = [block.text for block in response.content if block.type == "text"]
        if not text_blocks:
            raise RuntimeError("Anthropic returned an empty response.")
        return "\n".join(text_blocks)
