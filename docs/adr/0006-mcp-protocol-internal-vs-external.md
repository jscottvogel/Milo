# ADR 0006: Internal Python Tools vs External MCP Servers (PoC Mode)

## Status
Accepted

## Context
The Milo platform architecture (Section 6.7 of the build specification) outlines the use of the Model Context Protocol (MCP) to decouple tools into independent, secure, sidecar servers. This allows tools to be written in any language and isolated in micro-VMs or Fargate tasks. However, the current phase (Phase 4: Tool Catalog) requires building an initial suite of capabilities (memory search, email draft, calendar read, storage, etc.) to validate the end-to-end agentic loop, including the human-in-the-loop approval gate.

Implementing fully decoupled MCP servers over STDIO/SSE via separate containers adds significant infrastructure overhead and complexity that is not strictly necessary for validating the core LangGraph state machine and the tool orchestration logic.

## Decision
For the PoC (Phase 4), we have decided to implement the Tool Catalog as **in-process Python classes** conforming to a Pydantic-validated `Tool` protocol, rather than standing up independent MCP servers.

All tools reside in `packages/agent/agent/tools/` and are dynamically discovered and instantiated at runtime by a `ToolRegistry`. The LLM's `tool_use` events are intercepted and executed directly in the `AgentRunner` loop.

## Consequences
- **Positive:** Rapid iteration speed. No need to manage sidecar STDIO communication, separate Docker containers, or complex networking for the PoC.
- **Positive:** Direct access to the shared `AgentContext` (database session, tenant ID, etc.) simplifies the implementation of data-heavy tools like `memory.search` and `program.read`.
- **Negative:** Technical debt. The tools are currently tightly coupled to the `AgentRunner` process. When transitioning to a production deployment, these tools will need to be refactored into independent MCP servers that receive tenant context explicitly via the protocol instead of implicit SQLAlchemy sessions.

## Future Plans
Once the PoC validates the product experience (Phase 6+), the Tool Protocol will be deprecated in favor of the official MCP Python SDK, and tools will be migrated into individual services accessible via an MCP routing layer.
