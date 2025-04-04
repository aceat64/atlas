# TODO

- [ ] All the CI/CD stuff
- [ ] Setup Renovate

## Backend

- [x] Finish out routes
  - [x] Collections
  - [x] Rooms
  - [x] Stacks
  - [x] Users
- [x] [Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [x] filter for list_items endpoint
- [x] sort for all list_* endpoints
- [ ] Item search endpoint
- [ ] Validate foreign keys, ideally using `RequestValidationError` instead of `HTTPException(status_code=404)`
- [x] Actually save attachments to object storage
- [x] Figure out database async
- [ ] Move s3 client setup to deps?
- [ ] Logging
- [ ] Tracing
- [ ] Metrics
- [ ] [OAuth2 scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
- [ ] [Generate clients](https://fastapi.tiangolo.com/advanced/generate-clients/)
- [ ] Improve error message for invalid config
- [ ] CLI command to generate an example toml config file

## Frontend

- [ ] Start
