import os
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
    port: int = Field(
        8080, description="Bind socket to this port. If 0, an available port will be picked."
    )
    uds: str | None = Field(
        None, description="Bind to a UNIX domain socket.", examples=["/var/run/atlas.sock"]
    )
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
    level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], BeforeValidator(str.upper)
    ] = "INFO"
    access_log: bool = Field(True, description="Enable/Disable access log")


class TelemetrySettings(BaseModel):
    """Telemetry"""

    endpoint: AnyUrl | None = Field(
        None,
        examples=["http://localhost:4318/v1/traces"],
        description="OTLP endpoint",
    )
    console: bool = Field(
        False,
        description="Output traces/spans directly to the console. The log format setting does not apply to traces/spans.",  # noqa: E501
    )


class MetricsSettings(BaseModel):
    """Metrics"""

    host: str | None = Field(
        "127.0.0.1",
        description="Bind socket to this host. Disabled if set to None.",
        examples=["0.0.0.0"],
    )
    port: int = Field(9090, description="Bind socket to this port.")


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
    allow_invalid_certificates: bool = Field(
        False, description="Allow invalid/untrusted certificates."
    )

    @model_validator(mode="after")
    def check_endpoint_http(self) -> Self:
        """Require HTTPS if allow_http is False"""
        if self.endpoint and self.endpoint.scheme == "http" and not self.allow_http:
            raise ValueError("s3.endpoint must be HTTPS unless s3.allow_http is True")
        return self


class Settings(BaseSettings):
    """Application settings"""

    # Look for and load settings from specific toml files
    model_config = SettingsConfigDict(env_prefix="ATLAS_", env_nested_delimiter="__")

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
        return env_settings, TomlConfigSettingsSource(
            settings_cls,
            toml_file=os.environ.get(
                "ATLAS_CONFIG_FILE", ["/config/settings.toml", "settings.toml"]
            ),
        )

    db_uri: PostgresDsn = Field(
        PostgresDsn("postgresql://app:app@localhost:5432/app"),
        title="Database URI",
        description="Must include the database name.",
        examples=["postgresql://{username}:{password}@{hostname}:{port}/{dbname}"],
    )

    oidc_url: AnyHttpUrl = Field(
        AnyHttpUrl("https://authentik/application/o/atlas/.well-known/openid-configuration"),
        title="OIDC Discovery URL",
        description="Must be a valid OIDC Discovery endpoint, these usually end with `/.well-known/openid-configuration`.",  # noqa: E501
        examples=["https://authentik/application/o/atlas/.well-known/openid-configuration"],
    )

    log: LogSettings = LogSettings()
    server: ServerSettings = ServerSettings()
    cors: CorsSettings = CorsSettings()
    telemetry: TelemetrySettings = TelemetrySettings()
    metrics: MetricsSettings = MetricsSettings()
    s3: S3Settings = S3Settings()

    @field_validator("db_uri")
    def check_db_name(cls, v: PostgresDsn) -> PostgresDsn:
        """Require a database name"""
        assert v.path and len(v.path) > 1, "database must be provided"
        return v
