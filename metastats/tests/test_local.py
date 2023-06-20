import metastats
import os

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

