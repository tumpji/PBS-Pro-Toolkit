import metastats
import os
import time
from unittest import mock

# for MetaStats the result should always be None


def test_cpu():
    assert metastats.MetaStats.cpu is None


def test_gpu():
    assert metastats.MetaStats.gpu is None


def test_time():
    assert metastats.MetaStats.time is None


def test_job_id():
    assert metastats.MetaStats.job_id is None


# for the extended version, the result should sometimes be filled

def test_default_cpu():
    assert metastats.MetaStatsWithDefaults.cpu == os.cpu_count()


def test_default_time():
    assert metastats.MetaStatsWithDefaults.time is None


def test_default_gpu():
    assert metastats.MetaStatsWithDefaults.gpu is None


def test_default_job_id():
    jid = metastats.MetaStatsWithDefaults.job_id
    assert jid is not None

    jid2 = metastats.MetaStatsWithDefaults.job_id
    assert jid2 is not None

    assert jid == jid2


# simulation

@mock.patch.dict(os.environ, {"PBS_NCPUS": "11"})
def test_sim_cpu():
    assert metastats.MetaStats.cpu == 11
    assert metastats.MetaStatsWithDefaults.cpu == 11


@mock.patch.dict(os.environ, {"PBS_NGPUS": "11"})
def test_sim_gpu():
    assert metastats.MetaStats.gpu == 11
    assert metastats.MetaStatsWithDefaults.gpu == 11


@mock.patch.dict(os.environ, {"TORQUE_RESC_TOTAL_WALLTIME": "123"})
def test_sim_time():
    assert metastats.MetaStats.time == 123


@mock.patch.dict(os.environ, {"PBS_JOBID": "amos"})
def test_sim_job_id():
    assert metastats.MetaStats.job_id == 'amos'
    assert metastats.MetaStatsWithDefaults.job_id == 'amos'


@mock.patch.dict(os.environ, {"TORQUE_RESC_TOTAL_WALLTIME": "120"})
def test_sim_rem_time():
    assert metastats.MetaStats.time == 120
    assert 121 >= metastats.MetaStats.time_remaining >= 119
    time.sleep(10)
    assert 111 >= metastats.MetaStats.time_remaining >= 109
