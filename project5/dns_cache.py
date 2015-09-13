import sys
import collections
import threading
import json
import os

class Cache:
    """
    Cache defines a cache object and maintains a dict.
    """
    lock = threading.Lock()

    def __init__(self, cache_size):
        self.cache = collections.OrderedDict()
        # self.cache_file = open("cache.json", 'rw')
        self.__cache_size = cache_size
        self.cache_name = "cache.json"

    def loads_disk_json(self):
        with Cache.lock:
            if self.cache_name not in os.listdir("."):
                os.system("touch " + self.cache_name)
                f = open('cache.json', 'wb')
                f.write('{}')
                f.close()
            f = open('cache.json', 'rb')
            content = f.read()
            f.close()
            self.cache = json.loads(content)

    def dumps_disk_json(self):
        with Cache.lock:
            if self.cache_name not in os.listdir("."):
                os.system("touch " + self.cache_name)
            f = open('cache.json', 'wb')
            f.write(json.dumps(self.cache))
            f.close()


    def search(self, key):
        """
        search in the cache dict with the key
        :param key: in dnsserver, it is a client address, in http server it is a path
        :return:if the key exists in the cache, return the value. If not, return None
        """
        with Cache.lock:
            try:
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            except KeyError:
                return -1


    def update(self, key, value):
        """
        update the cache dict with key and value
        :param key: in dnsserver, it is a client address, in http server it is a path
        :param value: the value will be updated to, if it the key is not existed, create a new entry
        :return:
        """
        with Cache.lock:
            try:
                self.cache.pop(key)
            except KeyError:
                if sys.getsizeof(self.cache) > self.__cache_size:  # check the size of the cache, if it is full, FIFO
                    self.cache.popitem(last=False)
            self.cache[key] = value

    def delete(self, key):
        """
        delete a entry in the cache dict with the key
        :param key: in dnsserver, it is a client address, in http server it is a path
        :return:
        """
        with Cache.lock:
            try:
                del self.cache[key]
            except:
                print "no entry exists"

    def clear(self):
        """
        clear all the data in the cache
        :return:
        """
        with Cache.lock:
            self.cache = collections.OrderedDict()


