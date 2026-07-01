# Contributing to Converse

Thank you for investing your time in contributing to our platform!

## Development Workflow

1. **Branching**: Use `feature/issue-number-description` or `fix/issue-number-description`.
2. **Code Standards**: 
   - All code must pass `ruff` and `mypy --strict`.
   - Use `make format` and `make lint` before committing.
   - Follow Domain Driven Design principles. Ensure logic resides in the appropriate layer (Domain, Application, Infrastructure).
3. **Testing**:
   - Write unit tests for all domain and application logic.
   - Write integration tests for infrastructure and API endpoints.
   - `make test` must pass.

## Adding a New Microservice

When adding a new service:
1. Copy the standard `pyproject.toml` configuration.
2. Rely on `converse-shared` for all boilerplate (DDD, FastAPI app creation, Auth, Config).
3. Implement `Domain`, `Application`, `Infrastructure`, and `API` layers.
4. Add the service to `docker-compose.yml` and `docker-compose.dev.yml`.
5. Expose it via the API Gateway.
