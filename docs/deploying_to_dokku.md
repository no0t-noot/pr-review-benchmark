# Deploying to Dokku

## Prepare plugins

Ensure that the [Postgres plugin](https://github.com/dokku/dokku-postgres) and [Redis plugin](https://github.com/dokku/dokku-redis) are installed

```bash
# On your Dokku host:
sudo dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis
```

## Create Dokku app

```bash
# On your Dokku host:

# Create a new app with the name django-template
dokku apps:create django-template
```

## Configure Postgres service

```bash
# On your Dokku host:

# Create a new Postgres 17 service
dokku postgres:create django-template-postgres --image-version 17

# Link the Postgres service to your Dokku app
dokku postgres:link django-template-postgres django-template
```

## Configure Redis service

```bash
# On your Dokku host:

# Create a new Redis 7.2 service
dokku redis:create django-template-redis --image-version 7.2

# Link the Redis service to your Dokku app
dokku redis:link django-template-redis django-template
```

## Configure environment variables

```bash
# On your Dokku host:

# Generate and set SECRET_KEY
dokku config:set django-template SECRET_KEY=$(python3 -c "import secrets; print(''.join(secrets.choice([chr(i) for i in range(0x21, 0x7F)]) for i in range(60)));")

# Set DJANGO_SETTINGS_MODULE
dokku config:set django-template DJANGO_SETTINGS_MODULE=django_template.settings.base

# Set ALLOWED_HOSTS
dokku config:set django-template ALLOWED_HOSTS=v-django-template.app.vilantis.ai

# Set CSRF_TRUSTED_ORIGINS
dokku config:set django-template CSRF_TRUSTED_ORIGINS=https://django-template.app.vilantis.ai

# Set SENTRY_DSN
dokku config:set django-template SENTRY_DSN=https://sentry-dsn-here.com/
```

## Configure Dokku to build and release the `production` Docker image stage

```bash
# On your Dokku host:

# Add "--target production" to the build args
dokku docker-options:add django-template build "--target production"
```

## Configure git and push your app

```bash
# On your development machine:

git remote add dokku dokku@example.com:django-template
git push dokku main
```

## Configure networking

```bash
# On your Dokku host:

# Forward requests from host port 80 container port 8000
dokku ports:set django-template http:80:8000
```
