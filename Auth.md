# Auth

## Backend

`Resource Server (RS)` as defined in [RFC6749](https://www.rfc-editor.org/rfc/rfc6749.txt):

The server hosting the protected resources, capable of accepting and responding to protected resource requests using access tokens.

On startup the backend service will:

1. Make a GET request to the OpenID Connect Discovery endpoint (`oidc_url` in the config), save as `oidc_config`.
2. Make a GET request to the URL from `oidc_config['jwks_uri']`, save as `signing_keys`.

For every request made to the backend:

1. Check for `Authorization: Bearer` header.
2. Validate the JWT:
   1. Signed by a key listed in `signing_keys`
   2. `payload['iss']` matches `oidc_config['issuer']`
   3. Not expired, `payload['exp']` must be in the future
   4. Wasn't issued in the future, `payload['iat']` must be in the past
   5. Check `payload['aud']`?

## Frontend

- Authorization Code Flow with Proof Key for Code Exchange (PKCE)

## Notes

- Official specifications
  - [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)
  - [OpenID Connect Discovery 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-discovery-1_0.html)
  - [OpenID Connect Dynamic Client Registration 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-registration-1_0.html)
  - [OAuth 2.0 Multiple Response Type Encoding Practices](https://openid.net/specs/oauth-v2-multiple-response-types-1_0.html)
  - [The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749.txt)
  - [The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.txt)
  - [RFC 9068: JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
- <https://openid.net/developers/how-connect-works/>
- <https://auth0.com/docs/get-started/authentication-and-authorization-flow>
- <https://techdocs.akamai.com/eaa/docs/openid-connect-concepts-terms>
- Best practices
  - [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
