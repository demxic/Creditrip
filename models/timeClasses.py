from datetime import timedelta, datetime, time


class Duration(object):

    def __init__(self, minutes: int):
        """value should be a timedelta or minutes (int)"""
        # TODO : IMPLEMENT __format__ method
        if minutes < 0:
            minutes = 0
        self.minutes = int(minutes)

    @classmethod
    def from_timedelta(cls, value):
        minutes = value.total_seconds() / 60
        return cls(minutes)

    @classmethod
    def from_string(cls, value: str):
        hours = int(value[0:-2])
        minutes = int(value[-2:])
        return cls(minutes=hours * 60 + minutes)

    def as_timedelta(self):
        return timedelta(minutes=self.minutes)

    def no_trailing_zero(self):
        """Prints as HH:MM v.gr. 7:30 instead of 07:30"""
        if self.minutes == 0:
            hm = 4 * ''
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0}:{1:0>2d}".format(hours, minutes)

        return hm

    def __str__(self):
        """Prints as HHMM v.gr. 1230"""
        if self.minutes == 0:
            hm = 4 * ''
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0:0>2d}{1:0>2d}".format(hours, minutes)

        return hm

    def __repr__(self):
        """Prints as HHH:MM v.gr. 123:30"""
        if self.minutes == 0:
            hm = '00:00'
        else:
            hours, minutes = divmod(self.minutes, 60)
            hm = "{0:0>2d}:{1:0>2d}".format(hours, minutes)

        return hm

    def __add__(self, other):
        return Duration(self.minutes + other.minutes)

    def __radd__(self, other):
        """Because sum(x) always starts adding a 0, Duration takes this into account in this method"""
        return Duration(self.minutes + other.minutes)

    def __sub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __rsub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __mul__(self, other):
        return self.minutes / 60 * other

    def __rmul__(self, other):
        return self.__mul__(other)

    def __lt__(self, other):
        return self.minutes < other.minutes

    def __format__(self, fmt='0'):
        """Depending on fmt value, a Duration can be printed as follow:
        fmt = 0  :   HHMM          4 chars no signs                                v.gr. 0132, 0025, 0000
        fmt = 1  :   HHMM          4 chars no sings or blank if self.minutes = 0   v.gr. 0132, 0025,'   '
        fmt = 2  : HHH:MM          6 chars with colon in between                   v.gr  01:32, 00:25, 00:00, 132:45
        fmt = 3  :  HH:MM          5 chars colon in between and blank for min =0   v.gr  01:32, 00:25, '    '
        Any other value defaults to fmt == 0
        """

        if fmt == '1':
            return str(self)
        elif fmt == '2':
            return repr(self)
        elif fmt == '3':
            prov = repr(self)
            if self.minutes == 0:
                return '     '
            else:
                return repr(self)
        else:
            if self.minutes == 0:
                return '0000'
            else:
                return self.__str__()


class DateTimeTracker(object):
    """Keeps track of datetime object in order to build Itineraries"""

    def __init__(self, begin: str, timezone=None):
        self.datetime_format = "%d%b%Y%H:%M"
        self.timezone = timezone
        self.dt = datetime.strptime(begin, self.datetime_format)
        if timezone:
            self.dt = self.timezone.localize(self.dt)

    def start(self):
        """Moves one hour ahead"""
        self.dt += timedelta(hours=1)

    def release(self):
        "Moves half an hour ahead"
        self.dt += timedelta(minutes=30)

    def build_end_dt(self, time_string: str, destination_timezone):
        """Given an end_time and a timezone for it...

        build and return the corresponding aware end_datetime.
        Update DateTimeTracker correspondingly afterwards
        """
        begin_as_destination_time_zone = self.dt.astimezone(destination_timezone)
        end_hour = int(time_string[0:2])
        end_minutes = int(time_string[2:4])
        end_date = begin_as_destination_time_zone.date()
        end_time = time(hour=end_hour, minute=end_minutes)
        preliminary_end = destination_timezone.localize(datetime.combine(end_date, end_time))
        if preliminary_end < begin_as_destination_time_zone:
            end_date = (preliminary_end + timedelta(days=1)).date()
            end_time = time(hour=end_hour, minute=end_minutes)
            end_datetime = datetime.combine(end_date, end_time)
            end = destination_timezone.localize(end_datetime)
        else:
            end = preliminary_end
        self.dt = end
        return end

    def forward(self, time_string: str) -> timedelta:
        """Moves HH hours and MM minutes forward in time.
        time_string may be of type HH:MM or HHMM
        """
        hh = int(time_string[:-3])
        mm = int(time_string[-2:])
        td: timedelta = timedelta(hours=hh, minutes=mm)
        self.dt += td
        return td

    def backward(self, time_string: str) -> timedelta:
        """Moves HH hours and MM minutes backward in time.
        time_string may be of type HH:MM or HHMM
        """
        hh = int(time_string[:2])
        mm = int(time_string[-2:])
        td: timedelta = timedelta(hours=hh, minutes=mm)
        self.dt -= td
        return td

    @property
    def date(self):
        return self.dt.date()

    def __str__(self):
        return str(self.dt)
