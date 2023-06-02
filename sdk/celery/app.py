from celery import Celery
import celery

# dummy broker, will be changed on celery app binding
celery_app = Celery('phoenix', broker="redis://:redispassword@localhost:6389/0")


@celery.signals.setup_logging.connect
def on_setup_logging(**kwargs):
    pass
