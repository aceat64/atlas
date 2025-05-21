from obstore.store import S3Store

from app.core.config import Settings

settings = Settings()


def get_object_store() -> S3Store:
    return S3Store(
        settings.s3.bucket_name,
        prefix=settings.s3.path_prefix,
        aws_endpoint=str(settings.s3.endpoint),
        access_key_id=settings.s3.access_key_id,
        secret_access_key=settings.s3.secret_access_key,
        client_options={
            "allow_http": settings.s3.allow_http,
            "allow_invalid_certificates": settings.s3.allow_invalid_certificates,
        },
    )
