import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
import requests
import json
import os

# Settings
API_TOKEN = '...your token...'
OLLAMA_API_URL = "http://192.168.3.224:11434/api/generate"
OLLAMA_MODEL = 'qwen2.5-coder:32b'

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_directory = './logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_handler = RotatingFileHandler(os.path.join(log_directory, 'bot.log'), maxBytes=10 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

bot = Bot(token=API_TOKEN)

dp = Dispatcher()


def parse_response(response: str) -> str:
    try:
        response_data = json.loads(response)

        for key in ['solution', 'description', 'message', 'greeting', 'response', 'text', 'thoughts', 'name', 'joke',
                    'answer', 'anekdot', 'advice']:
            if key in response_data:
                return response_data[key]

        return response

    except json.JSONDecodeError:
        return response


async def get_ollama_response(prompt: str) -> str:
    try:
        data = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        logger.debug(f"Sending request to Ollama API: {data}")

        response = requests.post(OLLAMA_API_URL, json=data)

        if response.status_code == 200:
            result = response.json()

            logger.debug(f"Response from Ollama API: {json.dumps(result, indent=4)}")

            if "response" in result:
                return parse_response(result["response"])

            return "Response from the model not found."

        else:
            return f"Error: {response.status_code}, {response.text}"

    except Exception as e:
        logger.error(f"Error while making request to Ollama API: {str(e)}")
        return f"Error while making request to Ollama API: {str(e)}"


@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Hello! I am the AI bot for our local LLM model. Write to me, and I will assist you.")


@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    prompt = message.text

    response = await get_ollama_response(prompt)

    await message.answer(response)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
