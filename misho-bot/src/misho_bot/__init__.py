from datetime import datetime
import json
import logging
import openai
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

import os
from openai import OpenAI

from misho_api.job import JobCreateApi

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

response = client.responses.create(
    model="gpt-4o",
    instructions="You are a coding assistant that talks like a pirate.",
    input="How do I check if a Python object is an instance of a class?",
)

print(response.output_text)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

print(f"Telegram bot token: {_TOKEN}")

print(JobCreateApi.model_json_schema())

create_job_tool = {
    "type": "function",
    "function": {
        "name": "create_job",
        "description": "Create a job with a time slot, an action (RESERVE or NOTIFY), and a list of preferred court IDs in priority order.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_slot": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date",
                            "title": "Date"
                        },
                        "hour_slot": {
                            "type": "object",
                            "title": "HourSlotApi",
                            "properties": {
                                "from_hour": {
                                    "type": "integer",
                                    "title": "From Hour"
                                },
                                "to_hour": {
                                    "type": "integer",
                                    "title": "To Hour"
                                }
                            },
                            "required": ["from_hour", "to_hour"]
                        }
                    },
                    "required": ["date", "hour_slot"],
                    "title": "TimeSlotApi"
                },
                "action": {
                    "type": "string",
                    "enum": ["RESERVE", "NOTIFY"],
                    "title": "ActionApi"
                },
                "courts_by_priority": {
                    "type": "array",
                    "title": "Courts By Priority",
                    "items": {
                        "type": "integer"
                    },
                    "default": [4, 6, 5, 7]
                }
            },
            "required": ["time_slot", "action", "courts_by_priority"],
            "title": "JobCreateApi"
        }
    }
}

list_jobs_tool = {
    "type": "function",
    "function": {
        "name": "list_jobs",
        "description": (
            "Show a list of current jobs. Optionally filter by status. "
            "Possible status values: PENDING, FAILED, SUCCESS."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["PENDING", "FAILED", "SUCCESS"],
                    "description": "Optional status to filter jobs by."
                }
            },
            "required": [],
            "title": "ListJobsFilter"
        }
    }
}

delete_job_tool = {
    "type": "function",
    "function": {
        "name": "delete_job",
        "description": "Delete a job by its ID. Use this to remove an existing job.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "integer",
                    "description": "The unique identifier of the job to delete."
                }
            },
            "required": ["job_id"],
            "title": "DeleteJobRequest"
        }
    }
}

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Book a court. Prefer courts 1, 2. Use RESERVE."}
    ],
    tools=[create_job_tool, list_jobs_tool, delete_job_tool],
    tool_choice="auto"
)

message = response.choices[0].message

print(message)

if message.tool_calls:
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("hello")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


user_messages = []


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text

    print(update.effective_user.id)
    print(update.effective_user.username)

    if len(user_messages) == 0:
        user_message = {
            "role": "system",
            "content": f"""
                You are a helpful assistant. Today is {datetime.today()}.
                When the user says 'tomorrow', use day after today. 
                If start hour is less than 17, to_hour is from_hour + 1, otherwise to_hour is from_hour + 2.
                Prefer Croatian language.
                """
        }
        user_messages.append(user_message)

    user_messages.append({"role": "user", "content": message})

    print(user_messages)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=user_messages,
        tools=[create_job_tool, list_jobs_tool, delete_job_tool],
        tool_choice="auto"
    )

    open_ai_message = response.choices[0].message
    print(open_ai_message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=open_ai_message.content)


def main():
    application = ApplicationBuilder().token(_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)

    application.run_polling()
