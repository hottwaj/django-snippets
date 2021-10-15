from django.test import SimpleTestCase
from django_snippets.hierarchical_cache import HierarchicalCache

class HierachicalCacheTestCase(SimpleTestCase):
    def _get_cache(self, cache_name = 'default'):
        from django.core.cache import caches
        return caches[cache_name]

    def setUp(self):
        self._get_cache().clear()

    def test_get_cache(self):
        c = self._get_cache()
        self.assertIsInstance(c, HierarchicalCache)

    def test_get_underlying_caches(self):
        c = self._get_cache('locmem1')
        self.assertIsNotNone(c)
        c = self._get_cache('locmem2')
        self.assertIsNotNone(c)

    def get(self, key, **kwargs):
        return self._get_cache().get(key)

    def test_get_missing_key(self):
        self.assertIsNone(self.get('moo'))

    def set(self, key, value, **kwargs):
        return self._get_cache().set(key, value)

    def test_basic_set(self):
        key, val = 'test-1', 123
        self.assertIsNone(self.get(key))
        self.set(key, val)
        self.assertEqual(self.get(key), val)
        self.assertEqual(self._get_cache('locmem1').get(key), val)
        self.assertEqual(self._get_cache('locmem2').get(key), val)

    def test_value_propagates_from_lower_cache(self):
        key, val = 'test-2', 456
        self.assertIsNone(self.get(key))
        self._get_cache('locmem2').set(key, val)
        self.assertIsNone(self._get_cache('locmem1').get(key))
        self.assertEqual(self.get(key), val)
        self.assertEqual(self._get_cache('locmem1').get(key), val)

    def test_value_does_notpropagate_from_upper_cache(self):
        key, val = 'test-3', 789
        self.assertIsNone(self.get(key))
        self._get_cache('locmem1').set(key, val)
        self.assertIsNone(self._get_cache('locmem2').get(key))
        self.assertEqual(self.get(key), val)
        self.assertIsNone(self._get_cache('locmem2').get(key))

    def test_delete(self):
        key, val = 'test-4', 987
        self.assertIsNone(self.get(key))
        self.set(key, val)
        self.assertEqual(self.get(key), val)
        self._get_cache().delete(key)
        self.assertIsNone(self.get(key))
