import os
from datetime import timedelta
from urllib.parse import urlparse

from minio import Minio

RAW_MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'mineru-files')
MINIO_REGION = os.getenv('MINIO_REGION', 'us-east-1')


def _parse_endpoint(endpoint: str) -> tuple[str, bool]:
    parsed = urlparse(endpoint)
    if "://" in endpoint:
        return parsed.netloc, parsed.scheme == 'https'
    return endpoint, os.getenv('MINIO_SECURE', 'false').lower() == 'true'


MINIO_ENDPOINT, MINIO_SECURE = _parse_endpoint(RAW_MINIO_ENDPOINT)


class DynamicMinioClient:
    def __init__(self):
        self._client = None
        self._signature = None

    def _get_client(self):
        try:
            from app.services.runtime_settings import load_runtime_config

            runtime = load_runtime_config(include_secrets=True).get("minio", {})
            raw_endpoint = str(runtime.get("endpoint") or RAW_MINIO_ENDPOINT)
            endpoint, secure = _parse_endpoint(raw_endpoint)
            if "://" not in raw_endpoint:
                secure = bool(runtime.get("secure", MINIO_SECURE))
            access_key = str(runtime.get("access_key") or MINIO_ACCESS_KEY)
            secret_key = str(runtime.get("secret_key") or MINIO_SECRET_KEY)
            region = str(runtime.get("region") or MINIO_REGION)
        except Exception:
            endpoint, secure = MINIO_ENDPOINT, MINIO_SECURE
            access_key, secret_key, region = MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_REGION

        signature = (endpoint, secure, access_key, secret_key, region)
        if self._client is None or self._signature != signature:
            self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure, region=region)
            self._signature = signature
        return self._client

    def __getattr__(self, name):
        return getattr(self._get_client(), name)


minio_client = DynamicMinioClient()


def ensure_bucket():
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)


def upload_file(file_obj, filename, content_type=None):
    ensure_bucket()
    minio_path = filename
    minio_client.put_object(
        MINIO_BUCKET,
        minio_path,
        file_obj,
        length=-1,
        part_size=10*1024*1024,
        content_type=content_type
    )
    return minio_path


def get_presigned_url(bucket, minio_path, expires=3600):
    return minio_client.presigned_get_object(bucket, minio_path, expires=timedelta(seconds=expires))


def get_file_url(minio_path, expires=3600):
    return get_presigned_url(MINIO_BUCKET, minio_path, expires=expires)
