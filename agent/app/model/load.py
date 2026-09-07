"""Model loader for AgentCore Runtime."""

import os
from strands.models import BedrockModel


def load_model():
    """Load Bedrock model for the agent."""
    model_id = os.environ.get("MODEL_ID", "jp.anthropic.claude-sonnet-4-5-20250929-v1:0")
    return BedrockModel(model_id=model_id)
