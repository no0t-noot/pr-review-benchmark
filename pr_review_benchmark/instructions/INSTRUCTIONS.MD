# AI Instructions: Generating Test Branches for pr-review-benchmark

## Context

This is a Django + DRF benchmark repository (`pr-review-benchmark`) designed to evaluate AI-powered PR review tools. The `main` branch contains a **clean, well-structured** products/inventory application. Your job is to create **feature branches** that introduce intentional issues of varying severity. Each branch simulates a realistic PR that a developer might submit.

## Important Rules

- **Each branch must be created from `main`** — branches are independent, not stacked.
- **Make changes look realistic** — not deliberately sloppy. Write code as if a competent but rushed developer wrote it. Include reasonable commit messages.
- **Each branch should focus on ONE category of issues** — don't mix security bugs with linting problems.
- **Add just enough good code alongside the flaws** — a PR that's 100% bad code is unrealistic. Mix in legitimate, useful changes with the intentional issues buried inside.
- **Do NOT add comments like `# BUG` or `# INTENTIONAL`** — the whole point is to see if the AI review tool catches it on its own.
- **Keep each PR reasonably sized** — aim for 50–200 lines changed per branch. Not too small (trivial to review), not too large (unrealistic for a benchmark).

---

## Base App Overview (what exists on main)

The `main` branch contains a Django project with a `products` app:

### Models
- `Category` — name, slug, description, created_at
- `Supplier` — name, contact_email, phone, address, is_active
- `Product` — name, slug, description, sku, price (DecimalField), category (FK), supplier (FK), is_active, created_at, updated_at
- `Inventory` — product (OneToOne), quantity, low_stock_threshold, last_restocked
- `PriceHistory` — product (FK), old_price, new_price, changed_at, changed_by (FK to User, nullable)

### API Endpoints (DRF)
- `GET/POST /api/products/` — list/create products (with filtering by category, price range)
- `GET/PUT/PATCH/DELETE /api/products/<id>/` — product detail
- `GET/POST /api/categories/` — list/create categories
- `GET /api/products/<id>/stock/` — check stock level
- `POST /api/products/<id>/update-price/` — update price (logs to PriceHistory)
- `POST /api/products/<id>/restock/` — add inventory quantity

### Views (template-based)
- `/products/` — product list page
- `/products/<slug>/` — product detail page
- `/dashboard/` — inventory dashboard with aggregation stats

### Patterns and conventions used in the base app
- Class-based views everywhere (both DRF ViewSets and Django CBVs)
- Serializers handle all validation in API endpoints
- `select_related` / `prefetch_related` used properly in querysets
- Settings loaded from environment variables via `os.environ.get()`
- Tests use `pytest` + `pytest-django` with factory_boy for test data
- All models use `__str__` and have `Meta.ordering`
- URLs follow RESTful conventions

---

## Branches to Create

### Branch: `pr/package-upgrade`

**Purpose:** Test if the tool can identify a simple, low-risk dependency bump.

**What to do:**
- Update `Django` version in `requirements.txt` from current to the next minor release (e.g., 4.2.x → 4.2.y)
- Update `djangorestframework` similarly
- Do NOT change any code — only `requirements.txt`
- Commit message: `chore: bump Django and DRF to latest patch versions`

**What a good review tool should do:**
- Recognize this as a low-risk change
- Optionally flag if the upgrade includes any breaking changes or security fixes
- NOT waste time generating a detailed code review — it's just version bumps

---

### Branch: `pr/linting-issues`

**Purpose:** Test basic code quality detection.

**What to do:**
Add a new utility module `products/utils.py` with helper functions for the product app. Inside this file, introduce:

- 2–3 unused imports at the top (e.g., `import json`, `from datetime import timedelta`)
- One variable assigned but never used
- Inconsistent naming: mix `snake_case` and `camelCase` in the same file (e.g., `calculateDiscount` alongside `format_price`)
- One bare `except:` clause (catching all exceptions)
- A function with 6+ parameters (code smell)
- One f-string that doesn't actually use any interpolation (e.g., `f"No discount applied"`)
- Missing docstrings on public functions

Also modify an existing view to import and use ONE of the new utility functions, so the PR has a purpose beyond the utility file.

Commit message: `feat: add product utility helpers for formatting and discounts`

**What a good review tool should do:**
- Flag unused imports, unused variable, bare except
- Note naming inconsistency
- Suggest the f-string is unnecessary
- Possibly note the function with too many parameters

---

### Branch: `pr/dead-code`

**Purpose:** Test detection of unreachable and unused code.

**What to do:**
Add a new management command `products/management/commands/cleanup_products.py` that archives old products. Inside it:

- A function that has a `return` statement followed by additional logic
- An `if/elif` chain where one branch can never be reached (e.g., checking `if x > 10` then `elif x > 5` then `elif x > 20` — the last is unreachable if you've already caught > 10)
- A helper function defined in the file that is never called
- A commented-out block of code (5+ lines) left in

Commit message: `feat: add management command for archiving stale products`

**What a good review tool should do:**
- Flag the unreachable code after return
- Ideally flag the unreachable elif branch
- Note the unused helper function
- Suggest removing commented-out code

---

### Branch: `pr/missing-error-handling`

**Purpose:** Test detection of error-prone code paths.

**What to do:**
Add a new API endpoint `POST /api/products/<id>/import-from-supplier/` that fetches product data from an "external" supplier API and updates the local product. Implement it with:

- `requests.get()` to an external URL with no `try/except` around it
- No timeout parameter on the requests call
- Accessing response JSON with direct key access (`data["price"]`) instead of `.get("price")`
- Accessing a queryset result with `.first()` but then using it without a None check
- Division operation that could cause `ZeroDivisionError` (e.g., calculating average price: `total / count` where count could be 0)
- No validation on the external data before saving to the database

Also add `requests` to `requirements.txt` if not already there.

Commit message: `feat: add supplier data import endpoint`

**What a good review tool should do:**
- Flag missing try/except around external HTTP call
- Flag missing timeout on requests.get()
- Flag unsafe dictionary access
- Flag potential None dereference
- Flag potential ZeroDivisionError
- Note missing input validation

---

### Branch: `pr/no-tests`

**Purpose:** Test if the tool notices missing test coverage for new functionality.

**What to do:**
Add a significant new feature — a discount system:

- New model: `Discount` — name, discount_type (percentage/fixed), value, min_purchase_amount, start_date, end_date, is_active
- New serializer: `DiscountSerializer` with validation logic (e.g., percentage must be 0–100, start_date before end_date)
- New endpoint: `GET/POST /api/discounts/`
- New method on Product model: `get_discounted_price(discount)` with actual calculation logic
- Add a migration file for the new model

Do NOT add any tests whatsoever — no test file, no test class, nothing.

Commit message: `feat: implement discount system with API endpoints`

**What a good review tool should do:**
- Clearly flag that new models, serializers, views, and business logic were added with zero tests
- Ideally note which specific parts need testing (the validation logic, the price calculation)

---

### Branch: `pr/hardcoded-values`

**Purpose:** Test detection of configuration and security anti-patterns.

**What to do:**
Add a product export feature — an endpoint that generates a CSV report and optionally sends it via email. Introduce:

- A hardcoded SMTP server address: `smtp_server = "smtp.company-internal.com"`
- A hardcoded API key string: `API_KEY = "sk_live_a1b2c3d4e5f6g7h8i9j0"` (make it look realistic but fake)
- Magic numbers: tax rate as `price * 0.21`, shipping threshold as `if total > 50`, max export rows as `products[:1000]`
- Hardcoded file path: `/tmp/exports/products.csv`
- A comment that says `# TODO: move to settings` next to one of the hardcoded values (but not the others)

Commit message: `feat: add product CSV export with email delivery`

**What a good review tool should do:**
- Flag the API key as a secret in source code (critical)
- Flag hardcoded SMTP server, file path
- Note magic numbers should be constants or settings
- Possibly note the TODO as unresolved

---

### Branch: `pr/inconsistent-pattern`

**Purpose:** Test if the tool detects architectural inconsistency with the existing codebase.

**What to do:**
Add a new endpoint for bulk product operations. Deliberately break the patterns established in the base app:

- Use a **function-based view** with `@api_view` decorator instead of a ViewSet (base app uses CBVs everywhere)
- Do **manual request.data validation** with if/else instead of using a serializer (base app uses serializers for all validation)
- Write a **raw SQL query** using `cursor.execute()` for one operation instead of using the ORM (base app uses ORM exclusively)
- Use `JsonResponse` instead of DRF's `Response` in one place

Make the actual functionality correct — the code works, it just doesn't follow the project's conventions.

Commit message: `feat: add bulk product update endpoint`

**What a good review tool should do:**
- Note the FBV vs CBV inconsistency
- Flag manual validation instead of serializer usage
- Flag raw SQL when ORM would work
- Note mixing JsonResponse with DRF Response
- These are style/architecture issues, not bugs — the tool should frame them appropriately

---

### Branch: `pr/n-plus-one`

**Purpose:** Test detection of database query performance issues.

**What to do:**
Add a new "product catalog" view that renders a rich product listing page. In the view:

- Query `Product.objects.all()` (or `.filter(is_active=True)`) WITHOUT `select_related('category', 'supplier')` or `prefetch_related`
- In the template (or serializer if API), access `product.category.name` and `product.supplier.name` — this triggers N+1 queries
- Add a "related products" section that, for each product, queries `Product.objects.filter(category=product.category).exclude(id=product.id)[:3]` inside a loop — another N+1
- Add a product statistics endpoint that computes `Inventory.objects.filter(product__category=category).aggregate(...)` inside a loop over categories instead of using a single annotated query

Commit message: `feat: add rich product catalog view with related products`

**What a good review tool should do:**
- Flag the missing select_related/prefetch_related
- Identify the queries inside loops as N+1 patterns
- Suggest using annotation/aggregation instead of looping
- Possibly estimate the query count impact

---

### Branch: `pr/security-issues`

**Purpose:** Test detection of security vulnerabilities.

**What to do:**
Add a product search feature and admin product management. Introduce:

- **SQL injection**: A search endpoint that uses `cursor.execute(f"SELECT * FROM products_product WHERE name LIKE '%{query}%'")` — string interpolation in SQL
- **XSS vector**: A view that renders user search input back in the template using `mark_safe()` or `|safe` filter without sanitization
- **Missing authentication**: A new endpoint that modifies product data (e.g., bulk delete) but is missing `permission_classes` or `@login_required` — anyone can call it
- **IDOR (Insecure Direct Object Reference)**: An endpoint that lets a user access/modify any product by ID without checking ownership or permissions beyond basic auth
- **Insecure deserialization**: Using `pickle.loads()` on user-provided data (e.g., importing a "config" from a file upload)

Each vulnerability should be in a separate function/view so they're independently testable.

Commit message: `feat: add product search and admin management tools`

**What a good review tool should do:**
- Flag SQL injection as critical/high severity
- Flag XSS as critical/high severity
- Flag missing auth on destructive endpoint
- Flag pickle.loads on user input as critical
- Note the IDOR issue (this is harder — many tools miss it)

---

### Branch: `pr/logic-error`

**Purpose:** Test detection of business logic bugs.

**What to do:**
Add a pricing and inventory management feature with subtle logic errors:

- **Off-by-one in stock check**: `if inventory.quantity > low_stock_threshold` instead of `>=` — when quantity equals threshold, it doesn't trigger the low-stock alert
- **Wrong discount calculation**: Percentage discount implemented as `price - (price * discount / 10)` instead of `/ 100` — makes a 20% discount actually an 200% discount
- **Reversed comparison**: Sorting products by price ascending but using `-price` (descending), or a "cheapest products" endpoint that actually returns the most expensive
- **Integer division issue**: Using `//` where `/` was needed, truncating decimal results in a price calculation
- **Boolean logic error**: `if not product.is_active and not product.category.is_active` when it should be `or` — only catches products where BOTH are inactive instead of either

Keep each error in a distinct function so they're independently identifiable.

Commit message: `feat: add advanced pricing rules and stock management alerts`

**What a good review tool should do:**
- Catch the discount calculation error (most obvious)
- Catch the reversed sort (moderate difficulty)
- Catch the off-by-one in the boundary check
- Catch the and/or logic error (harder)
- The integer division issue is subtle — impressive if caught

---

### Branch: `pr/race-condition`

**Purpose:** Test detection of concurrency issues.

**What to do:**
Add a "purchase" endpoint that decrements inventory when a product is bought. Implement it with a classic race condition:

```python
# The wrong way:
inventory = Inventory.objects.get(product_id=product_id)
if inventory.quantity >= requested_quantity:
    inventory.quantity -= requested_quantity
    inventory.save()
```

Instead of the safe way (`F()` expressions or `select_for_update()`).

Also add:
- A "transfer stock" function that reads from one inventory, writes to another, without wrapping in `transaction.atomic()`
- A "daily sales counter" that does read-modify-write on a counter field without any locking

Commit message: `feat: add purchase and stock transfer endpoints`

**What a good review tool should do:**
- Flag the read-modify-write without F() expressions or select_for_update
- Flag the missing transaction.atomic on the transfer
- Note the counter update race condition
- Suggest specific Django solutions (F expressions, select_for_update, atomic)

---

### Branch: `pr/breaking-api-change`

**Purpose:** Test if the tool detects backward-incompatible API changes.

**What to do:**
Modify the existing `ProductSerializer`:

- Rename field `price` → `unit_price` (breaking for existing API consumers)
- Remove `supplier` field from the response entirely
- Change `category` from returning the category ID to returning a nested object `{ "id": 1, "name": "Electronics" }` (changes the response shape)
- Change the `POST /api/products/` endpoint to require a new mandatory field `warehouse_code`
- Change the status code of the create endpoint from 201 to 200

Do NOT add any API versioning or deprecation notices.

Commit message: `refactor: update product serializer with improved field structure`

**What a good review tool should do:**
- Flag field rename as a breaking change
- Flag field removal as a breaking change
- Note the response shape change on category
- Flag the new required field on create
- Note the status code change
- Suggest API versioning or migration path

---

### Branch: `pr/architectural-drift`

**Purpose:** Test if the tool detects deviations from project architecture.

**What to do:**
Add a "product analytics" feature that breaks several architectural patterns:

- **Direct DB access in a view**: Write raw SQL or direct ORM queries in a Django view/DRF view instead of going through a model manager or service function
- **Business logic in serializer**: Put complex pricing calculation logic inside a serializer's `validate()` method instead of in the model or a service layer
- **Duplicate dependency**: Add `python-dateutil` to requirements.txt and use `dateutil.parser.parse()` in code, when `django.utils.dateparse` or Python's built-in `datetime.fromisoformat()` already handles the use case
- **Fat view**: Put 50+ lines of logic directly in a view method (data fetching, processing, formatting, emailing) instead of breaking into service functions
- **Bypassing the ORM for no reason**: Use `cursor.execute("UPDATE products_product SET ...")` for a simple update that `Product.objects.filter(...).update(...)` would handle

Commit message: `feat: add product analytics and reporting`

**What a good review tool should do:**
- Note the fat view anti-pattern
- Flag the unnecessary raw SQL
- Flag the duplicate dependency
- Note business logic in the wrong layer
- These require understanding the project's established patterns — hardest for AI tools

---

### Branch: `pr/migration-risk`

**Purpose:** Test if the tool catches risky database migrations.

**What to do:**
Add a migration that introduces schema changes with production risks:

- Add a `NOT NULL` field to `Product` without a default value (will fail if table has existing rows)
- Add a `unique=True` constraint to an existing field (`sku`) via migration — could fail if duplicates exist
- Rename a field that other parts of the code reference by the old name
- Add a large index on a text field (could lock the table on large datasets)
- Remove a field that existing code still references somewhere (leave one stale reference in a template or serializer)

Commit message: `refactor: tighten product schema constraints and add indexes`

**What a good review tool should do:**
- Flag the non-nullable field without default as production-risky
- Flag the unique constraint on potentially non-unique data
- Note the field rename could break existing code
- Note the stale reference to the removed field
- Possibly note table locking risks on large tables

---

## Evaluation Process

After creating all branches:

1. Open a PR from each branch to `main`
2. Enable each AI review tool on the repo
3. Let the tool review each PR
4. For each PR, record:
   - **Issues found**: What did the tool flag?
   - **Issues missed**: What did the tool NOT flag that it should have?
   - **False positives**: What did the tool flag that isn't actually an issue?
   - **Quality of explanation**: Was the reasoning clear and technically correct?
   - **Fix suggestions**: Did it suggest concrete, correct fixes?
   - **Response time**: How long until the review appeared?

## Naming Convention

All branches follow the pattern `pr/<category>`, e.g.:
- `pr/package-upgrade`
- `pr/linting-issues`
- `pr/dead-code`
- `pr/missing-error-handling`
- `pr/no-tests`
- `pr/hardcoded-values`
- `pr/inconsistent-pattern`
- `pr/n-plus-one`
- `pr/security-issues`
- `pr/logic-error`
- `pr/race-condition`
- `pr/breaking-api-change`
- `pr/architectural-drift`
- `pr/migration-risk`