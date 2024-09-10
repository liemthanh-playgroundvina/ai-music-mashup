from configs.env import settings
from ai_celery.init_broker import is_broker_running
from ai_celery.init_redis import is_backend_running
from ai_celery.celery_app import app

if not is_backend_running():
    exit()
if not is_broker_running():
    exit()

app.conf.task_routes = {
    'tasks.ai_mashup_music_task': {'queue': settings.AI_MASHUP_MUSIC},
}

from ai_celery.ai_mashup_music import ai_mashup_music_task
