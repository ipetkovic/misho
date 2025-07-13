

class OpenAiToolHandler:
    def __init__(self, user_client):
        self._user_client = user_client

    async def handle_tool_call(self, tool_call):
        if tool_call.type == "function":
            result = await self._user_client.call_function(tool_call.function)
            shrinked_result = self._user_client.shrink_result(result)
            print(shrinked_result)
            self._user_client.tool_call_append(tool_call, shrinked_result)
        elif tool_call.type == "content":
            content = tool_call.content
            self._user_client.content_append(content)
