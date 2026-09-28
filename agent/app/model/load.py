"""Model loader for AgentCore Runtime."""

import os
from strands.models import BedrockModel


def load_model():
    """Load Bedrock model for the agent."""
    model_id = os.environ.get(
        "MODEL_ID",
        "arn:aws:bedrock:ap-northeast-1:334107163417:inference-profile/apac.amazon.nova-pro-v1:0"
    )
    return BedrockModel(model_id=model_id)
