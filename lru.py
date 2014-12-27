from collections import Iterable
cache = {}


class Cache:
    def __init__(self, lru_length=7):
        self.cache_content = {}
        self.cache_list = []
        self.lru_length = lru_length


def cached(item_name,lru_length=7):
    """
    :param item_name:
        ``item name to cached``
    :type item_name:
        ``string``
    """
    if not cache.has_key(item_name):
        cache[item_name] = Cache(lru_length)
    def wrapper_maker(get_data_from_db):
        def wrapper(self, **kargs):
            """
            :requirements:
                ```decorated function has at least one parameter```
                ```NOTICE: param of DECORATED function passed by kargs```
            """
            cache_key = kargs.values()[0]
            try:
                idx = cache[item_name].cache_list.index(cache_key)
            except ValueError:
                idx = None
            if idx is not None:
                cache[item_name].cache_list.pop(idx)
                cache[item_name].cache_list.append(cache_key)
            else:
                cache_value = get_data_from_db(self, **kargs)
                cache[item_name].cache_content[cache_key] = cache_value
                if len(cache[item_name].cache_list) > cache[item_name].lru_length:
                    del cache[item_name].cache_content[cache[item_name].cache_list[0]]
                    cache[item_name].cache_list.pop(0)
                cache[item_name].cache_list.append(cache_key)
            return cache[item_name].cache_content[cache_key]
        return wrapper
    return wrapper_maker


#old code is as follows, the above code is more generic.
#cache = {}
#cache_list = []
#LRU_LENGTH = 7
#def check_cache(cache_list, cache_key):
#    try:
#        return cache_list.index(cache_key)
#    except ValueError:
#        return None


#def fetch_data(aid):
#    article = dataquery.get_article_by_aid(aid)
#    return article


#def get_article(aid):
#    idx = check_cache(aid)
#    if idx is not None:
#        cache_list.pop(idx)
#        cache_list.append(aid)
#    else:
#        article = fetch_data(aid=aid)
#        cache[aid] = article
#        if len(cache_list) > LRU_LENGTH:
#            del cache[cache_list[0]]
#            cache_list.pop(0)
#        cache_list.append(aid)
#    return cache[aid]