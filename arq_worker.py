# RUN THIS FILE WITH `watchmedo auto-restart --patterns='*.py' --recursive -- arq arq_worker.WorkerSettings`

import os
from arq.connections import RedisSettings
from openai import AsyncOpenAI
from models import Item, Collection
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

REDIS_SETTINGS = RedisSettings()


# TODO: create a job that will process the transcript
# - use OpenAI function calling/structured outputs to extract a structured output
async def process_transcript(ctx, info):
    logger.debug(f"DEBUG: {info}")
    prompt = """
    system_prompt

    user_context

    examples
    {medication 1: name, }


    """
    return
    # return llm_structured
    # return info[1]


class WorkerSettings:
    functions = [process_transcript]
    redis_settings = REDIS_SETTINGS