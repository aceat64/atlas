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


class LogSettings(BaseModel):
    format: Literal["json", "logfmt", "console"] = "console"
    level: Annotated[
        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], BeforeValidator(str.upper)
    ] = "INFO"
    access_log: bool = Field(True, description="Enable/Disable access log")


class TelemetrySettings(BaseModel):
    endpoint: AnyUrl | None = Field(
        None,
        examples=["http://localhost:4318/v1/traces"],
        description="OTLP endpoint",
    )
    console: bool = Field(False, description="Output traces/spans to the console.")


class MetricsSettings(BaseModel):
    host: str | None = Field(
        "127.0.0.1", description="Bind socket to this host. Disabled if set to None."
    )
    port: int = Field(9090, description="Bind socket to this port.")


class CorsSettings(BaseModel):
    """Cross-Origin Resource Sharing (CORS)"""

    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class S3Settings(BaseModel):
    """S3-Compatible object storage settings."""

    bucket_name: str
    path_prefix: str = "/"
    region_name: str | None = Field(
        None,
        examples=["us-east-2"],
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_REGION`).",
    )
    endpoint: AnyHttpUrl | None = Field(
        None,
        examples=["http://localhost:9000"],
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_ENDPOINT_URL_S3`).",  # noqa: E501
    )
    access_key_id: str | None = Field(
        None,
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_ACCESS_KEY_ID`).",
    )
    secret_access_key: str | None = Field(
        None,
        description="If not set, AWS SDK auto-discovery will be used (envvar `AWS_SECRET_ACCESS_KEY`).",  # noqa: E501
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
    model_config = SettingsConfigDict(
        env_prefix="ATLAS",
        toml_file=[
            # First, load the defaults
            # "settings.default.toml",
            # Next, load localdev (if it exists)
            "settings.localdev.toml",
            # Finally, load /config/settings.toml (should only exist when running in a container)
            "/config/settings.toml",
        ],
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
        title="Database URI",
        description="Must include the database name.",
        examples=[
            "postgresql://app:app@localhost:5432/app",
            "postgresql://{username}:{password}@{hostname}:{port}/{dbname}",
        ],
    )

    oidc_url: AnyHttpUrl = Field(
        title="OIDC Discovery URL",
        description="Must be a valid OIDC Discovery endpoint, these usually end with `/.well-known/openid-configuration`.",  # noqa: E501
        examples=["https://authentik/application/o/atlas/.well-known/openid-configuration"],
    )

    log: LogSettings = LogSettings()
    cors: CorsSettings = CorsSettings()
    telemetry: TelemetrySettings = TelemetrySettings()
    metrics: MetricsSettings = MetricsSettings()
    s3: S3Settings

    @field_validator("db_uri")
    def check_db_name(cls, v: PostgresDsn) -> PostgresDsn:
        """Require a database name"""
        assert v.path and len(v.path) > 1, "database must be provided"
        return v


settings = Settings()
