.PHONY: build

build:
	docker compose build
	@echo ""
	@echo "You can now start your containers with \`make start\`"

build-no-cache:
	docker compose build --no-cache
	@echo ""
	@echo "You can now start your containers with \`make start\`"

start:
	docker compose up -d && docker attach $$(docker compose ps -q web)

stop:
	docker compose down

stop-remove-orphans:
	docker compose down --remove-orphans

restart: stop start

sh:
	docker compose run --rm web bash

shell:
	docker compose run --rm web python3 manage.py shell_plus

migrate:
	docker compose run --rm web python3 manage.py migrate

makemigrations:
	docker compose run --rm web python3 manage.py makemigrations

test:
	docker compose run --rm web python3 manage.py test --settings=pr_review_benchmark.settings.test -v=2

test-keepdb:
	docker compose run --rm web python3 manage.py test --settings=pr_review_benchmark.settings.test -v=2 --keepdb

makemessages:
	docker compose run --rm web python3 manage.py makemessages -a

compilemessages:
	docker compose run --rm web python3 manage.py compilemessages
	@echo "You will need to restart your development server for the changes to take effect."

bump-deps:
	docker compose run --rm --no-deps web sh -c 'poetry self add poetry-plugin-up && poetry up'
	docker compose run --rm --no-deps web npx --yes npm-check-updates -u --target semver
	docker compose run --rm --no-deps web npm install
	docker compose run --rm --no-deps web pre-commit autoupdate

rename:
	@# Check if PROJECT_NAME is defined
	@if [ -z "$$PROJECT_NAME" ]; then \
		echo ""; \
		echo "Usage:"; \
		echo "    make rename PROJECT_NAME=my_project_name_with_underscores"; \
		echo ""; \
		exit 1; \
	fi

	@# Get a version of PROJECT_NAME but with dashes instead of underscores
	$(eval PROJECT_NAME_KEBAB := $(subst _,-,$(PROJECT_NAME)))

	@echo ""
	@echo "This Makefile target will:"
	@echo "1.) Replace all instances of the following in files and folders:"
	@echo "  - \`pr_review_benchmark\` with \`$(PROJECT_NAME)\`"
	@echo "  - \`pr-review-benchmark\` with \`$(PROJECT_NAME_KEBAB)\`"
	@echo ""
	@echo "Proceeding in 10 seconds..."
	@echo ""

	@sleep 10

	@# Rename the pr_review_benchmark directory
	mv pr_review_benchmark $(PROJECT_NAME)

	@# Replace all instances of pr_review_benchmark with PROJECT_NAME
	grep -rl pr_review_benchmark . | xargs perl -i -pe "s/pr_review_benchmark/$(PROJECT_NAME)/g"

	@# Replace all instances of pr-review-benchmark with PROJECT_NAME_KEBAB
	grep -rl pr-review-benchmark . | xargs perl -i -pe "s/pr-review-benchmark/$(PROJECT_NAME_KEBAB)/g"

	@# Reset git index
	rm .git/index
	git reset

	@echo ""
	@echo "Done!"
