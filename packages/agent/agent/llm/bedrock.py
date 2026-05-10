import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Prices per 1k tokens (in USD) - approximate for Claude 3.5 series
# Need to update when Sonnet 3.5 v2 hits bedrock, these are typical ranges
PRICING = {
    "us-east-1": {
        "primary": {"in": 0.003, "out": 0.015},  # Claude 3.5 Sonnet
        "cheap": {"in": 0.00025, "out": 0.00125} # Claude 3.5 Haiku
    }
}

class LLMUsage:
    def __init__(self, model_id: str, input_tokens: int, output_tokens: int):
        self.model_id = model_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = self._calculate_cost()

    def _calculate_cost(self) -> float:
        # We assume us-east-1 for pricing in PoC
        region = "us-east-1"
        model_class = "primary" if "sonnet" in self.model_id.lower() else "cheap"
        rates = PRICING[region][model_class]

        cost = (self.input_tokens / 1000.0) * rates["in"] + (self.output_tokens / 1000.0) * rates["out"]
        return cost

class BedrockClient:
    def __init__(self):
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        # Retry config for ThrottlingException
        self.boto_config = Config(
            region_name=self.region,
            read_timeout=300, # Increased timeout for long-running LLM streams
            retries={"max_attempts": 0} # We handle retries via tenacity
        )
        
        profile_name = os.environ.get("AWS_PROFILE")
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        self.client = session.client("bedrock-runtime", config=self.boto_config)

        self.primary_model_id = os.environ.get("BEDROCK_PRIMARY_MODEL", "us.anthropic.claude-sonnet-4-6")
        self.cheap_model_id = os.environ.get("BEDROCK_CHEAP_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

    def _get_model_id(self, model: str) -> str:
        return self.primary_model_id if model == "primary" else self.cheap_model_id

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ClientError)
    )
    async def invoke_with_streaming(
        self,
        messages: list[dict[str, Any]],
        system: str,
        tools: list[dict[str, Any]],
        model: str = "primary"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Streams events: token, tool_use, tool_use_input_delta, message_stop, usage
        """
        model_id = self._get_model_id(model)

        kwargs: dict[str, Any] = {
            "modelId": model_id,
            "messages": messages,
            "system": [{"text": system}],
            "inferenceConfig": {"temperature": 0.0, "maxTokens": 4096}
        }

        if tools:
            kwargs["toolConfig"] = {"tools": tools}

        try:
            # We must run boto3 blocking calls in a thread pool
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.client.converse_stream(**kwargs))

            stream = response.get('stream')
            if not stream:
                return

            for event in stream:
                if 'messageStart' in event:
                    pass
                elif 'contentBlockDelta' in event:
                    delta = event['contentBlockDelta']['delta']
                    if 'text' in delta:
                        yield {"type": "token", "content": delta['text']}
                    elif 'toolUse' in delta:
                        yield {"type": "tool_use_input_delta", "delta": delta['toolUse']['input']}
                elif 'contentBlockStart' in event:
                    start = event['contentBlockStart']['start']
                    if 'toolUse' in start:
                        yield {
                            "type": "tool_use_start",
                            "toolUseId": start['toolUse']['toolUseId'],
                            "name": start['toolUse']['name']
                        }
                elif 'contentBlockStop' in event:
                    yield {"type": "content_block_stop"}
                elif 'messageStop' in event:
                    yield {
                        "type": "message_stop",
                        "stopReason": event['messageStop']['stopReason']
                    }
                elif 'metadata' in event:
                    usage = event['metadata']['usage']
                    metrics = LLMUsage(
                        model_id=model_id,
                        input_tokens=usage['inputTokens'],
                        output_tokens=usage['outputTokens']
                    )
                    yield {"type": "usage", "metrics": metrics}

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "ThrottlingException":
                logger.warning("Bedrock ThrottlingException. Retrying...")
                raise e # Trigger tenacity retry
            elif error_code == "ModelNotReadyException" and os.environ.get("BEDROCK_FALLBACK_TO_ANTHROPIC", "false").lower() == "true":
                logger.warning("Bedrock ModelNotReady, falling back to direct Anthropic API (not implemented yet)")
                # Fallback to direct anthropic SDK
                raise NotImplementedError("Anthropic fallback not fully implemented")
            else:
                logger.error(f"Bedrock invocation failed: {e}")
                raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(ClientError)
    )
    async def embed_text(self, text: str) -> list[float]:
        """
        Embeds a string using Titan Text Embeddings v2.
        """
        import json
        model_id = "amazon.titan-embed-text-v2:0"
        
        kwargs = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({"inputText": text})
        }
        
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.client.invoke_model(**kwargs))
            
            response_body = json.loads(response.get('body').read())
            return response_body.get('embedding')
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "ThrottlingException":
                logger.warning("Bedrock ThrottlingException on embedding. Retrying...")
                raise e
            logger.error(f"Bedrock embedding failed: {e}")
            raise e
