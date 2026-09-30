import pymysql

pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseFeatures

# Support MySQL 8.0.x on Django 6.1+
DatabaseFeatures.minimum_database_version = (8, 0)

# PyAV 19+ compatibility patch for faster-whisper
try:
    import av
    _orig_av_open = av.open

    def _safe_av_open(*args, **kwargs):
        if "metadata_errors" in kwargs:
            try:
                return _orig_av_open(*args, **kwargs)
            except TypeError:
                kwargs.pop("metadata_errors", None)
                return _orig_av_open(*args, **kwargs)
        return _orig_av_open(*args, **kwargs)

    av.open = _safe_av_open
except Exception:
    pass

