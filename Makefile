download_model:
	git clone https://huggingface.co/taejunkim/allinone ./models

config:
	mkdir -p logs && touch logs/celery.log
	cp configs/env.example configs/.env
	# And add params ...

build:
	docker pull nvidia/cuda:11.8.0-runtime-ubuntu20.04
	docker build -t ai-mashup-music -f Dockerfile .

start:
	docker compose -f docker-compose.yml down
	docker compose -f docker-compose.yml up -d

start-prod:
	docker compose -f docker-compose-prod.yml down
	docker compose -f docker-compose-prod.yml up -d

stop:
	docker compose -f docker-compose.yml down

stop-prod:
	docker compose -f docker-compose-prod.yml down

# Checker
cmd-image:
	# python inference.py
	docker run -it --gpus all --rm --runtime=nvidia \
		-v .:/app \
		-v ./models:/root/.cache/torch/hub/checkpoints \
		-v ./models:/models \
		-v ./models/loaders.py:/usr/local/lib/python3.9/site-packages/allin1/models/loaders.py \
		ai-mashup-music /bin/bash

cmd-worker:
	docker compose exec worker-ai-mashup-music /bin/bash

log-worker:
	cat logs/celery.log
