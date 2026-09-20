from app.ai_agent.contracts import AgentPrincipal, AgentToolDefinition, AgentToolName


class AgentToolAuthorizationPolicy:
    def is_authorized(
        self,
        principal: AgentPrincipal,
        definition: AgentToolDefinition,
    ) -> bool:
        if definition.required_permission not in principal.permissions:
            return False
        if (
            principal.allowed_tools is not None
            and definition.name not in principal.allowed_tools
        ):
            return False
        return True

    def authorize(
        self,
        principal: AgentPrincipal,
        definition: AgentToolDefinition,
    ) -> None:
        if not self.is_authorized(principal, definition):
            raise AgentToolAuthorizationError(
                f"Agent is not authorized to call {definition.name.value}"
            )


class AgentToolAuthorizationError(PermissionError):
    pass


class UnknownAgentToolError(LookupError):
    def __init__(self, tool_name: AgentToolName | str) -> None:
        super().__init__(f"Unknown agent tool: {tool_name}")
