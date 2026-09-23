# Deployment Testing Checklist

Use this checklist after deploying the Django application to Render with Supabase PostgreSQL and Storage.

## 1. Check Render Deployment

- [ ] Open the latest Render deployment logs.
- [ ] Confirm migration `0018` completes successfully.
- [ ] Confirm the service reports as live.
- [ ] Confirm there are no Supabase database connection errors.
- [ ] Confirm there are no Supabase Storage authentication errors.

Expected migration output includes successful `Applying ... OK` messages.

## 2. Test Product Media

- [ ] Log in using a staff account.
- [ ] Add a product with a `.jpg`, `.jpeg`, `.png`, `.gif`, or `.webp` image.
- [ ] Keep the image at or below 5 MB.
- [ ] Confirm the file appears in the Supabase `product-media` bucket.
- [ ] Open the storefront as a customer or guest.
- [ ] Confirm the product image displays correctly.
- [ ] Edit the product and upload another valid image.
- [ ] Delete an existing product image.

## 3. Test Invalid Uploads

- [ ] Try uploading a non-image file.
- [ ] Try uploading an image larger than 5 MB.
- [ ] Try using a mismatched file extension and MIME type.
- [ ] Confirm invalid uploads are rejected.
- [ ] Confirm rejected files are not stored in Supabase.

## 4. Test Customer Workflow

- [ ] Register a new customer account.
- [ ] Confirm the new account is not a staff account.
- [ ] Log out and log in again.
- [ ] Browse products and open product details.
- [ ] Add a product to the cart.
- [ ] Update the cart quantity.
- [ ] Remove an item from the cart.
- [ ] Checkout the cart.
- [ ] Confirm the cart is empty after checkout.
- [ ] Confirm an order is created.
- [ ] Confirm exactly the purchased quantity is removed from stock.
- [ ] Confirm the outstanding balance is shown correctly.
- [ ] Confirm customers cannot access staff pages.

## 5. Test Staff Workflow

- [ ] Log in using the staff account.
- [ ] Open the staff dashboard.
- [ ] View customer orders.
- [ ] Update an order status.
- [ ] Record a payment.
- [ ] Confirm debt balances update.
- [ ] View notifications after a new order.
- [ ] Add, edit, and delete a product.
- [ ] Adjust product stock.
- [ ] Add a supplier and consignment.
- [ ] Record an expense.
- [ ] Open reports and financial reports.

## 6. Test API Security

- [ ] Confirm unauthenticated management API requests are rejected.
- [ ] Confirm normal customers cannot create or modify management API records.
- [ ] Confirm staff API access works.
- [ ] Confirm staff token authentication works.
- [ ] Confirm customers can only read their own order-related API records.

## 7. Test Persistence

- [ ] Create a product and upload an image.
- [ ] Create a customer order.
- [ ] Trigger a Render redeploy.
- [ ] Confirm the product still exists.
- [ ] Confirm the order still exists.
- [ ] Confirm the image still displays.
- [ ] Confirm the image remains in Supabase Storage.

## 8. Troubleshooting

If migrations fail with a database host error:

- [ ] Confirm Render `DATABASE_URL` uses the Supabase Session Pooler URI.
- [ ] Confirm the URI uses port `5432`.
- [ ] Confirm `sslmode=require` is included.
- [ ] Remove stale `INTERNAL_DATABASE_URL`, `RENDER_DATABASE_URL`, or `POSTGRESQL_URL` variables.

If image uploads fail:

- [ ] Confirm `SUPABASE_STORAGE_ENDPOINT` is set.
- [ ] Confirm the S3 access key ID and secret key are correct.
- [ ] Confirm the bucket names are exactly `product-media` and `profile-media`.
- [ ] Confirm `SUPABASE_PRODUCT_PUBLIC_URL` uses the correct project ID.
- [ ] Confirm `product-media` is public.
- [ ] Confirm `profile-media` is private.

Never include database URLs, passwords, S3 secret keys, or service-role keys in bug reports or Git commits.
