import asyncio
from datetime import datetime, timedelta
import json
import logging
from misho_bot import open_ai_tools
from misho_client import Authorization
from misho_client.job_client import JobClient
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletion

from misho_api.job import JobCreateApi


class OpenAiUserClient:
    def __init__(
        self,
        open_ai_client: OpenAI,
        job_client: JobClient,
        authorization: Authorization
    ):
        self._last_message_timestamp = None
        self._messages = [self._system_message()]
        self._open_ai_client = open_ai_client
        self._job_client = job_client
        self._authorization = authorization
        self._clear_context_after_seconds = 60 * 10  # 10 minutes
        self._lock = asyncio.Lock()
        self._context_cleanup_task_started = False

    async def handle_user_message(self, user_message: str) -> str | None:
        if not self._context_cleanup_task_started:
            asyncio.create_task(self._start_context_cleanup_loop())
            self._context_cleanup_task_started = True

        async with self._lock:
            self._messages.append({"role": "user", "content": user_message})
            response = self._ask_openai()
            self._last_message_timestamp = datetime.now()
            return self._handle_open_ai_response(response)

    def _ask_openai(self):
        return self._open_ai_client.chat.completions.create(
            model="gpt-4o",
            messages=self._messages,
            tools=open_ai_tools.get_tools(),
            tool_choice="auto"
        )

    def _handle_open_ai_response(self, response: ChatCompletion) -> str | None:
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            return choice.message.content

        elif choice.finish_reason == "tool_calls":
            tool_calls = choice.message.tool_calls

            for tool_call in tool_calls:
                self._handle_tool_call(tool_call)

            response = self._ask_openai()
            return self._handle_open_ai_response(response)

    def _handle_tool_call(self, tool_call: ChatCompletionMessageToolCall):
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Function call: {func_name} with arguments: {args}")

        if func_name == "create_job":
            result = self._job_client.create_job(
                authorization=self._authorization,
                job_create=JobCreateApi(**args)
            )
            self._tool_call_append(tool_call, result)

        elif func_name == "list_jobs":
            result = self._job_client.list_jobs(
                authorization=self._authorization
            )
            self._tool_call_append(tool_call, result)

        elif func_name == "delete_job":
            result = self._job_client.delete_job(
                authorization=self._authorization,
                job_id=args['job_id']
            )
            self._tool_call_append(tool_call, result)

    def _tool_call_append(self, tool_call: ChatCompletionMessageToolCall, result: any):
        self._messages.append({
            "role": "assistant",
            "tool_calls": [tool_call]  # Required to include tool call
        })

        self._messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            }
        )

    async def _start_context_cleanup_loop(self):
        while True:
            await asyncio.sleep(30)
            async with self._lock:
                if (
                    self._last_message_timestamp and
                    datetime.now() - self._last_message_timestamp > timedelta(seconds=self._clear_context_after_seconds)
                ):
                    self._clear_context()

    def _clear_context(self):
        logging.info("Clearing context due to inactivity.")
        self._messages = [self._system_message()]
        self._last_message_timestamp = None

    def _system_message(self):
        return {
            "role": "system",
            "content": f"""
                You are a helpful assistant. Today is {datetime.today()}.
                When the user says 'tomorrow', use day after today. 
                If start hour is less than 17, to_hour is from_hour + 1, otherwise to_hour is from_hour + 2.
                Prefer Croatian language.
                """
        }
