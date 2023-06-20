import os
import random
import datetime
from typing import Optional, List

JOB_START_TIME = datetime.datetime.now()


class _MetaStats(type):
    def get_env_var(cls, varname: str, cast=None, op=None):
        print(f'x is {varname}')
        print(os.environ)
        try:
            x = os.environ[varname]
            print(f'Found x {x}')
            if cast is not None:
                x = cast(x)
            if op is not None:
                x = op(x)
            print(f'Found x {x}')
        except KeyError:
            print('keyError')
            return None
        return x

    def get_env_vars(cls, varnames: List[str], cast=None, op=None):
        for varname in varnames:
            x = cls.get_env_var(varname, cast, op)
            if x is not None:
                return x
        return None

    @property
    def job_id(cls) -> Optional[str]:
        return cls.get_env_var('PBS_JOBID', str)

    @property
    def mem_gb(cls) -> Optional[int]:
        return cls.get_env_vars(['PBS_RESC_MEM', 'TORQUE_RESC_TOTAL_MEM'],
            int,
            lambda x: x // 2**30)

    @property
    def cpu(cls) -> Optional[int]:
        return cls.get_env_vars(
            ['PBS_NCPUS', 'PBS_RESC_TOTAL_PROCS', 'TORQUE_RESC_TOTAL_PROCS'],
            int)

    @property
    def gpu(cls) -> Optional[int]:
        return cls.get_env_var('PBS_NGPUS', int)

    @property
    def time(cls):
        return cls.get_env_vars(
            ['PBS_RESC_TOTAL_WALLTIME', 'TORQUE_RESC_TOTAL_WALLTIME'],
            int)

    @property
    def time_remainding(cls) -> Optional[int]:
        time = cls.time
        print(time)
        if time is None:
            return None
        else:
            delta = datetime.datetime.now() - JOB_START_TIME
            return time - int(delta.total_seconds())


class _MetaStatsWithDefaults(_MetaStats):
    @property
    def cpu(cls) -> Optional[int]:
        x = super().cpu
        if x is not None:
            return x
        return os.cpu_count()  # <- can return None

    @property
    def job_id(cls) -> str:
        x = super().job_id
        if x is not None:
            return x
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



