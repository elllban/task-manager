import time

import pytest

from app.core.cache import LocalCache


@pytest.fixture
def cache():
    return LocalCache(cleanup_interval=1)


class TestLocalCache:
    def test_set_and_get(self, cache):
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'

    def test_get_missing(self, cache):
        assert cache.get('nonexistent') is None

    def test_delete(self, cache):
        cache.set('key', 'val')
        cache.delete('key')
        assert cache.get('key') is None

    def test_exists(self, cache):
        cache.set('key', 'val')
        assert cache.exists('key') is True
        assert cache.exists('missing') is False

    def test_ttl_expiry(self, cache):
        cache.set('key', 'val', ttl=1)
        assert cache.get('key') == 'val'
        time.sleep(1.5)
        assert cache.get('key') is None

    def test_clear_user_session(self, cache):
        cache.set('user:1:token', 'abc')
        cache.set('user:1:key', 'def')
        cache.set('user:2:token', 'xyz')
        cache.clear_user_session(1)
        assert cache.get('user:1:token') is None
        assert cache.get('user:1:key') is None
        assert cache.get('user:2:token') == 'xyz'

    def test_clear_all(self, cache):
        cache.set('a', 1)
        cache.set('b', 2)
        cache.clear_all()
        assert cache.size == 0

    def test_size(self, cache):
        cache.set('a', 1)
        cache.set('b', 2)
        assert cache.size == 2
