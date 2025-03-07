from pydantic import (
    AnyHttpUrl,
    BaseModel,
    PostgresDsn,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class CorsSetings(BaseModel):
    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class Settings(BaseSettings):
    """Application settings"""

    # Look for and load settings from specific toml files
    model_config = SettingsConfigDict(
        toml_file=[
            # First, load the defaults
            # "settings.default.toml",
            # Next, load localdev (if it exists)
            "settings.localdev.toml",
            # Finally, load /config/settings.toml (should only exist when running in a container)
            "/config/settings.toml",
        ]
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

    db_uri: PostgresDsn = PostgresDsn("postgresql://app:app@localhost:5432/app")
    oidc_url: AnyHttpUrl = AnyHttpUrl(
        "https://authentik/application/o/atlas/.well-known/openid-configuration"
    )
    """OIDC Discovery URL"""
    cors: CorsSetings = CorsSetings()

    @field_validator("db_uri")
    def check_db_name(cls, v: PostgresDsn) -> PostgresDsn:
        """Require a database name"""
        assert v.path and len(v.path) > 1, "database must be provided"
        return v


settings = Settings()
