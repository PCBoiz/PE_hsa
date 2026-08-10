import os
import sys

from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'

    def ready(self):
        # Keep-warm Neon (chống scale-to-zero) — CHỈ khi thực sự phục vụ request:
        # runserver hoặc WSGI (gunicorn/uwsgi). KHÔNG bật khi migrate/shell/
        # collectstatic/test để tránh luồng nền vô ích + đánh thức Neon vô cớ.
        argv = sys.argv
        prog = os.path.basename(argv[0]) if argv else ''
        is_runserver = 'runserver' in argv
        # LƯU Ý: gunicorn/uwsgi KHÔNG set os.environ['SERVER_SOFTWARE'] (chỉ set
        # trong WSGI environ per-request) → phải nhận diện qua tên tiến trình
        # argv[0] hoặc cờ env tường minh ENABLE_KEEPALIVE (đặt trong render.yaml).
        is_wsgi = (
            os.environ.get('ENABLE_KEEPALIVE') == '1'
            or prog.startswith(('gunicorn', 'uwsgi', 'uvicorn'))
            or os.environ.get('SERVER_SOFTWARE', '').startswith(('gunicorn', 'uwsgi'))
        )
        if not (is_runserver or is_wsgi):
            return
        if is_runserver:
            # runserver có reloader: spawn tiến trình cha (watcher) + con (phục vụ,
            # RUN_MAIN='true'). Chỉ bật ở con. Khi --noreload: 1 tiến trình duy
            # nhất, RUN_MAIN không set → dựa vào cờ --noreload để bật.
            if os.environ.get('RUN_MAIN') != 'true' and '--noreload' not in argv:
                return
        from common.keepalive import start_keepalive

        start_keepalive()
