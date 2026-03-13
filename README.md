# MasterMinds Expense Management Portal

Flask-based expense management portal with responsive UI, friend management, profile onboarding, and modern client-side interactions.

## Tech Stack

- Backend: Python, Flask, SQLite
- Frontend: HTML, CSS, Vanilla JS
- UI Enhancements: responsive design, dark/light theme, loading skeletons, live form validation

## Current Features

- User signup and login
- Profile details dashboard
- Friend search and request workflow
- Accept/reject friend requests
- Upload and view profile picture
- Responsive mobile-first UI
- Theme toggle (dark/light) persisted in browser local storage

## Project Structure (Scalable Frontend Pattern)

- `templates/base.html`: common layout and shared shell
- `templates/login.html`: login page
- `templates/signup.html`: signup page
- `templates/dashboard.html`: dashboard page
- `templates/friends.html`: friends page UI
- `templates/partials/ui_macros.html`: reusable Jinja components (card, form field, modal)
- `static/css/main.css`: global design tokens and responsive styles
- `static/js/main.js`: app-wide JS (flash handling + theme toggle)
- `static/js/components.js`: reusable modal behavior and component helpers
- `static/js/auth.js`: signup validation logic (phone, UPI, password match)
- `static/js/friends.js`: search, skeleton loading, tab behavior, request actions

This split keeps page-specific logic isolated, making new pages/features easier to add.

## Reusable Component Pattern

Import macros inside templates:

```jinja2
{% from 'partials/ui_macros.html' import card, form_field, modal %}
```

Extended reusable macros now available:

- `page_header(title, subtitle)`: standard heading with optional action slot
- `stats_card(label, value, helper, tone)`: compact metrics cards
- `data_table(headers)`: reusable table shell with caller rows
- `empty_state(title, description)`: shared no-data UI

Use card wrapper:

```jinja2
{% call card('Section Title', 'Optional subtitle') %}
	<!-- section content -->
{% endcall %}
```

Use page header with actions:

```jinja2
{% call page_header('Friends and Requests', 'Manage your network') %}
	<button class="btn btn-ghost" type="button">Action</button>
{% endcall %}
```

Use form field macro:

```jinja2
{{ form_field('email', 'Email', field_type='email', placeholder='you@example.com', required=true) }}
```

Use reusable modal:

```jinja2
<button type="button" data-modal-open="myModal">Open</button>

{% call modal('myModal', 'My Modal Title', 'Optional description') %}
	<p>Modal content</p>
{% endcall %}
```

`static/js/components.js` handles opening/closing via `data-modal-open` and `data-modal-close`.

## Setup

1. Open terminal in project root.
2. Install dependencies in your active environment:

```bash
python -m pip install -r requirements.txt
```

If your environment is conda `tf_env`, you can run:

```bash
C:/Users/sharm/anaconda3/Scripts/conda.exe run -p C:/Users/sharm/.conda/envs/tf_env python -m pip install -r requirements.txt
```

## Run Locally

```bash
python app.py
```

Or with your conda path:

```bash
C:/Users/sharm/anaconda3/Scripts/conda.exe run -p C:/Users/sharm/.conda/envs/tf_env python app.py
```

Visit:

- `http://127.0.0.1:5000`

## What To Test Now (End-to-End)

1. Signup with valid details and optional image upload.
2. Confirm live validation on signup:
	- Phone must be exactly 10 digits
	- UPI must follow `name@bank`
	- Confirm password must match password
3. Login with the new account.
4. Open friends page and search users:
	- Observe loading skeleton while searching
	- Send request and verify feedback
5. Accept/reject pending requests and confirm UI updates.
6. Toggle dark/light mode and refresh page to verify persistence.

## Scalability Notes For Next Features

1. Add one JS module per page/feature under `static/js/`.
2. Keep shared styles in `main.css`; add sectioned component blocks for new features.
3. Create reusable Jinja partials for repeated UI pieces (cards, tables, modals).
4. For larger backend growth, migrate to Flask Blueprints (`auth`, `friends`, `expenses`).
5. Add automated tests using `pytest` and `Flask` test client before major feature expansion.