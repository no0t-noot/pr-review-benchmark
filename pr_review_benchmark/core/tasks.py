import logging

from pr_review_benchmark.celery import app

logger = logging.getLogger(__name__)


@app.task
def hello_world():
    logger.info("Hello, world!")
