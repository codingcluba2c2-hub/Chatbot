import asyncio
from pipeline.pipeline_context import PipelineContext
from api.routes.chat import pipeline_runner
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing pipeline...")
    ctx = PipelineContext(
        original_message="How many earned leaves?",
        session_id="test",
        conversation_id="test"
    )
    result = pipeline_runner.process(ctx)
    print(result)

if __name__ == "__main__":
    asyncio.run(test())
