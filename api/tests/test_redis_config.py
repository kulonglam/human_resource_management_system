"""Redis configuration helpers."""

from django.test import SimpleTestCase, override_settings

from api.redis_config import (
    build_cache_config,
    build_q_cluster_config,
    infrastructure_snapshot,
    parse_redis_url,
)


class RedisConfigTests(SimpleTestCase):
    def test_parse_redis_url(self):
        parsed = parse_redis_url('redis://red-abc123:6379/2')
        self.assertEqual(parsed['host'], 'red-abc123')
        self.assertEqual(parsed['port'], 6379)
        self.assertEqual(parsed['db'], 2)

    def test_parse_redis_url_with_auth(self):
        parsed = parse_redis_url('rediss://user:secret@redis.example.com:6380/1')
        self.assertEqual(parsed['username'], 'user')
        self.assertEqual(parsed['password'], 'secret')
        self.assertTrue(parsed['ssl'])

    def test_build_cache_config_uses_locmem_without_redis(self):
        config = build_cache_config(None)
        self.assertIn('LocMemCache', config['default']['BACKEND'])

    def test_build_cache_config_uses_redis_when_configured(self):
        config = build_cache_config('redis://localhost:6379/0')
        self.assertEqual(config['default']['BACKEND'], 'django_redis.cache.RedisCache')

    def test_build_q_cluster_uses_orm_fallback_without_redis(self):
        cluster = build_q_cluster_config(None, workers=2)
        self.assertEqual(cluster['orm'], 'default')
        self.assertNotIn('redis', cluster)

    def test_build_q_cluster_uses_redis_when_configured(self):
        cluster = build_q_cluster_config('redis://localhost:6379/0', workers=3)
        self.assertEqual(cluster['workers'], 3)
        self.assertEqual(cluster['redis']['host'], 'localhost')
        self.assertNotIn('orm', cluster)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'redis-config-test',
            },
        },
    )
    def test_ping_cache_with_locmem(self):
        from api.redis_config import ping_cache

        ok, message = ping_cache()
        self.assertTrue(ok)
        self.assertEqual(message, 'ok')

    def test_infrastructure_snapshot(self):
        self.assertEqual(infrastructure_snapshot('redis://x')['queue_backend'], 'redis')
        self.assertEqual(infrastructure_snapshot(None)['cache_backend'], 'locmem')
