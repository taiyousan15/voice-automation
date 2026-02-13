# ADR-007: Authentication & Authorization Strategy

**Status**: Accepted

**Date**: 2026-02-11

**Decision Makers**: Architecture Committee

---

## Context

The podcast system requires secure authentication for:
- **Admin Dashboard**: Content management, settings control
- **Public API**: Analytics, custom integrations
- **Internal Services**: Inter-service communication

Key constraints:

- **Simplicity**: Minimal complexity for MVP
- **Security**: Protection against token theft, replay attacks
- **Cost**: ¥0 (no managed auth service needed)
- **Scalability**: Support multiple authenticated users
- **JWT Compatibility**: Easy integration with external services

---

## Decision

Adopt **JWT-based authentication** with **database-backed refresh tokens**:

```
Admin Dashboard:
  User email/password → JWToken (15 min expiry)
                    → RefreshToken (30 day expiry, stored in DB)

Public API:
  API Key (long-lived token, can be rotated)
  or
  OAuth2 (for future 3rd party integrations)

Internal Services:
  Service-to-Service: Shared secret + HMAC signature
```

### Implementation

```python
# JWT token management
class AuthService:
    def login(email: str, password: str) -> TokenPair:
        """Generate JWT access token + refresh token."""
        user = User.find_by_email(email)
        if not user.verify_password(password):
            raise AuthError()

        access_token = jwt.encode(
            payload={'user_id': user.id, 'exp': now() + 15*min},
            secret=settings.JWT_SECRET,
            algorithm='HS256'
        )

        refresh_token = RefreshToken.create(
            user_id=user.id,
            expires_at=now() + 30*days,
            token=generate_secure_random(32)
        )

        return TokenPair(access=access_token, refresh=refresh_token.token)

    def verify_token(token: str) -> User:
        """Verify JWT token and return user."""
        try:
            payload = jwt.decode(
                token,
                secret=settings.JWT_SECRET,
                algorithms=['HS256']
            )
            return User.find(payload['user_id'])
        except JWTExpired:
            raise AuthError("Token expired, use refresh token")
        except JWTInvalid:
            raise AuthError("Invalid token")
```

---

## Consequences

### Benefits ✅

1. **Simplicity**: Standard JWT implementation, widely understood
2. **Stateless**: No session storage required
3. **Scalability**: Works across distributed services
4. **Security**: Refresh token rotation, short expiry times
5. **Cost**: ¥0 (built-in to application)

### Drawbacks ⚠️

1. **Token Revocation**: Cannot immediately revoke access tokens (until expiry)
2. **Secret Management**: JWT secret must be secured in environment variables
3. **Token Size**: JWT adds overhead to each request

---

## Alternatives Considered

### ❌ Alternative 1: Session-Based (Cookies)

**Pros**: Simple, revocable immediately
**Cons**: Requires session store, not suitable for distributed systems
**Why Rejected**: JWT better for microservices architecture

### ❌ Alternative 2: OAuth2 + OpenID Connect

**Pros**: Industry standard, supports 3rd party auth
**Cons**: Over-engineered for MVP, complexity not justified
**Why Rejected**: Too complex for initial release, can add later

### ❌ Alternative 3: API Keys Only

**Pros**: Simple, no token refresh needed
**Cons**: No user context, keys harder to rotate safely
**Why Rejected**: JWT provides better security properties

---

## Implementation Plan

### Phase 1: JWT Setup (Week 1)
- [ ] Implement JWT encoding/decoding
- [ ] Create login endpoint
- [ ] Add middleware for token verification
- [ ] Secure JWT secret in environment

### Phase 2: Refresh Token (Week 2)
- [ ] Implement refresh token storage (PostgreSQL)
- [ ] Add token refresh endpoint
- [ ] Implement token rotation strategy
- [ ] Add token revocation (logout)

---

## Related Requirements

- REQ-501: Infrastructure & API Reliability
- REQ-902: Security (Authentication)

---

## Related ADRs

- ADR-006: Database Selection
