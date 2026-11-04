import pymysql

pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseFeatures

# Support MySQL 8.0.x on Django 6.1+
DatabaseFeatures.minimum_database_version = (8, 0)

from django.db.backends.mysql.schema import DatabaseSchemaEditor
# TiDB / MySQL compatibility: add columns first and create foreign keys separately
DatabaseSchemaEditor.sql_create_column_inline_fk = None

_orig_add_field = DatabaseSchemaEditor.add_field
def _safe_add_field(self, model, field):
    if getattr(field, 'unique', False):
        field.unique = False
        try:
            _orig_add_field(self, model, field)
        finally:
            field.unique = True
        unique_sql = self._create_unique_sql(model, [field])
        if unique_sql:
            self.deferred_sql.append(unique_sql)
    else:
        _orig_add_field(self, model, field)

DatabaseSchemaEditor.add_field = _safe_add_field

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

