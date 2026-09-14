import os
from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseMediaStorage(Storage):
    """Use Supabase S3 storage when configured, with local fallback for development."""

    def __init__(self, bucket_name, public=False):
        self.bucket_name = os.environ.get(
            f"SUPABASE_{bucket_name.upper().replace('-', '_')}_BUCKET",
            bucket_name,
        )
        self.public = public
        self._backend = self._build_backend()

    def _build_backend(self):
        endpoint = os.environ.get('SUPABASE_STORAGE_ENDPOINT')
        access_key = os.environ.get('SUPABASE_STORAGE_ACCESS_KEY_ID')
        secret_key = os.environ.get('SUPABASE_STORAGE_SECRET_ACCESS_KEY')

        if not all((endpoint, access_key, secret_key)):
            return FileSystemStorage(
                location=settings.MEDIA_ROOT,
                base_url=settings.MEDIA_URL,
            )

        from storages.backends.s3 import S3Storage

        return S3Storage(
            access_key=access_key,
            secret_key=secret_key,
            bucket_name=self.bucket_name,
            endpoint_url=endpoint,
            region_name=os.environ.get('SUPABASE_STORAGE_REGION', 'us-east-1'),
            addressing_style='path',
            querystring_auth=not self.public,
            file_overwrite=False,
        )

    def _open(self, name, mode='rb'):
        return self._backend.open(name, mode)

    def _save(self, name, content):
        return self._backend.save(name, content)

    def delete(self, name):
        return self._backend.delete(name)

    def exists(self, name):
        return self._backend.exists(name)

    def listdir(self, path):
        return self._backend.listdir(path)

    def size(self, name):
        return self._backend.size(name)

    def url(self, name):
        if self.public and os.environ.get('SUPABASE_PRODUCT_PUBLIC_URL'):
            return (
                f"{os.environ['SUPABASE_PRODUCT_PUBLIC_URL'].rstrip('/')}/"
                f"{quote(name, safe='/')}"
            )
        return self._backend.url(name)
