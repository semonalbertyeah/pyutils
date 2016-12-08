# -*- coding:utf-8 -*-


class ListProxy(object):
    """
        proxying operation on part of a list

        indicate range with: 
            start, length
            start, end (as in list slice, end is not included)
    """
    def __init__(self, target, start=0, end=None, length=None):
        """
            target -> the proxied list
            start -> the start position of proxied part
            length -> the length of proxied part
                      if length is None,
                      that means proxied part start from 
                      position "start" to end of the list.
        """
        assert isinstance(target, list)
        assert isinstance(start, int) and \
               start >= -len(target) and \
               start <= (len(target) - 1)

        if end is not None:
            assert isinstance(end, int) and \
                   end >= start and \
                   end <= (len(target) - 1)

        if length is not None:
            assert isinstance(length, int) and \
                   length >= 0 and \
                   length <= len(target)

        self.__target = target
        self.__start = start
        self.__end = end
        self.__length = length


    @staticmethod
    def assure_positive_index(idx, length):
        """
            return a positive index
            idx -> index value
            length -> length of list
        """
        if idx < -length or idx >= length:
            print idx
            raise IndexError, "list index out of range" 
        if idx < 0:
            return length + idx
        else:
            return idx


    @property
    def start(self):
        """
            the oppsite value of the start index (in proxied list)
        """
        return self.assure_positive_index(self.__start, len(self.__target))


    @property
    def length(self):
        """
            length the proxied part
        """
        if self.__length is not None:
            return self.__length
        elif self.__end is not None:
            end = self.assure_positive_index(self.__end, len(self.__target))
            return end - self.start
        else:
            # to the end
            return len(self.__target) - self.start


    @property
    def end(self):
        """
            the opposite value of the end index (in proxied list)
        """
        return self.start + self.length


    def adjust_index(self, idx):
        """
            proxy index -> target index
        """
        idx = self.assure_positive_index(idx, self.length)
        return self.start + idx


    def adjust_slice(self, s):
        """
            proxy range -> target range
        """
        assert isinstance(s, slice)
        if s.start is not None:
            start = self.adjust_index(s.start)
        else:
            start = self.start

        if s.stop is not None:
            stop = self.adjust_index(s.stop)
        else:
            stop =self.end

        step = 1 if s.step is None else s.step

        if step > 0:
            assert start <= stop
        else:
            assert start >= stop

        return slice(start, stop, step)



    def __getitem__(self, soi):
        """
            soi -> slice of index
        """
        if isinstance(soi, slice):
            s = self.adjust_slice(soi)
            return self.__target[s]
        else:
            idx = self.adjust_index(soi)
            return self.__target[idx]


    def __setitem__(self, soi, value):
        if isinstance(soi, slice):
            s = self.adjust_slice(soi)
            self.__target[s] = value
        else:
            idx = self.adjust_index(soi)
            self.__target[idx] = value

    def __delitem__(self, *args, **kwargs):
        raise TypeError, "cannot delete item in a list proxy."

    def __contains__(self, value):
        return value in self.__target[self.start: self.end]

    def __iter__(self):
        return self.__target[self.self:self.end].__iter__()

    def __len__(self):
        return self.length

    def count(self, value):
        return self.__target[self.start: self.end].count(value)

    def index(self, value):
        return self.__target[self.start: self.end].index(value)

