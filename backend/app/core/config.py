from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    PostgresDsn,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


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
    url: AnyHttpUrl | None = Field(
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

    cors: CorsSettings = CorsSettings()
    s3: S3Settings

    @field_validator("db_uri")
    def check_db_name(cls, v: PostgresDsn) -> PostgresDsn:
        """Require a database name"""
        assert v.path and len(v.path) > 1, "database must be provided"
        return v


settings = Settings()
