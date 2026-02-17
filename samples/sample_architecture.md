# Sample Architecture Document

Use this file to test the architectural review agent.

## Overview

This is a placeholder architecture document in Markdown. The agent will parse it and invoke the LLM for feedback.

## Components

- **API Layer**: REST endpoints.
- **Service Layer**: Business logic.
- **Data Layer**: Persistence and caches.

## Decisions

- Use OpenAPI for API contracts.
- Prefer async I/O for scalability.

## Open Questions

- Caching strategy for read-heavy workloads.
- Observability (metrics, tracing).
