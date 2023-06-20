import os
from os import environ
import random
import datetime


class _MetaStats(type):
    def get_env_var(cls, varname, cast=None, op=None):
        try:
            x = environ[varname]
            if cast is not None:
                x = cast(x)
            if op is not None:
                x = op(x)
            return x
        except KeyError:
            return None

    @property
    def job_id(cls):
        cls.get_env_var('PBS_JOBID', str)

    @property
    def cpu(cls):
        cls.get_env_var('PBS_NCPUS', int)

    @property
    def gpu(cls):
        cls.get_env_var('PBS_NGPUS', int)

    @property
    def time(cls):
        cls.get_env_var('PBS_RESC_TOTAL_WALLTIME', int)


class _MetaStatsWithDefaults(_MetaStats):
    @property
    def cpu(cls):
        if super().cpu is None:
            return os.cpu_count()

    @property
    def job_id(cls):
        if super().job_id is None:
            if not hasattr(cls, '_cached_job_id'):
                t = str(datetime.datetime.utcnow())
                t = t.replace(' ', '_')
                r = "{:0>13}".format(random.randint(0, 10**13 - 1))
                setattr(cls, '_cached_job_id', f'local_{t}_{r}')
            return cls._cached_job_id


class MetaStats(metaclass=_MetaStats):
    pass


class MetaStatsWithDefaults(metaclass=_MetaStatsWithDefaults):
    pass

