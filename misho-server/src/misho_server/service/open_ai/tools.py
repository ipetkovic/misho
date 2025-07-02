create_job_tool = {
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
            "Show a list of current jobs"
            "Possible status values: PENDING, FAILED, SUCCESS."
            "Do not list jobs with numbered bullets, since user can confuse them with job IDs."
            "Always include courts by priority in the response. Always include job ID in the response."
            "Never include user in the response."
        ),
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


def get_tools():
    return [
        create_job_tool,
        list_jobs_tool,
        delete_job_tool
    ]
