# `django_template/static_src`

This directory contains static files that are built or compiled by external tooling. The built version of these files are stored in `django_template/static_built`.

This directory should NOT be included in `STATICFILES_DIRS`.

If you are looking to add static files that do not require external tooling to be built or compiled, please add them in the `django_template/static` directory.
