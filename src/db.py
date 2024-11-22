import redis


class Database(object):
    """ Redis database object
    """
    def __init__(self, host="127.0.0.1", port=6379, db=0):
        self.rdb = redis.Redis( host, port, db)

    def set_values(self,values):
        """ Set one key value
        :param key:
        :param value: dict: set of key value pairs
        :return:
        """
        for key,val in values:
            self.rdb.sadd(key,val)

    def get_values(self, key):
        return self.rdb.smembers(key)


    def getall(self, station):
        data = self.rdb.hgetall(station)
        decoded = {}
        for k,v in data.items():
            decoded[k.decode()] = v.decode()
        return decoded

    def get( self, station, key):
        """ Get all key values in the database for this key
        @param str station: The network id where the original request came from
        returns: The objects save with the network and uid
        """
        item = self.rdb.hget(station, key)
        if item:
            return item.decode()

    def put(self, station, values):
        """ Write the new items on the destination network
        @param station: char: station id used to index
        @param values: dictionary of values to save
        @returns: None
        """
        # See which keys no longer exist eg. wx_string
        keys = [ item.decode() for item in self.rdb.hkeys(station)]
        diff = set(keys) - set(list(values.keys))
        if 'wx_sting' in diff:
            self.rdb.hdel(station,'wx_string')
            
        for key, value in values.items():
            if not value or isinstance(value, dict) or isinstance(value, list):
                continue
            self.rdb.hset(station, key, value)

    def add(self, key, values):
        """ Set members of a list
        :param str key:
        :param list values:
        :return: None
        """
        for value in values:
            self.rdb.sadd(key, value)

    def members(self, key):
        """ Return a list for a key
        :param key: key to return
        :return: list: of key values
        """
        members = self.rdb.smembers(key)
        if members:
            return [ member.decode() for member in members]

    def geo_add(self,key, point):
        """
        Add a geo point to the database
        :param key:
        :param lat:
        :param lon:
        :return:
        """
        return self.rdb.geoadd(key,point)


