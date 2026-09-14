# Supabase Storage Setup

The application uses two Supabase Storage buckets:

- `product-media`: public, for storefront product images.
- `profile-media`: private, for customer profile images.

## Create The Buckets

1. Open the Supabase project.
2. Open **Storage**.
3. Create a bucket named `product-media` and mark it public.
4. Create a bucket named `profile-media` and keep it private.

## Create S3 Credentials

Open the Supabase Storage S3 or access-key settings and create an access key with permission to read and write both buckets.

Do not commit the access key or secret key.

## Render Variables

Add these variables to the Render web service:

```text
SUPABASE_STORAGE_ENDPOINT=https://YOUR_PROJECT_REF.storage.supabase.co/storage/v1/s3
SUPABASE_STORAGE_ACCESS_KEY_ID=your-access-key
SUPABASE_STORAGE_SECRET_ACCESS_KEY=your-secret-key
SUPABASE_STORAGE_REGION=us-east-1
SUPABASE_PRODUCT_MEDIA_BUCKET=product-media
SUPABASE_PROFILE_MEDIA_BUCKET=profile-media
SUPABASE_PRODUCT_PUBLIC_URL=https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/product-media
```

The application uses local filesystem storage when the three storage credentials are absent, which keeps local development and automated tests working.

## Verify Storage

After redeploying Render:

- Upload a product image as staff and confirm it appears in the public storefront.
- Confirm the object appears under `product-media` in Supabase.
- Upload a profile image if the profile upload form is enabled.
- Confirm profile media is stored under `profile-media` and is not publicly accessible without a signed URL.
