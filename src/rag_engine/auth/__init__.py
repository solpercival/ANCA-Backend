"""
Authentication and authorisation for the RAG engine.

Callers log in with a username and password and receive a short-lived JWT access
token plus a long-lived refresh token in an HttpOnly cookie. The access token is
verified without touching storage; the refresh token is rotated on every use and
tracked in Redis so a stolen copy can be detected and its session revoked.

Modules, from the lowest layer up:

- tiers: account tiers, the authenticated Principal, and tier capability checks.
- passwords: Argon2id hashing and timing-safe verification.
- tokens: creating and verifying access tokens; generating and digesting refresh tokens.
- interfaces: storage protocols (UserRepository, SessionStore) and their records.
- service: AuthService, the login/refresh/logout and account use cases.
- dependencies: FastAPI dependencies that identify the caller and build AuthService.
- schemas: Pydantic response models for the /auth endpoints.
- routes: the /auth APIRouter.
"""
