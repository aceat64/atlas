import os
from datetime import timedelta
from secrets import token_urlsafe
from typing import Annotated, Literal, Self

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    BeforeValidator,
    Field,
    PostgresDsn,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class ServerSettings(BaseModel):
    """
    Uvicorn configuration, passed directly to `uvicorn.run()`.

    ref: https://www.uvicorn.org/settings/
    """

    host: str = Field("127.0.0.1", description="Bind socket to this host.", examples=["0.0.0.0"])
    port: int = Field(8080, description="Bind socket to this port. If 0, an available port will be picked.")
    uds: str | None = Field(None, description="Bind to a UNIX domain socket.", examples=["/var/run/atlas.sock"])
    forwarded_allow_ips: list[str] | str | None = Field(
        None,
        description="Comma separated list of IP Addresses, IP Networks, or literals (e.g. UNIX Socket path) to trust with proxy headers. The literal '*' means trust everything.",  # noqa: E501
        examples=["*", "127.0.0.1", "192.168.0.0/16", "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"],
    )


class LogSettings(BaseModel):
    """Logging"""

    format: Literal["json", "logfmt", "console"] = Field(
        "console",
        description="Console format is human readable and colored. JSON and logfmt are single line per log entry.",
    )
    level: Annotated[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], BeforeValidator(str.upper)] = "INFO"
    access_log: bool = Field(True, description="Enable/Disable access log")


class TelemetrySettings(BaseModel):
    """Telemetry"""

    otel_endpoint: AnyUrl | None = Field(
        None,
        examples=["http://localhost:4318/v1/traces"],
        description="OTLP endpoint. Disabled if set to None.",
    )
    console: bool = Field(
        False,
        description="Output traces/spans directly to the console. The log format setting does not apply to traces/spans.",  # noqa: E501
    )


class PrometheusSettings(BaseModel):
    """Prometheus exporter"""

    host: str | None = Field(
        "0.0.0.0",
        description="Bind socket to this host. Disabled if set to None.",
        examples=["127.0.0.1"],
    )
    port: int = Field(9090, description="Bind socket to this port.")


class MetricsSettings(BaseModel):
    """Metrics"""

    otel_endpoint: AnyUrl | None = Field(
        None,
        examples=["http://localhost:4318/v1/metrics"],
        description="OTLP endpoint. Disabled if set to None.",
    )
    prometheus: PrometheusSettings = PrometheusSettings()


class CorsSettings(BaseModel):
    """Cross-Origin Resource Sharing (CORS)"""

    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class S3Settings(BaseModel):
    """Object Storage"""

    bucket_name: str = "app"
    path_prefix: str = "/"
    region_name: str | None = Field(
        None,
        examples=["us-east-2"],
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_REGION`).",
    )
    endpoint: AnyHttpUrl | None = Field(
        None,
        examples=["http://localhost:9000"],
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_ENDPOINT_URL_S3`).",
    )
    access_key_id: str | None = Field(
        None,
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_ACCESS_KEY_ID`).",
    )
    secret_access_key: str | None = Field(
        None,
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_SECRET_ACCESS_KEY`).",
    )
    allow_http: bool = Field(False, description="Allow connecting over HTTP.")
    allow_invalid_certificates: bool = Field(False, description="Allow invalid/untrusted certificates.")

    @model_validator(mode="after")
    def check_endpoint_http(self) -> Self:
        """Require HTTPS if allow_http is False"""
        if self.endpoint and self.endpoint.scheme == "http" and not self.allow_http:
            raise ValueError("s3.endpoint must be HTTPS unless s3.allow_http is True")
        return self


class ApiSettings(BaseModel):
    cors: CorsSettings = CorsSettings()


class CookieSettings(BaseModel):
    session_key: str = token_urlsafe(32)
    max_age: int = int(timedelta(weeks=2).total_seconds())
    domain: str = "localhost"


class FrontendSettings(BaseModel):
    cors: CorsSettings = CorsSettings()
    cookie: CookieSettings = CookieSettings()


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        title="ATLAS Application Settings",
        toml_file=os.environ.get("ATLAS_CONFIG_FILE", ["settings.toml", "/config/atlas.toml"]),
        env_prefix="ATLAS_",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Load settings from environment variables and toml files.
        return env_settings, TomlConfigSettingsSource(settings_cls)

    db_uri: PostgresDsn = Field(
        PostgresDsn("postgresql://app:app@localhost:5432/app"),
        title="Database URI",
        description="Must include the database name.",
        examples=["postgresql://{username}:{password}@{hostname}:{port}/{dbname}"],
    )

    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oidc_url: AnyHttpUrl = Field(
        AnyHttpUrl("https://authentik/application/o/atlas/.well-known/openid-configuration"),
        title="OIDC Discovery URL",
        description="Must be a valid OIDC Discovery endpoint, these usually end with `/.well-known/openid-configuration`.",  # noqa: E501
        examples=["https://authentik/application/o/atlas/.well-known/openid-configuration"],
    )

    log: LogSettings = LogSettings()
    server: ServerSettings = ServerSettings()
    s3: S3Settings = S3Settings()

    telemetry: TelemetrySettings = TelemetrySettings()
    metrics: MetricsSettings = MetricsSettings()

    api: ApiSettings = ApiSettings()
    frontend: FrontendSettings = FrontendSettings()

    @field_validator("db_uri")
    def check_db_name(cls, v: PostgresDsn) -> PostgresDsn:
        """Require a database name"""
        if v.path and len(v.path) > 1:
            return v
        raise ValueError("database must be provided")


settings: AppSettings = AppSettings.model_construct()
