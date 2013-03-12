# -*- coding: utf-8 -*-
import logging
import inspect
import os


def need_to_log(total_time):
    log_min_time = os.environ.get('SA_MIN_LOG_SLOW_SQL', 3)
    if total_time >= float(log_min_time):
        return True
    return False


def get_arsia_frame():
    ignored_packages = ['SQLAlchemy', 'affinitic.db', 'dogpile.cache',
                        'dogpile.core']
    for frame, file_path, linenumber, fname, line, i in inspect.stack()[1:]:
        if [ignored for ignored in ignored_packages if ignored in file_path]:
                continue
        return frame


def log_long_query(engine, total_time, statement, parameters):
    if not need_to_log(total_time):
        return
    frame = get_arsia_frame()
    if frame is not None:
        function = "%s()" % frame.f_code.co_name
        file_line = "%s:%s" % (frame.f_code.co_filename, frame.f_lineno)
    else:
        function = file_line = 'UNKNOWN'
    instance_name = os.path.split(os.environ.get('INSTANCE_HOME', '.'))[-1]
    dbdriver = "%s@%s" % (engine.url.drivername, engine.url.host)
    logger = logging.getLogger('affinitic.db')
    logger.warning("Long query: %ss \n %s \n params: %s \n db: %s \n instance: %s \n function: %s \n file/line: %s" % (total_time, statement, repr(parameters), dbdriver, instance_name, function, file_line))
