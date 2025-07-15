import asyncio
from datetime import datetime, timedelta
import logging
from misho_server.core.user import UserId
from misho_server.infrastructure.open_ai import tools
from misho_server.infrastructure.open_ai.tool_handler import OpenAiToolHandler
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletion


class OpenAiUserClient:
    def __init__(
        self,
        open_ai_client: OpenAI,
        tool_handler: OpenAiToolHandler,
        user_id: UserId
    ):
        self._last_message_timestamp = None
        self._messages = [self._system_message()]
        self._open_ai_client = open_ai_client
        self._tool_handler = tool_handler
        self._user_id = user_id
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
            response = await self._handle_open_ai_response(response)
            return response

    def add_system_message_to_context(self, message: str):
        self._messages.append({
            "role": "system",
            "content": message
        })
        self._last_message_timestamp = datetime.now()

    def _ask_openai(self):
        return self._open_ai_client.chat.completions.create(
            model="gpt-4o",
            messages=self._messages,  # type: ignore
            tools=tools.get_tools(),
            tool_choice="auto"
        )

    async def _handle_open_ai_response(self, response: ChatCompletion) -> str | None:
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            self._content_append(choice.message.content)
            return choice.message.content

        elif choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_calls = choice.message.tool_calls

            for tool_call in tool_calls:
                await self._handle_tool_call(tool_call)

            response = self._ask_openai()
            open_ai_response = await self._handle_open_ai_response(response)
            return open_ai_response

    async def _handle_tool_call(self, tool_call: ChatCompletionMessageToolCall):
        result = await self._tool_handler.handle_tool_call(self._user_id, tool_call)
        self._tool_call_append(tool_call, result)

    def _content_append(self, content: str | None):
        if content is not None:
            self._messages.append({
                "role": "assistant",
                "content": content
            })

    def _tool_call_append(self, tool_call: ChatCompletionMessageToolCall, result: str):
        self._messages.append({
            "role": "assistant",
            "tool_calls": [tool_call]  # type: ignore
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
                Prefer Croatian language.
                When user asks for job reservation, keep in mind that job creation does not mean that reservation is made.
                It means that job is created and will be executed once the time slot is available.
                """
        }
