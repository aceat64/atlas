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
- [x] sort for list endpoints
- [ ] filter for list endpoinds
  - [ ] Collections
  - [x] Items
  - [ ] Rooms
  - [ ] Stacks
  - [ ] Tags
  - [ ] Users
- [ ] Item search endpoint
- [ ] validate that foreign keys are valid during model_validate
- [ ] Use `RequestValidationError` instead of `HTTPException(status_code=404)` for POST/PUT/DELETE endpoints
- [x] Create middleware for [Link headers](./backend/Link_Header.md)
- [x] Actually save attachments to object storage
- [x] Figure out database async
- [ ] Move s3 client setup to deps?
- [ ] Logging
- [ ] Tracing
- [ ] Metrics
- [ ] [OAuth2 scopes](https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/)
- [ ] [Generate clients](https://fastapi.tiangolo.com/advanced/generate-clients/)

## Frontend

- [ ] Start
