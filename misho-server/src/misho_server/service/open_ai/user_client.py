import asyncio
from datetime import datetime, timedelta
import json
import logging
from misho_server.domain.job import JobCreate
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.domain.time_slot import TimeSlot
from misho_server.domain.user import UserId
from misho_server.repository.reservation_calendar import ReservationCalendarRepository
from misho_server.service.jobs_service import JobsService
from misho_server.service.open_ai import tools
from misho_server.service.reservation_calendar import ReservationCalendarService
from misho_server.service.reservation_cancel_service import ReservationCancelService
from misho_server.service.reservation_service import ReservationService
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall, ChatCompletion


class OpenAiUserClient:
    def __init__(
        self,
        open_ai_client: OpenAI,
        jobs_service: JobsService,
        reservation_service: ReservationService,
        reservation_cancel_service: ReservationCancelService,
        reservation_calendar_service: ReservationCalendarService,
        user_id: UserId | None
    ):
        self._last_message_timestamp = None
        self._messages = [self._system_message()]
        self._open_ai_client = open_ai_client
        self._jobs_service = jobs_service
        self._reservation_calendar_service = reservation_calendar_service
        self._reservation_service = reservation_service
        self._reservation_cancel_service = reservation_cancel_service
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

    def _ask_openai(self):
        return self._open_ai_client.chat.completions.create(
            model="gpt-4o",
            messages=self._messages,
            tools=tools.get_tools(),
            tool_choice="auto"
        )

    async def _handle_open_ai_response(self, response: ChatCompletion) -> str | None:
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            return choice.message.content

        elif choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_calls = choice.message.tool_calls

            for tool_call in tool_calls:
                await self._handle_tool_call(tool_call)

            response = self._ask_openai()
            open_ai_response = await self._handle_open_ai_response(response)
            return open_ai_response

    async def _handle_tool_call(self, tool_call: ChatCompletionMessageToolCall):
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Function call: {func_name} with arguments: {args}")

        async def call(cr):
            try:
                result = await cr
                return result
            except Exception as e:
                logging.error(f"Error calling function {func_name}: {e}")
                return str(e)

        if func_name == "create_job":
            logging.info(f"Creating job with args: {args}")
            args['user_id'] = self._user_id
            result = await call(
                self._jobs_service.create_job(
                    job_create=JobCreate(**args)
                )
            )

            self._tool_call_append(tool_call, result)

        elif func_name == "list_jobs":
            logging.info(f"List job called.")
            result = await call(self._jobs_service.list_jobs(user_id=self._user_id))
            print(f"List jobs result: {result}")
            self._tool_call_append(tool_call, result)

        elif func_name == "delete_job":
            result = await call(self._jobs_service.delete_job(
                job_id=args['job_id'],
                user_id=self._user_id
            ))
            self._tool_call_append(tool_call, result)

        elif func_name == "reserve":
            logging.info(f"Reserve called with args: {args}")
            time_slot = TimeSlot(**args['time_slot'])
            court = int(args['court'])
            reservation_slot = ReservationSlot(
                time_slot=time_slot,
                court=court
            )
            result = await call(
                self._reservation_service.reserve(
                    user_id=self._user_id,
                    reservation_slot=reservation_slot
                ))
            if result is None:
                result = "Reservation successful."

            self._tool_call_append(tool_call, result)

        elif func_name == "cancel_reservation":
            logging.info(f"Reservation cancel called with args: {args}")
            time_slot = TimeSlot(**args['time_slot'])
            court = int(args['court'])
            reservation_slot = ReservationSlot(
                time_slot=time_slot,
                court=court
            )
            result = await call(
                self._reservation_cancel_service.cancel_reservation(
                    user_id=self._user_id,
                    reservation_slot=reservation_slot
                ))
            if result is None:
                result = "Reservation cancellation successful."

            self._tool_call_append(tool_call, result)

        elif func_name == "get_reservations":
            logging.info(f"Get reservations called with args: {args}.")
            # Assuming reservation_calendar is a method in JobsService
            dates = args.get('dates', None)
            dates = [datetime.strptime(date, "%Y-%m-%d").date()
                     for date in dates] if dates else None
            only_for_user = args.get('only_for_user', False)

            user_id_filter = None
            if only_for_user:
                user_id_filter = self._user_id

            print(
                f"Dates for reservation calendar: {dates}, user_id_filter: {user_id_filter}")

            result = await call(self._reservation_calendar_service.get_calendar(user_id=user_id_filter, filter_by_days=dates))
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
                When user asks for job reservation, keep in mind that job creation does not mean that reservation is made.
                It means that job is created and will be executed once the time slot is available.
                """
        }
