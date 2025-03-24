from datetime import datetime
from typing import Annotated, Any

import httpx
import jwt
from jwt import PyJWKSet
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    GetPydanticSchema,
    model_validator,
)


class AuthBaseModel(BaseModel):
    # Allows docstrings of attributes to be used for Field() descriptions.
    # Setting `description` in Field() will override the attribute docstring.
    model_config = ConfigDict(use_attribute_docstrings=True)


class OpenIDConnectDiscoveryError(Exception):
    pass


class TokenPayload(AuthBaseModel, extra="allow"):
    """
    ID Tokens and Access Tokens, while two distinct concepts have a lot of
    overlap in the Claims[1] used.

    1. Claim - Piece of information asserted about an Entity.

    References:
    - [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
    - [RFC 9068: JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
    - [RFC 8693: OAuth 2.0 Token Exchange](https://www.rfc-editor.org/rfc/rfc8693)
    - [RFC 7519: JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519)
    """

    iss: str = Field(title="Issuer")
    """
    REQUIRED for ID Tokens (per OIDC) and Access Tokens (per RFC9068).
    
    Issuer Identifier for the Issuer of the response. The iss value is a
    case-sensitive URL using the https scheme that contains scheme, host, and
    optionally, port number and path components and no query or fragment
    components.

    Reference:
    - <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    """

    sub: str = Field(title="Subject")
    """
    REQUIRED for ID Tokens (per OIDC) and Access Tokens (per RFC9068).
    
    Subject Identifier. A locally unique and never reassigned identifier within
    the Issuer for the End-User, which is intended to be consumed by the Client,
    e.g., 24400320 or AItOawmwtWwcT0k51BayewNvutrJUqsvl6qs7A4. It MUST NOT
    exceed 255 ASCII [RFC20] characters in length. The sub value is a
    case-sensitive string.

    Reference:
    - <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    - <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    """

    aud: str | list[str] = Field(title="Audience")
    """
    REQUIRED for ID Tokens (per OIDC) and Access Tokens (per RFC9068).
    
    Audience(s) that this ID Token is intended for. It MUST contain the OAuth
    2.0 client_id of the Relying Party as an audience value. It MAY also contain
    identifiers for other audiences. In the general case, the aud value is an
    array of case-sensitive strings. In the common special case when there is
    one audience, the aud value MAY be a single case-sensitive string.

    Reference:
    - <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    """

    exp: datetime = Field(title="Expiration Time")
    """
    REQUIRED for ID Tokens (per OIDC) and Access Tokens (per RFC9068).
    
    Expiration time on or after which the ID Token MUST NOT be accepted by the
    RP when performing authentication with the OP. The processing of this
    parameter requires that the current date/time MUST be before the expiration
    date/time listed in the value. Implementers MAY provide for some small
    leeway, usually no more than a few minutes, to account for clock skew. Its
    value is a JSON [RFC8259] number representing the number of seconds from
    1970-01-01T00:00:00Z as measured in UTC until the date/time.
    
    See RFC 3339 [RFC3339] for details regarding date/times in general and UTC
    in particular. NOTE: The ID Token expiration time is unrelated the lifetime
    of the authenticated session between the RP and the OP.

    Reference:
    - <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    """

    iat: datetime = Field(title="Issued At")
    """
    REQUIRED for ID Tokens (per OIDC) and Access Tokens (per RFC9068).
    
    Time at which the JWT was issued. Its value is a JSON number representing
    the number of seconds from 1970-01-01T00:00:00Z as measured in UTC until the
    date/time.

    Reference:
    - <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    """

    auth_time: datetime | None = Field(None, title="Authentication Time")
    """
    Time when the End-User authentication occurred. Its value is a JSON number
    representing the number of seconds from 1970-01-01T00:00:00Z as measured in
    UTC until the date/time. When a max_age request is made or when auth_time is
    requested as an Essential Claim, then this Claim is REQUIRED; otherwise, its
    inclusion is OPTIONAL. (The auth_time Claim semantically corresponds to the
    OpenID 2.0 PAPE [OpenID.PAPE] auth_time response parameter.)

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    """

    nonce: str | None = None
    """
    String value used to associate a Client session with an ID Token, and to
    mitigate replay attacks. The value is passed through unmodified from the
    Authentication Request to the ID Token. If present in the ID Token, Clients
    MUST verify that the nonce Claim Value is equal to the value of the nonce
    parameter sent in the Authentication Request. If present in the
    Authentication Request, Authorization Servers MUST include a nonce Claim in
    the ID Token with the Claim Value being the nonce value sent in the
    Authentication Request. Authorization Servers SHOULD perform no other
    processing on nonce values used. The nonce value is a case-sensitive string.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    """

    acr: str | None = Field(None, title="Authentication Context Class Reference")
    """
    OPTIONAL.
    
    Authentication Context Class Reference. String specifying an Authentication
    Context Class Reference value that identifies the Authentication Context
    Class that the authentication performed satisfied. The value "0" indicates
    the End-User authentication did not meet the requirements of ISO/IEC 29115
    [ISO29115] level 1. For historic reasons, the value "0" is used to indicate
    that there is no confidence that the same person is actually there.
    Authentications with level 0 SHOULD NOT be used to authorize access to any
    resource of any monetary value. (This corresponds to the OpenID 2.0 PAPE
    [OpenID.PAPE] nist_auth_level 0.) An absolute URI or an RFC 6711 [RFC6711]
    registered name SHOULD be used as the acr value; registered names MUST NOT
    be used with a different meaning than that which is registered. Parties
    using this claim will need to agree upon the meanings of the values used,
    which may be context specific. The acr value is a case-sensitive string.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    """

    amr: list[str] | None = Field(None, title="Authentication Methods References")
    """
    OPTIONAL.
    
    Authentication Methods References. JSON array of strings that are
    identifiers for authentication methods used in the authentication. For
    instance, values might indicate that both password and OTP authentication
    methods were used. The amr value is an array of case-sensitive strings.
    Values used in the amr Claim SHOULD be from those registered in the IANA
    Authentication Method Reference Values registry [IANA.AMR] established by
    [RFC8176]; parties using this claim will need to agree upon the meanings of
    any unregistered values used, which may be context specific.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    """

    azp: str | None = Field(None, title="Authorized Party")
    """
    OPTIONAL.
    
    Authorized party - the party to which the ID Token was issued. If present,
    it MUST contain the OAuth 2.0 Client ID of this party. The azp value is a
    case-sensitive string containing a StringOrURI value. Note that in practice,
    the azp Claim only occurs when extensions beyond the scope of this
    specification are used; therefore, implementations not using such extensions
    are encouraged to not use azp and to ignore it when it does occur.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#IDToken>
    """

    name: str | None = Field(None, title="Full Name")
    """
    End-User's full name in displayable form including all name parts, possibly
    including titles and suffixes, ordered according to the End-User's locale
    and preferences.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    given_name: str | None = Field(None, title="Given Name")
    """
    Given name(s) or first name(s) of the End-User. Note that in some cultures,
    people can have multiple given names; all can be present, with the names
    being separated by space characters.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    family_name: str | None = Field(None, title="Family Name")
    """
    Surname(s) or last name(s) of the End-User. Note that in some cultures,
    people can have multiple family names or no family name; all can be present,
    with the names being separated by space characters.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    middle_name: str | None = Field(None, title="Middle Name")
    """
    Middle name(s) of the End-User. Note that in some cultures, people can have
    multiple middle names; all can be present, with the names being separated by
    space characters. Also note that in some cultures, middle names are not used.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    nickname: str | None = Field(None, title="Nickname")
    """
    Casual name of the End-User that may or may not be the same as the
    given_name. For instance, a nickname value of Mike might be returned
    alongside a given_name value of Michael.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    preferred_username: str | None = Field(None, title="Preferred Username")
    """
    Shorthand name by which the End-User wishes to be referred to at the RP,
    such as janedoe or j.doe. This value MAY be any valid JSON string including
    special characters such as @, /, or whitespace. The RP MUST NOT rely upon
    this value being unique, as discussed in Section 5.7.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    profile: str | None = Field(None, title="Profile URL")
    """
    URL of the End-User's profile page. The contents of this Web page SHOULD be
    about the End-User.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    picture: str | None = Field(None, title="Picture URL")
    """
    URL of the End-User's profile picture. This URL MUST refer to an image file
    (for example, a PNG, JPEG, or GIF image file), rather than to a Web page
    containing an image. Note that this URL SHOULD specifically reference a
    profile photo of the End-User suitable for displaying when describing the
    End-User, rather than an arbitrary photo taken by the End-User.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    website: str | None = Field(None, title="Website URL")
    """
    URL of the End-User's Web page or blog. This Web page SHOULD contain
    information published by the End-User or an organization that the End-User
    is affiliated with.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    email: str | None = Field(None, title="E-Mail Address")
    """
    End-User's preferred e-mail address. Its value MUST conform to the RFC 5322
    [RFC5322] addr-spec syntax. The RP MUST NOT rely upon this value being
    unique, as discussed in Section 5.7.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    email_verified: bool | None = Field(None, title="E-Mail Verified")
    """
    True if the End-User's e-mail address has been verified; otherwise false.
    When this Claim Value is true, this means that the OP took affirmative steps
    to ensure that this e-mail address was controlled by the End-User at the
    time the verification was performed. The means by which an e-mail address is
    verified is context specific, and dependent upon the trust framework or
    contractual agreements within which the parties are operating.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    gender: str | None = Field(None, title="Gender")
    """
    End-User's gender. Values defined by this specification are female and male.
    Other values MAY be used when neither of the defined values are applicable.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    birthdate: str | None = Field(None, title="Birthday")
    """
    End-User's birthday, represented as an ISO 8601-1 [ISO8601-1] YYYY-MM-DD
    format. The year MAY be 0000, indicating that it is omitted. To represent
    only the year, YYYY format is allowed. Note that depending on the underlying
    platform's date related function, providing just year can result in varying
    month and day, so the implementers need to take this factor into account to
    correctly process the dates.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    zoneinfo: str | None = Field(None, title="Time Zone")
    """
    String from IANA Time Zone Database [IANA.time-zones] representing the
    End-User's time zone. For example, Europe/Paris or America/Los_Angeles.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    locale: str | None = Field(None, title="Locale")
    """
    End-User's locale, represented as a BCP47 [RFC5646] language tag. This is
    typically an ISO 639 Alpha-2 [ISO639] language code in lowercase and an ISO
    3166-1 Alpha-2 [ISO3166-1] country code in uppercase, separated by a dash.
    For example, en-US or fr-CA. As a compatibility note, some implementations
    have used an underscore as the separator rather than a dash, for example,
    en_US; Relying Parties MAY choose to accept this locale syntax as well.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    phone_number: str | None = Field(None, title="Phone Number")
    """
    End-User's preferred telephone number. E.164 [E.164] is RECOMMENDED as the
    format of this Claim, for example, +1 (425) 555-1212 or +56 (2) 687 2400. If
    the phone number contains an extension, it is RECOMMENDED that the extension
    be represented using the RFC 3966 [RFC3966] extension syntax, for example,
    +1 (604) 555-1234;ext=5678.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    phone_number_verified: bool | None = Field(None, title="Phone Number Verified")
    """
    True if the End-User's phone number has been verified; otherwise false. When
    this Claim Value is true, this means that the OP took affirmative steps to
    ensure that this phone number was controlled by the End-User at the time the
    verification was performed. The means by which a phone number is verified is
    context specific, and dependent upon the trust framework or contractual
    agreements within which the parties are operating. When true, the
    phone_number Claim MUST be in E.164 format and any extensions MUST be
    represented in RFC 3966 format.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    address: Any = Field(None, title="Postal Address")
    """
    End-User's preferred postal address. The value of the address member is a
    JSON [RFC8259] structure containing some or all of the members defined in
    Section 5.1.1.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#AddressClaim>
    """

    updated_at: datetime | None = Field(None, title="Last Updated")
    """
    Time the End-User's information was last updated. Its value is a JSON number
    representing the number of seconds from 1970-01-01T00:00:00Z as measured in
    UTC until the date/time.

    Reference: <https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims>
    """

    client_id: str | None = Field(None, title="Client ID")
    """
    REQUIRED for Access Tokens (per RFC9068).
    
    RFC9068:

    As defined in Section 4.3 of [RFC8693].

    RFC8693:

    The client_id claim carries the client identifier of the OAuth 2.0 [RFC6749]
    client that requested the token.

    Reference:
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    - <https://www.rfc-editor.org/rfc/rfc8693#section-4.3>
    """

    jti: str | None = Field(None, title="JWT ID")
    """
    REQUIRED for Access Tokens (per RFC9068).

    RFC9068:

    As defined in Section 4.1.7 of [RFC7519].

    RFC7519:

    The "jti" (JWT ID) claim provides a unique identifier for the JWT.
    The identifier value MUST be assigned in a manner that ensures that
    there is a negligible probability that the same value will be
    accidentally assigned to a different data object; if the application
    uses multiple issuers, collisions MUST be prevented among values
    produced by different issuers as well.  The "jti" claim can be used
    to prevent the JWT from being replayed.  The "jti" value is a case-
    sensitive string.  Use of this claim is OPTIONAL.

    Reference:
    - <https://www.rfc-editor.org/rfc/rfc9068#name-data-structure>
    - <https://www.rfc-editor.org/rfc/rfc7519#section-4>
    """

    nbf: datetime | None = Field(None, title="Not Before")
    """
    The "nbf" (not before) claim identifies the time before which the JWT
    MUST NOT be accepted for processing.  The processing of the "nbf"
    claim requires that the current date/time MUST be after or equal to
    the not-before date/time listed in the "nbf" claim.  Implementers MAY
    provide for some small leeway, usually no more than a few minutes, to
    account for clock skew.  Its value MUST be a number containing a
    NumericDate value.  Use of this claim is OPTIONAL.

    Reference: <https://www.rfc-editor.org/rfc/rfc7519#section-4>
    """

    sid: str | None = None
    """
    TODO: Unknown/Not Defined
    """

    uid: str | None = None
    """
    TODO: Unknown/Not Defined
    """


class ProviderMetadata(AuthBaseModel):
    """OpenID Connect Discovery Provider Metadata"""

    issuer: AnyHttpUrl = Field(title="Issuer")
    """
    REQUIRED.

    URL using the https scheme with no query or fragment components that the OP
    asserts as its Issuer Identifier. If Issuer discovery is supported, this
    value MUST be identical to the issuer value returned by WebFinger. This also
    MUST be identical to the iss Claim value in ID Tokens issued from this
    Issuer.
    """

    authorization_endpoint: AnyHttpUrl = Field(title="Authorization Endpoint")
    """
    REQUIRED.

    URL of the OP's OAuth 2.0 Authorization Endpoint [OpenID.Core]. This URL
    MUST use the https scheme and MAY contain port, path, and query parameter
    components.
    """

    token_endpoint: AnyHttpUrl = Field(title="Token Endpoint")
    """
    URL of the OP's OAuth 2.0 Token Endpoint [OpenID.Core]. This is REQUIRED unless
    only the Implicit Flow is used. This URL MUST use the https scheme and MAY contain
    port, path, and query parameter components.
    """

    userinfo_endpoint: AnyHttpUrl | None = Field(None, title="Userinfo Endpoint")
    """
    RECOMMENDED.

    URL of the OP's UserInfo Endpoint [OpenID.Core]. This URL MUST use the https
    scheme and MAY contain port, path, and query parameter components.
    """

    jwks_uri: AnyHttpUrl = Field(title="JWKS URI")
    """
    REQUIRED.

    URL of the OP's JWK Set [JWK] document, which MUST use the https scheme.
    This contains the signing key(s) the RP uses to validate signatures from the
    OP. The JWK Set MAY also contain the Server's encryption key(s), which are
    used by RPs to encrypt requests to the Server. When both signing and
    encryption keys are made available, a use (public key use) parameter value
    is REQUIRED for all keys in the referenced JWK Set to indicate each key's
    intended usage. Although some algorithms allow the same key to be used for
    both signatures and encryption, doing so is NOT RECOMMENDED, as it is less
    secure. The JWK x5c parameter MAY be used to provide X.509 representations
    of keys provided. When used, the bare key values MUST still be present and
    MUST match those in the certificate. The JWK Set MUST NOT contain private or
    symmetric key values.
    """

    registration_endpoint: AnyHttpUrl | None = Field(None, title="Registration Endpoint")
    """
    RECOMMENDED.

    URL of the OP's Dynamic Client Registration Endpoint [OpenID.Registration],
    which MUST use the https scheme. 
    """

    scopes_supported: list[str] | None = Field(["openid"], title="Scopes Supported")
    """
    RECOMMENDED.

    JSON array containing a list of the OAuth 2.0 [RFC6749] scope values that
    this server supports. The server MUST support the openid scope value.
    Servers MAY choose not to advertise some supported scope values even when
    this parameter is used, although those defined in [OpenID.Core] SHOULD be
    listed, if supported.
    """

    response_types_supported: list[str] | None = Field(None, title="Response Types Supported")
    """
    REQUIRED.

    JSON array containing a list of the OAuth 2.0 response_type values that this
    OP supports. Dynamic OpenID Providers MUST support the code, id_token, and the
    id_token token Response Type values.
    """

    response_modes_supported: list[str] | None = Field(None, title="Response Mode Supported")
    """
    OPTIONAL.

    JSON array containing a list of the OAuth 2.0 response_mode values that this
    OP supports, as specified in OAuth 2.0 Multiple Response Type Encoding Practices
    [OAuth.Responses]. If omitted, the default for Dynamic OpenID Providers is
    ["query", "fragment"].
    """

    grant_types_supported: list[str] | None = Field(None, title="Grant Types Supported")
    """
    OPTIONAL.

    JSON array containing a list of the OAuth 2.0 Grant Type values that this OP
    supports. Dynamic OpenID Providers MUST support the authorization_code and
    implicit Grant Type values and MAY support other Grant Types. If omitted, the
    default value is ["authorization_code", "implicit"].
    """

    acr_values_supported: list[str] | None = Field(None, title="ACR Values Supported")
    """
    OPTIONAL.

    JSON array containing a list of the Authentication Context ClassReferences
    that this OP supports.
    """

    subject_types_supported: list[str] = Field(title="Subject Types Supported")
    """
    REQUIRED.

    JSON array containing a list of the Subject Identifier types that this OP supports.
    Valid types include pairwise and public. 
    """

    id_token_signing_alg_values_supported: list[str]
    """
    REQUIRED.

    JSON array containing a list of the JWS signing algorithms (alg values) supported
    by the OP for the ID Token to encode the Claims in a JWT [JWT]. The algorithm
    RS256 MUST be included. The value none MAY be supported but MUST NOT be used
    unless the Response Type used returns no ID Token from the Authorization Endpoint
    (such as when using the Authorization Code Flow).
    """

    id_token_encryption_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE encryption algorithms (alg values)
    supported by the OP for the ID Token to encode the Claims in a JWT [JWT].
    """

    id_token_encryption_enc_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE encryption algorithms (enc values)
    supported by the OP for the ID Token to encode the Claims in a JWT [JWT].
    """

    userinfo_signing_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWS [JWS] signing algorithms (alg values)
    [JWA] supported by the UserInfo Endpoint to encode the Claims in a JWT [JWT].
    The value none MAY be included.
    """

    userinfo_encryption_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE [JWE] encryption algorithms (alg values)
    [JWA] supported by the UserInfo Endpoint to encode the Claims in a JWT [JWT].
    """

    userinfo_encryption_enc_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE encryption algorithms (enc values)
    [JWA] supported by the UserInfo Endpoint to encode the Claims in a JWT [JWT].
    """

    request_object_signing_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWS signing algorithms (alg values) supported
    by the OP for Request Objects, which are described in Section 6.1 of OpenID
    Connect Core 1.0 [OpenID.Core]. These algorithms are used both when the Request
    Object is passed by value (using the request parameter) and when it is passed
    by reference (using the request_uri parameter). Servers SHOULD support none
    and RS256.
    """

    request_object_encryption_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE encryption algorithms (alg values)
    supported by the OP for Request Objects. These algorithms are used both when
    the Request Object is passed by value and when it is passed by reference.
    """

    request_object_encryption_enc_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWE encryption algorithms (enc values)
    supported by the OP for Request Objects. These algorithms are used both when
    the Request Object is passed by value and when it is passed by reference.
    """

    token_endpoint_auth_methods_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of Client Authentication methods supported by
    this Token Endpoint. The options are client_secret_post, client_secret_basic,
    client_secret_jwt, and private_key_jwt, as described in Section 9 of OpenID
    Connect Core 1.0 [OpenID.Core]. Other authentication methods MAY be defined
    by extensions. If omitted, the default is client_secret_basic -- the HTTP Basic
    Authentication Scheme specified in Section 2.3.1 of OAuth 2.0 [RFC6749].
    """

    token_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    """
    OPTIONAL.

    JSON array containing a list of the JWS signing algorithms (alg values) supported
    by the Token Endpoint for the signature on the JWT [JWT] used to authenticate
    the Client at the Token Endpoint for the private_key_jwt and client_secret_jwt
    authentication methods. Servers SHOULD support RS256. The value none MUST NOT
    be used.
    """

    display_values_supported: list[str] | None = Field(None, title="Display Values Supported")
    """
    OPTIONAL.

    JSON array containing a list of the display parameter values that the OpenID
    Provider supports. These values are described in Section 3.1.2.1 of OpenID
    Connect Core 1.0 [OpenID.Core].
    """

    claim_types_supported: list[str] | None = Field(None, title="Claim Types Supported")
    """
    OPTIONAL.

    JSON array containing a list of the Claim Types that the OpenID Provider supports.
    These Claim Types are described in Section 5.6 of OpenID Connect Core 1.0
    [OpenID.Core]. Values defined by this specification are normal, aggregated,
    and distributed. If omitted, the implementation supports only normal Claims.
    """

    claims_supported: list[str] | None = Field(None, title="Claims Supported")
    """
    RECOMMENDED.

    JSON array containing a list of the Claim Names of the Claims that the OpenID
    Provider MAY be able to supply values for. Note that for privacy or other reasons,
    this might not be an exhaustive list.
    """

    service_documentation: AnyHttpUrl | None = Field(None, title="Service Documentation")
    """
    OPTIONAL.

    URL of a page containing human-readable information that developers might want
    or need to know when using the OpenID Provider. In particular, if the OpenID
    Provider does not support Dynamic Client Registration, then information on how
    to register Clients needs to be provided in this documentation.
    """

    claims_locales_supported: list[str] | None = None
    """
    OPTIONAL.

    Languages and scripts supported for values in Claims being returned, represented
    as a JSON array of BCP47 [RFC5646] language tag values. Not all languages and
    scripts are necessarily supported for all Claim values.
    """

    ui_locales_supported: list[str] | None = None
    """
    OPTIONAL.

    Languages and scripts supported for the user interface, represented as a JSON
    array of BCP47 [RFC5646] language tag values.
    """

    claims_parameter_supported: bool = False
    """
    OPTIONAL.

    Boolean value specifying whether the OP supports use of the claims parameter,
    with true indicating support. If omitted, the default value is false.
    """

    request_parameter_supported: bool = False
    """
    OPTIONAL.

    Boolean value specifying whether the OP supports use of the request parameter,
    with true indicating support. If omitted, the default value is false.
    """

    request_uri_parameter_supported: bool = True
    """
    OPTIONAL.

    Boolean value specifying whether the OP supports use of the request_uri parameter,
    with true indicating support. If omitted, the default value is true.
    """

    require_request_uri_registration: bool = False
    """
    OPTIONAL.

    Boolean value specifying whether the OP requires any request_uri values used
    to be pre-registered using the request_uris registration parameter. Pre-registration
    is REQUIRED when the value is true. If omitted, the default value is false.
    """

    op_policy_uri: AnyHttpUrl | None = None
    """
    OPTIONAL.

    URL that the OpenID Provider provides to the person registering the Client to
    read about the OP's requirements on how the Relying Party can use the data
    provided by the OP. The registration process SHOULD display this URL to the
    person registering the Client if it is given.
    """

    op_tos_uri: AnyHttpUrl | None = Field(None, title="OpenID Provider Terms of Service URI")
    """
    OPTIONAL.

    URL that the OpenID Provider provides to the person registering the Client to
    read about the OpenID Provider's terms of service. The registration process
    SHOULD display this URL to the person registering the Client if it is given.
    """


class OpenIDConnectDiscovery(AuthBaseModel):
    discovery_url: AnyHttpUrl
    """The OpenID Connect discovery URL"""
    metadata: ProviderMetadata
    """OpenID Provider Metadata"""
    jwks: Annotated[PyJWKSet, GetPydanticSchema(lambda _s, h: h(Any))]
    """JSON Web Key Set"""
    last_updated: datetime = Field(default_factory=datetime.now)
    """Time when the discovery data was fetched"""

    def __init__(self, discovery_url: AnyHttpUrl, **data: Any):
        # If only discovery_url is provided as a positional argument,
        # convert it to the expected format
        data["discovery_url"] = discovery_url
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def fetch_discovery_and_jwks(cls, data: dict[str, Any]) -> dict[str, Any]:
        if isinstance(data, dict) and "discovery_url" in data:
            discovery_url = data["discovery_url"]
            try:
                # Fetch the discovery document
                with httpx.Client(timeout=10.0) as client:
                    # Get discovery document
                    discovery_response = client.get(str(discovery_url))
                    discovery_response.raise_for_status()
                    metadata = discovery_response.json()

                    # Get JWKS using the jwks_uri from the discovery document
                    jwks_uri = metadata.get("jwks_uri")
                    if not jwks_uri:
                        raise KeyError("jwks_uri not found in discovery document")

                    jwks_response = client.get(jwks_uri)
                    jwks_response.raise_for_status()
                    jwks_data = jwks_response.json()

                # Construct the result with nested structure
                return {
                    "discovery_url": discovery_url,
                    "metadata": metadata,
                    "jwks": PyJWKSet.from_dict(jwks_data),
                }
            except Exception as exc:
                raise OpenIDConnectDiscoveryError(
                    f"Failed to fetch OpenID Connect discovery document or JWKS: {exc}"
                ) from exc
        return data

    def decode_access_token(self, token: str, audience: str | None = None) -> Any:
        """
        Decode and validate a JWT access token using the JWKS data.

        Args:
            token: The JWT token to decode and validate
            audience: Optional audience to validate against

        Returns:
            Dict[str, Any]: The decoded token payload if valid

        Raises:
            ValueError: If the token is invalid for any reason
        """
        # Get the header without verifying the token
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if not kid:
            raise ValueError("Token header does not contain a Key ID (kid)")

        # Verify and decode the token using the key
        return jwt.decode(
            token,
            key=self.jwks[kid],
            algorithms=self.jwks[kid].algorithm_name,
            audience=audience,
            issuer=str(self.metadata.issuer),
            options={"require": ["exp", "iat"], "verify_aud": audience is not None},
        )

    def refresh_jwks(self) -> None:
        """Refresh the JWKS data from the jwks_uri endpoint."""
        try:
            with httpx.Client(timeout=10.0) as client:
                jwks_response = client.get(str(self.metadata.jwks_uri))
                jwks_response.raise_for_status()
                jwks_data = jwks_response.json()

            self.jwks = PyJWKSet.from_dict(jwks_data)
            self.last_updated = datetime.now()
        except Exception as exc:
            raise OpenIDConnectDiscoveryError(f"Failed to refresh JWKS: {exc}") from exc
