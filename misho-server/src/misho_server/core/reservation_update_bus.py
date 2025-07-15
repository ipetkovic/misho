import asyncio
from typing import Awaitable, Callable
from misho_server.core.reservation_update_event import ReservationUpdateEvent

type ReservationUpdateSubscriber = Callable[[
    ReservationUpdateEvent], Awaitable[None]]


class ReservationUpdateBus:
    def __init__(self):
        self._subscribers: list[ReservationUpdateSubscriber] = []

    async def publish(self, event: ReservationUpdateEvent):
        await self._notify(event)

    def subscribe(self, subscriber: ReservationUpdateSubscriber):
        self._subscribers.append(subscriber)

    async def _notify(self, event: ReservationUpdateEvent):

        async def run(subscriber: ReservationUpdateSubscriber, event: ReservationUpdateEvent):
            await subscriber(event)

        for subscriber in self._subscribers:
            asyncio.create_task(run(subscriber, event))
