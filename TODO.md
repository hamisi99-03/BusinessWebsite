- [ ] Gather repo state + confirm cart integration points (models/views/urls/templates)
- [x] STEP 1: Add Cart and CartItem models to ecommerce/models.py

- [x] STEP 2: Run makemigrations + migrate

- [x] STEP 3: Add cart views to ecommerce/views.py (cart_view, add_to_cart, remove_from_cart, update_cart_item, checkout_from_cart)

- [x] STEP 4: Add cart URLs to ecommerce/urls.py

- [x] STEP 5: Create ecommerce/templates/ecommerce/cart.html
- [x] STEP 6: Add cart icon link to ecommerce/templates/ecommerce/base.html
- [x] STEP 7: Update ecommerce/templates/ecommerce/product_list.html to use Add to Cart POST form

- [x] STEP 8: Run makemigrations + migrate + check

- [x] STEP 9: Test cart routes + ensure order system remains intact
# TODO

- [ ] Inspect and update payment form view rendering logic
  - [ ] Replace `add_payment` in `ecommerce/views.py` to only supply orders with outstanding balance > 0
  - [ ] Replace `update_payment` in `ecommerce/views.py` similarly
  - [ ] Ensure required imports (`timezone`, `get_object_or_404`) exist
- [ ] Update `ecommerce/templates/ecommerce/payment_form.html`
  - [ ] Replace order dropdown HTML to show only unpaid orders (using `orders` passed from views)
  - [ ] Replace balance box HTML (`#balanceBox`)
  - [ ] Replace bottom `<script>` with new logic that pre-fills amount and updates balance box immediately
- [ ] Validate
  - [ ] Run `python manage.py check`
  - [ ] Open payment form URL and verify dropdown + balance box behavior

