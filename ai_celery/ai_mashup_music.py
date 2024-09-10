import json
import logging
import os

from celery import Task
from ai_celery.celery_app import app
from configs.env import settings
from ai_celery.common import Celery_RedisClient, CommonCeleryService

import torch
from interface import mashup_music


class AIMashupMusicTask(Task):
    """
    Abstraction of Celery's Task class to support AI Mashup Music
    """
    abstract = True

    def __init__(self):
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


@app.task(
    bind=True,
    base=AIMashupMusicTask,
    name="{query}.{task_name}".format(
        query=settings.AI_QUERY_NAME,
        task_name=settings.AI_MASHUP_MUSIC
    ),
    queue=settings.AI_MASHUP_MUSIC
)
def ai_mashup_music_task(self, task_id: str, data: bytes, task_request: bytes, file: bytes):
    """
    Service AI Mashup Music tasks

    task_request example:
        {'master_audio': None, 'slave_audio': None, 'mode': {'mode': 'auto'}, 'config': {'match_key': false, 'match_bpm': true}}

    file:
        {'master_audio': 'static/public/ai_cover_gen/a.mp3', 'slave_audio': 'static/public/ai_cover_gen/b.mp3'}

    """
    print(f"============= AI Mashup Music task {task_id}: Started ===================")
    try:
        # Load data
        data = json.loads(data)
        request = json.loads(task_request)
        file = json.loads(file)
        Celery_RedisClient.started(task_id, data)

        # Check task removed
        Celery_RedisClient.check_task_removed(task_id)

        # Request
        mode = request['mode']['mode']
        match_key = request['config']['match_key']
        match_bpm = request['config']['match_bpm']

        # Predict
        master_audio = file.get('master_audio').split("/")[-1]
        master_audio = "/app/static/public/ai_cover_gen/" + master_audio

        slave_audio = file.get('slave_audio').split("/")[-1]
        slave_audio = "/app/static/public/ai_cover_gen/" + slave_audio

        output, metadata_gpt, song_structure, time_execute = mashup_music(mode, master_audio, slave_audio, match_key, match_bpm)

        # Save s3
        urls = {
            "mashup_audio": CommonCeleryService.fast_upload_s3_files([output], settings.AI_MASHUP_MUSIC),
            "song_structure": song_structure
        }

        # Successful
        metadata = [
            {
                "task": settings.AI_MASHUP_MUSIC,
                "tool": "local",
                "model": "madmom",
                "usage": None,
                "time_execute": time_execute,
            },
            metadata_gpt
        ]
        response = {"urls": urls, "metadata": metadata}
        Celery_RedisClient.success(task_id, data, response)

        try:
            os.remove(output)
        except:
            pass

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        import gc;
        gc.collect()

        return

    except ValueError as e:
        logging.getLogger().error(str(e), exc_info=True)
        err = {'code': "400", 'message': str(e).split('!')[0].strip()}
        Celery_RedisClient.failed(task_id, data, err)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        import gc;
        gc.collect()

        return

    except Exception as e:
        logging.getLogger().error(str(e), exc_info=True)
        err = {'code': "500", 'message': "Internal Server Error"}
        Celery_RedisClient.failed(task_id, data, err)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

        import gc;
        gc.collect()

        return
