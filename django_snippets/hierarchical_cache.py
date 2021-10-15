from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT


class HierarchicalCache(BaseCache):
    """Django-compatible hierarchical cache."""

    def __init__(self, location, params):
        """Initialize HierarchicalCache instance.

        :param list[str] cache_names: list of names of the caches that should be used by this hierarchical cache

        """
        super().__init__(params)
        self.location = location
        options = params.get('OPTIONS', {})
        if 'CACHE_NAMES' not in options:
            raise ValueError('OPTIONS.CACHE_NAMES not provided')
        self.cache_names = options['CACHE_NAMES']

    def _get_cache(self, cache_name):
        from django.core.cache import caches
        return caches[cache_name]

    def _iter_caches(self):
        for cname in self.cache_names:
            yield self._get_cache(cname)

    def _reverse_iter_caches(self):
        for cname in self.cache_names[::-1]:
            yield self._get_cache(cname)

    def add(self, key, value, **kwargs) -> bool:
        """Set a value in the cache if it is not there already"""
        value_added = True
        for cache in self._reverse_iter_caches():
            value_added &= cache.add(key, value, *args)
        return value_added

    def get(self, key, default = None, **kwargs):
        """Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.

        :param key: key for item
        :param default: return value if key is missing (default None)
        :return: value for item if key is found else default"""
        missed_caches = []
        for cache in self._iter_caches():
            result = cache.get(key, default = default, **kwargs)
            if result != default:
                # populate missed caches
                for mcache in missed_caches[::-1]:
                    mcache.set(key, result)
                break
            else:
                missed_caches.append(cache)

        return result

    def set(self, key, value, **kwargs) -> bool:
        """Set a value in the cache.  Return True if successful"""
        for cache in self._reverse_iter_caches():
            cache.set(key, value, **kwargs)  # some underlying caches return None i.e. not T/F
        return True # so return True in all cases. bit crap!

    def delete(self, key, **kwargs) -> bool:
        """Delete a key from the cache, failing silently.

        :param key: key for item
        :return: True if item was deleted"""
        value_deleted = True
        for cache in self._reverse_iter_caches():
            value_deleted &= cache.delete(key, **kwargs)
        return value_deleted

    def delete_many(self, keys, **kwargs):
        """Delete a bunch of values in the cache at once. """
        for cache in self._reverse_iter_caches():
            cache.delete_many(keys, **kwargs)

    def has_key(self, key, **kwargs) -> bool:
        """Returns True if the key is in the cache and has not expired.
        :return: True if key is found
        """
        return any([cache.has_key(key, **kwargs) for cache in self._iter_caches()])

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None) -> bool:
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """
        return all([cache.touch(key, timeout = timeout, **kwargs)
                    for cache in self._iter_caches()])


    def clear(self):
        """Remove *all* values from the cache at once."""
        for cache in self._reverse_iter_caches():
            cache.clear()