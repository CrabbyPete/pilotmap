import redis


class Database(redis.Redis):
    """ Redis database object
    """
    def __init__(self, host="127.0.0.1", port=6379, db=0):
        super().__init__(host="127.0.0.1", port=6379, db=0, decode_responses=True)

    def put(self, station, values):
        """ Write the new items on the destination network
        @param station: char: station id used to index
        @param values: dictionary of values to save
        @param skip:bool skip check for keys that no longer exist
        @returns: None
        """
        # See which keys no longer exist eg. wx_string
        keys = self.hkeys(station)
        diff = set(keys) - set(list(values.keys()))
        for key in diff:
            self.hdel(station,key)

        # Now put in what you have
        for key, value in values.items():
            if not value or isinstance(value, dict) or isinstance(value, list):
                continue
            self.hset(station, key, value)



