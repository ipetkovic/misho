
from datetime import datetime
import json
import logging
from typing import Awaitable, TypeVar, Union
from misho_server.domain.job import JobCreate
from misho_server.domain.reservation_calendar import ReservationCalendar
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.domain.time_slot import TimeSlot
from misho_server.domain.user import UserId
from misho_server.service.jobs_service import JobsService
from misho_server.service.reservation_calendar import ReservationCalendarService
from misho_server.service.reservation_cancel_service import ReservationCancelService
from misho_server.service.reservation_service import ReservationService
from openai.types.chat import ChatCompletionMessageToolCall

T = TypeVar("T")


class OpenAiToolHandler:
    def __init__(
        self,
        jobs_service: JobsService,
        reservation_service: ReservationService,
        reservation_cancel_service: ReservationCancelService,
        reservation_calendar_service: ReservationCalendarService,
    ):
        self._jobs_service = jobs_service
        self._reservation_calendar_service = reservation_calendar_service
        self._reservation_service = reservation_service
        self._reservation_cancel_service = reservation_cancel_service

    async def handle_tool_call(self, user_id: UserId, tool_call: ChatCompletionMessageToolCall) -> str:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"Function call: {func_name} with arguments: {args}")

        async def call(coroutine: Awaitable[T], *, context: str = "unknown") -> Union[T, str]:
            try:
                return await coroutine
            except Exception as e:
                logging.error(f"[{context}] Exception: {e}")
                return str(e)

        if func_name == "create_job":
            logging.info(f"Creating job with args: {args}")
            args['user_id'] = user_id
            result = await call(
                self._jobs_service.create_job(
                    job_create=JobCreate(**args)
                )
            )
            return str(result)

        elif func_name == "list_jobs":
            logging.info(f"List job called.")
            result = await call(self._jobs_service.list_jobs(user_id=user_id))
            return str(result)

        elif func_name == "delete_job":
            result = await call(self._jobs_service.delete_job(
                job_id=args['job_id'],
                user_id=user_id
            ))
            return str(result)

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
                    user_id=user_id,
                    reservation_slot=reservation_slot
                ))
            if result is None:
                result = "Reservation successful."

            return str(result)

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
                    user_id=user_id,
                    reservation_slot=reservation_slot
                ))
            if result is None:
                result = "Reservation cancellation successful."

            return str(result)

        elif func_name == "get_reservations":
            logging.info(f"Get reservations called with args: {args}.")
            # Assuming reservation_calendar is a method in JobsService
            dates = args.get('dates', None)
            dates = [datetime.strptime(date, "%Y-%m-%d").date()
                     for date in dates] if dates else None
            only_for_user = args.get('only_for_user', False)

            user_id_filter = None
            if only_for_user:
                user_id_filter = user_id

            result = await call(self._reservation_calendar_service.get_calendar(user_id=user_id_filter, filter_by_days=dates))

            if isinstance(result, ReservationCalendar):
                result = result.calendar
                result = {(str(
                    reservation_slot.time_slot), reservation_slot.court): reservation.reserved_by for reservation_slot, reservation in result.items()}

            return str(result)

        raise ValueError(f"Unknown function call: {func_name}")
