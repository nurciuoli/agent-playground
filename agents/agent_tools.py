#Agent util jsons
execute_plan_json = {
    "name": "execute_plan",
    "description": "Come up with an organized and thoughtful plan of how to break up the user request into individual actionable pieces",
    "parameters": {
        "type": "object",
        "properties": {
            "objective": {"type": "string"},
            "tasks": {
                "type": "array",
                "description": "An array of individual tasks that workers can execute asynchronously",
                "items": {
                    "type": "object",
                    "properties": {
                        "instructions": {"type": "string",
                                         "description":"a detailed prompt describing exactly what the worker should do and any context needed"},
                        "output_file": {
                            "type": "string",
                            "description": "full filepath with extension, such as code.py",
                        },
                        "choices": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["instructions","output_file"],
                },
            },
        },
        "required": ["objective", "tasks"],
    },
}


get_review_json = {
    "name": "get_review",
    "description": "Use to get a peer review on your final work",
    "parameters": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "description": "Files to have reviewed and detailed background on the question you are asking",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_name_with_ext": {"type": "string",
                                      "description":"a name and filepath for the file. EXAMPLE: main.py, poem1.txt, templates/index.html"},
                        "content": {"type": "string",
                                    "description":"a summary of what you want reviewed in the file"},
                                    "choices": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["file_name_with_extension","content"],
                },
            },
        },
        "required": ["files"],
    },
}


get_second_opinion_json = {
    "name": "get_second_opinion",
    "description": "Use this to ask a peer a question or get their opinion",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "question to get advice or help get answered",
            },
        },
        "required": ["question"],
    },
}

