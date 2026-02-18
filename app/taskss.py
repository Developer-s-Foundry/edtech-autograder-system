from app.celery_app import celery_app

#celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
@celery_app.task(name="app.tasks.add")
def add(x, y):
    return x + y
