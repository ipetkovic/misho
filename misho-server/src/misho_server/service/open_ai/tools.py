from openai.types.chat import ChatCompletionToolParam

create_job_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "create_job",
        "description": (
            "Create a job with a time slot, an action (RESERVE or NOTIFY), and a list of preferred court IDs in priority order."
            "Croatian: Kreiraj zadatak za zadani termin, akcijom (REZERVIRAJ ili OBAVIJESTI), i listom preferiranih terena poredanih po prioritetu."
        ),
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
                            "description": "If user specifies start hour only... If it is less than 17, to_hour is from_hour + 1, otherwise to_hour is from_hour + 2.",
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
                },
                "expires_at": {
                    "type": "string",
                    "format": "date-time",
                    "title": "Job Expiration Time",
                    "description": (
                        "The time when the job expires. Don't force user to specify this. In that case reservation job will expire 10 hours before start of the time slot."
                        "Notification job will expire on start of the time slot."
                    )
                },
                "on_expiry_action": {
                    "type": "string",
                    "enum": ["CREATE_NOTIFY_JOB", None],
                    "title": "On Expiry Action",
                    "description": (
                        "Action to take when the job expires"
                        "This is only applicable for RESERVE action. If set to None, no action will be taken on expiry."
                        "Use CREATE_NOTIFY_JOB for reserve actions by default, and for NOTIFY None."
                    )
                }
            },
            "required": ["time_slot", "action", "courts_by_priority"],
            "title": "JobCreateApi"
        }
    }
}

reserve_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "reserve",
        "description": (
            "Reserve court immidiately for the given time slot. This can be used only for up to five days in advance. In contrast to create_job, this does not create a job, but reserves the court immediately."
        ),
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
                            "title": "HourSlot",
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
                            "description": "If user specifies start hour only... If it is less than 17, to_hour is from_hour + 1, otherwise to_hour is from_hour + 2.",
                            "required": ["from_hour", "to_hour"]
                        }
                    },
                    "required": ["date", "hour_slot"],
                    "title": "TimeSlot"
                },
                "court": {
                    "type": "integer",
                    "title": "Court to reserve",
                }
            },
            "required": ["time_slot", "court"],
            "title": "ReserveRequest"
        }
    }
}

cancel_reservation_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "cancel_reservation",
        "description": (
            "Cancel reservation for the court immidiately for the given time slot. This can be used only for up to five days in advance. In contrast to create_job, this does not create a job, but cancels reserve immediately."
        ),
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
                            "title": "HourSlot",
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
                            "description": "If user specifies start hour only... If it is less than 17, to_hour is from_hour + 1, otherwise to_hour is from_hour + 2.",
                            "required": ["from_hour", "to_hour"]
                        }
                    },
                    "required": ["date", "hour_slot"],
                    "title": "TimeSlot"
                },
                "court": {
                    "type": "integer",
                    "title": "Court to reserve",
                }
            },
            "required": ["time_slot", "court"],
            "title": "ReserveCancelRequest"
        }
    }
}

list_jobs_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "list_jobs",
        "description": (
            "Show a list of current jobs"
            "Possible status values: PENDING, FAILED, SUCCESS."
            "If PENDING is returned, use ACTIVE status."
            "Do not list jobs with numbered bullets, since user can confuse them with job IDs."
            "Always include courts by priority in the response. Always include job ID in the response."
            "Include expires_at and on_expiry_action in the response, if it is set."
            "Never include user in the response."
        ),
    }
}

delete_job_tool: ChatCompletionToolParam = {
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

reservation_calendar_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "get_reservations",
        "description": "Get the reservation calendar for up to five days in advance. Should return a table",
        "parameters": {
            "type": "object",
            "properties": {
                "only_for_user": {
                    "type": "boolean",
                    "description": "If true, only return reservations made by the current user. If false, return all reservations.",
                },
                "dates": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "date",
                    },
                    "description": "Filter reservations by specific dates."
                }
            },
            "required": []  # Both parameters are optional
        }
    }
}


def get_tools() -> list[ChatCompletionToolParam]:
    return [
        create_job_tool,
        list_jobs_tool,
        delete_job_tool,
        reserve_tool,
        cancel_reservation_tool,
        reservation_calendar_tool
    ]
