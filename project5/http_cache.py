import sys
import collections
import threading
import hashlib
import gzip
import os


class Cache:
    """
    Cache defines a cache object and maintains a dict.
    """
    lock = threading.Lock()

    def __init__(self):
        # self.cache = collections.OrderedDict()
        # self.__cache_size = cache_size
        self.page = []
        self.dir_name = "cache"

    def load_from_disk(self):
        with Cache.lock:
            # for root, dir, filenames in os.walk(self.dir_name):
            #     print filenames
            #     self.page = filenames
            self.page = os.listdir(self.dir_name)

    def new_dir(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name)

    def search(self, path):
        """
        search in the cache dict with the key
        :param key: in dnsserver, it is a client address, in http server it is a path
        :return:if the key exists in the cache, return the value. If not, return None
        """
        with Cache.lock:
            # try:
            # value = self.page.pop(key)
            # self.page[key] = value
            # return value
            # except KeyError:
            # return -1
            path_md5 = self._get_path_md5(path)
            if path_md5 in self.page:
                self.page.remove(path_md5)
                self.page.append(path_md5)
                try:
                    f = gzip.open(self.dir_name + "/" + path_md5, "rb")
                    content = f.read()
                    f.close()
                    return content
                except:
                    self.page.remove(path_md5)
                    return -1
            else:
                return -1

    def update(self, path, content):
        """
        update the cache dict with key and value
        :param key: in dnsserver, it is a client address, in http server it is a path
        :param value: the value will be updated to, if it the key is not existed, create a new entry
        :return:
        """
        with Cache.lock:
            # try:
            # self.cache.pop(key)
            # except KeyError:
            # if sys.getsizeof(self.cache) > self.__cache_size:  # check the size of the cache, if it is full, FIFO
            # self.cache.popitem(last=False)
            # self.cache[key] = value
            path_md5 = self._get_path_md5(path)
            if path_md5 in self.page:
                self.page.remove(path_md5)
                self._page_push(path_md5, content)
            else:
                if not os.path.exists(self.dir_name):
                    os.mkdir(self.dir_name)
                    self._page_push(path_md5, content)
                elif self.size_not_full():
                    self._page_push(path_md5, content)
                else:
                    self._page_pop()
                    self._page_push(path_md5, content)

    def size_not_full(self):
        """
        need revising
        :return:
        """
        # return len(self.page) < 2000
        curr_size = 0
        curr_size = sum(os.path.getsize(self.dir_name + "/" + f) for f in os.listdir(self.dir_name) if os.path.isfile(self.dir_name + "/" + f))
        # print "curr_size", curr_size
        return curr_size < (1024 * 1024 * 10 - 500 * 1024)


    def _page_push(self, path_md5, content):

        """
        psuh the item into the look_up page and zip the content on the disk
        :return:
        """
        self.page.append(path_md5)
        f = gzip.open(self.dir_name + "/" + path_md5, 'wb')
        f.write(content)
        f.close()
        self.page.append(path_md5)


    def _page_pop(self):

        """

        :return:
        """
        path_md5 = self.page.pop()
        try:
            os.remove(self.dir_name + "/" + path_md5)
        except:
            pass


    def _get_path_md5(self, path):

        """
        get the md5 of the path
        :param path: path sent by the client
        :return: the md5 value of input path
        """

        h = hashlib.md5()
        h.update(path)
        return h.hexdigest()


