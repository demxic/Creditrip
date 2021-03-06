from datetime import timedelta, datetime, date

import psycopg2
import pytz

from data.database import CursorFromConnectionPool
#import data.exceptions
from data.exceptions import MissingAirport, UnstoredTrip
from models.timeClasses import Duration

utc = pytz.utc


class Airport(object):
    """Create airports using the Flyweight pattern
    Try using the weakref.WeakValueDictionary() if  garbage-collection concerned
    for our simple app, not needed
    """
    _airports = dict()

    def __new__(cls, iata_code: str, timezone=None, *args, **kwargs):
        airport = cls._airports.get(iata_code)
        if not airport:
            airport = super().__new__(cls)
            cls._airports[iata_code] = airport

        return airport

    def __init__(self, iata_code: str, timezone=None, viaticum: str = None):
        """
        Represents an airport as a 3 letter code
        """
        self.iata_code = iata_code
        self.timezone = timezone
        self.viaticum = viaticum

    # def save_to_db(self):
    #     with CursorFromConnectionPool() as cursor:
    #         continent, tz_city = self.timezone.split('/')
    #         try:
    #             cursor.execute('INSERT INTO airports (iata_code, continent, tz_city, viaticum_zone) '
    #                            'VALUES (%s, %s, %s, %s)',
    #                            (self.iata_code, continent, tz_city, self.viaticum))
    #         except psycopg2.IntegrityError:
    #             print("Already stored")
    #
    # def update_to_db(self):
    #     split_timezone = self.timezone.split()
    #     if len(split_timezone) == 2:
    #         # Este es un caso normal
    #         continent, tz_city = split_timezone
    #     else:
    #         # Este es el caso de America/Argentina/Buenos_Aires
    #         continent = split_timezone[0]
    #         tz_city = split_timezone[1] + '/' + split_timezone[2]
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('UPDATE airports '
    #                        '    set continent = %s, tz_city = %s, viaticum_zone = %s '
    #                        'WHERE iata_code = %s', (continent, tz_city,
    #                                                 self.viaticum, self.iata_code))
    #
    @classmethod
    def load_from_db_by_iata_code(cls, iata_code: str):
        airport = cls._airports.get(iata_code.upper())
        if not airport:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('SELECT * FROM airports WHERE iata_code=%s;', (iata_code,))
                airport_data = cursor.fetchone()
                if not airport_data:
                    raise MissingAirport(iata_code)
                timezone = pytz.timezone(airport_data[1] + '/' + airport_data[2])
                airport = cls(iata_code=airport_data[0], timezone=timezone, viaticum=airport_data[3])
                cls._airports[iata_code] = airport
        return airport

    def __str__(self):
        return "{}".format(self.iata_code)


class CrewMember(object):
    """Defines a CrewMember"""

    def __init__(self, crew_member_id: int = None, name: str = None, pos: str = None, group: str = None,
                 base: Airport = None, seniority: int = None):
        self.crew_member_id = crew_member_id
        self.name = name
        self.pos = pos
        self.group = group
        self.base = Airport(base) if isinstance(base, str) else base
        self.seniority = seniority
        self.line = None

    def __str__(self):
        return "{0:3s} {1:6s}-{2:12s}".format(self.pos, self.crew_member_id, self.name)


class Equipment(object):
    _equipments = dict()

    def __new__(cls, airplane_code, *args, **kwargs):
        equipment = cls._equipments.get(airplane_code)
        if not equipment:
            equipment = super().__new__(cls)
            cls._equipments[airplane_code] = equipment
        return equipment

    def __init__(self, airplane_code, cabin_members: int = None):
        self.airplane_code = airplane_code
        self.cabin_members = cabin_members

    # def save_to_db(self):
    #     with CursorFromConnectionPool() as cursor:
    #         try:
    #             cursor.execute('INSERT INTO equipments (code, cabin_members) '
    #                            'VALUES (%s, %s)',
    #                            (self.airplane_code, self.cabin_members))
    #         except psycopg2.IntegrityError:
    #             print("Already stored")
    #
    # @classmethod
    # def load_from_db_by_code(cls, airplane_code):
    #     equipment = cls._equipments.get(airplane_code)
    #     if not equipment:
    #         with CursorFromConnectionPool() as cursor:
    #             cursor.execute('SELECT * FROM equipments WHERE code=%s', (airplane_code,))
    #             equipment_data = cursor.fetchone()
    #             if equipment_data:
    #                 equipment = cls(airplane_code=equipment_data[0], cabin_members=equipment_data[1])
    #                 cls._equipments[airplane_code] = equipment
    #
    #     return equipment

    def __str__(self):
        if not self.airplane_code:
            eq_string = 3 * ' '
        else:
            eq_string = self.airplane_code
        return eq_string

    def __eq__(self, other) -> bool:
        return self.airplane_code == other.airplane_code


class Route(object):
    """For a given airline, represents a flight number or ground duty name
        with its origin and destination airports
        Note: flights and ground duties are called Events"""
    _routes = dict()

    def __new__(cls, name: str, origin: Airport, destination: Airport, *args, **kwargs):
        route_key = name + origin.iata_code + destination.iata_code
        route = cls._routes.get(route_key)
        if not route:
            route = super().__new__(cls)
            cls._routes[route_key] = route
        return route

    def __init__(self, name: str, origin: Airport, destination: Airport, route_id: int = None):
        """Flight numbers have 4 digits only"""
        self.route_id = route_id
        self.name = name
        self.origin = origin
        self.destination = destination

    # @classmethod
    # def create_route(cls):
    #     """
    #         route = E3 MEX MEX
    #         Note: While creating a flight to be, DH condition should not be marked within route name
    #     """
    #     print("Enter route as FLT ORG DES, v.gr  E2 MEX MEX    or   0403 MEX JFK   or   0106 MEX GDL")
    #     route_string = input("Do not input DH condition: ")
    #     name, departure_airport, arrival_airport = route_string.split()
    #     route = cls(name=name, origin=Airport(departure_airport),
    #                 destination=Airport(arrival_airport))
    #     return route
    #
    # def as_dict(self):
    #     "Return route parameters as a dictionary"
    #     return {'name': self.name, 'origin': self.origin, 'destination': self.destination,
    #             'route_id': self.route_id}
    #
    # def modify_route(self):
    #     """This function will update a route"""
    #     print("Current route: ")
    #     print(self)
    #     new_route = self.create_route()
    #     print("Update with route: ")
    #     print(new_route)
    #     answer = input("Are you sure you want to store new roue? Changes can't be undone Y/N").capitalize()
    #     if answer == 'Y':
    #         return new_route
    #     else:
    #         return None
    #
    def save_to_db(self) -> int:
        if not self.route_id:
            route_id = self.load_route_id()
            if not route_id:
                with CursorFromConnectionPool() as cursor:
                    cursor.execute('INSERT INTO public.routes (name, origin, destination) '
                                   'VALUES (%s, %s, %s)'
                                   'RETURNING route_id;',
                                   (self.name, self.origin.iata_code, self.destination.iata_code))
                    route_id = cursor.fetchone()[0]
            self.route_id = route_id
        return self.route_id

    def load_route_id(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT route_id FROM public.routes '
                           '    WHERE name=%s'
                           '      AND origin=%s'
                           '      AND destination=%s',
                           (self.name, self.origin.iata_code, self.destination.iata_code))
            route_id = cursor.fetchone()
            if route_id:
                return route_id[0]

    @classmethod
    def load_by_id(cls, route_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT name, origin, destination '
                           '    FROM public.routes '
                           '    WHERE route_id=%s',
                           (route_id,))
            route_data = cursor.fetchone()
            origin = Airport(route_data[1])
            destination = Airport(route_data[2])

            return cls(name=route_data[0], origin=origin,
                       destination=destination, route_id=route_id)

    @classmethod
    def load_from_db_by_fields(cls, name: str, origin: Airport, destination: Airport):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT route_id FROM public.routes '
                           '    WHERE name=%s'
                           '      AND origin=%s'
                           '      AND destination=%s',
                           (name, origin.iata_code, destination.iata_code))
            route_id = cursor.fetchone()
            if route_id:
                route = cls(route_id=route_id[0], name=name, origin=origin, destination=destination)
                return route

    def __str__(self):
        return "{} {} {}".format(self.name, self.origin, self.destination)


class Itinerary(object):
    """ An Itinerary represents a Duration occurring between a 'begin' and an 'end' datetime. """

    def __init__(self, begin: datetime, end: datetime):
        """Enter beginning and ending utc aware-datetime """
        self._begin = begin
        self._end = end
        self.begin_timezone = begin.tzinfo
        self.end_timezone = end.tzinfo

    @classmethod
    def from_timedelta(cls, begin: datetime, a_timedelta: timedelta):
        """Returns an Itinerary from a given begin datetime and the timedelta duration of it"""
        end = begin + a_timedelta
        return cls(begin, end)

    @property
    def begin(self):
        return self._begin.astimezone(self.begin_timezone)

    @begin.setter
    def begin(self, new_begin):
        self.begin_timezone = new_begin.tzinfo
        self._begin = new_begin.astimezone(utc)

    @property
    def end(self):
        return self._end.astimezone(self.end_timezone)

    @end.setter
    def end(self, new_end):
        self.end_timezone = new_end.tzinfo
        self._end = new_end.astimezone(utc)

    @property
    def duration(self) -> Duration:
        return Duration.from_timedelta(self._end - self._begin)

    def astimezone(self, begin_timezone, end_timezone):
        self.begin_timezone = begin_timezone
        self.end_timezone = end_timezone

    def __str__(self):
        template = "{0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        return template.format(self)

    def __eq__(self, other):
        return (self.begin == other.begin) and (self.end == other.end)

    # @classmethod
    # def create_itinerary(cls):
    #     """Given an itinerary as a string"""
    #     print("For begin ", end=" ")
    #     begin_datetime = create_datetime()
    #     print("For end ", end=" ")
    #     end_datetime = create_datetime()
    #     return cls(begin=begin_datetime, end=end_datetime)

    # @classmethod
    # def from_date_and_strings(cls, date: datetime.date, begin: str, end: str):
    #     """date should  be a datetime.date object
    #     begin and end should have a %H%M (2345) format"""
    #     begin = '0000' if begin == '2400' else begin
    #     end = '0000' if end == '2400' else end
    #     formatting = '%H%M'
    #     begin_string = datetime.strptime(begin, formatting).time()
    #     begin = datetime.combine(date, begin_string)
    #     end_string = datetime.strptime(end, formatting).time()
    #     end = datetime.combine(date, end_string)
    #
    #     if end < begin:
    #         end += timedelta(days=1)
    #     return cls(begin, end)
    #
    # @classmethod
    # def from_string(cls, input_string: str):
    #     """
    #     format DDMMYYYY HHMM    HHMM
    #            23122019 1340    0320
    #            DATE     begin   blk
    #     """
    #     date, begin, blk = input_string.split()
    #     formatting = '%d%m%Y%H%M'
    #     begin = datetime.strptime(date + begin, formatting)
    #     return cls.from_timedelta(begin=begin, a_timedelta=Duration.from_string(blk).as_timedelta())

    # def get_elapsed_dates(self):
    #     """Returns a list of dates in range [self.begin, self.end]"""
    #     delta = self.end.date() - self.begin.date()
    #     all_dates = (self.begin.date() + timedelta(days=i) for i in range(delta.days + 1))
    #     return list(all_dates)
    #
    # def in_same_month(self):
    #     if self.begin.month == self.end.month:
    #         return True
    #     else:
    #         return False

    # def compute_credits(self, itinerator=None):
    #     return None
    #
    # def overlaps(self, other):
    #     begin_date = self.begin.date()
    #     overlap = max(0, min(self.end, other.end) - max(self.begin, other.begin))
    #     return overlap


class Event(object):
    """
    Represents  Vacations, GDO's, time-off, etc.
    Markers don't account for duty or block time in a given month
    """

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, event_id: int = None):
        self.route = route
        self.scheduled_itinerary = scheduled_itinerary
        self.event_id = event_id
        self._credits = None

    @staticmethod
    def create_event_parameters() -> dict:
        """Ask user to input a scheduled itinerary

            scheduled_itinerary = 100813 0823 1345
            actual_itinerary = None

        """
        event_parameters = dict()
        event_parameters['route'] = Route.create_route()
        answer = input("Do you know the scheduled itinerary for this event? Y/N :").capitalize()[0]
        if answer == 'Y':
            event_parameters['scheduled_itinerary'] = Itinerary.create_itinerary()
        else:
            event_parameters['scheduled_itinerary'] = None
        return event_parameters

    @property
    def name(self) -> str:
        """Although an Event is more likely to be localized, using Route
            to store and retrieve information makes for a better class hierarchy"""
        return self.route.name

    @property
    def begin(self) -> datetime:
        return self.scheduled_itinerary.begin if self.scheduled_itinerary else None

    @property
    def end(self) -> datetime:
        return self.scheduled_itinerary.end if self.scheduled_itinerary else None

    @property
    def duration(self) -> Duration:
        return Duration.from_timedelta(self.end - self.begin)

    def compute_credits(self, creditator=None):
        self._credits = {'block': Duration(0), 'dh': Duration(0), 'daily': Duration(0)}

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            self.scheduled_itinerary.astimezone(begin_timezone=timezone,
                                                end_timezone=timezone)
        else:
            self.scheduled_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                end_timezone=self.route.destination.timezone)

    def __str__(self) -> str:
        if self.scheduled_itinerary:
            template = "{0.route.name} {0.begin:%d%b} BEGIN {0.begin:%H%M} END {0.end:%H%M}"
        else:
            template = "{0.route.name}"
        return template.format(self)

    # def save_to_db(self):
    #     if not self.event_id:
    #         with CursorFromConnectionPool() as cursor:
    #             # cursor.execute('SELECT * FROM public.reserves '
    #             #                'WHERE name=%s, dated=%s ')
    #             # gd_data = cursor.fetchone()
    #             # if not gd_data:
    #             try:
    #                 cursor.execute('INSERT INTO public.markers('
    #                                '            route_id, begin, duration) '
    #                                'VALUES (%s, %s, %s);',
    #                                (self.route.route_id, self.begin, self.duration.as_timedelta()))
    #             except psycopg2.IntegrityError:
    #                 print("{} has already been stored".format(str(self)))


class GroundDuty(Event):
    """
    Represents  training, reserve or special assignments.
    Ground duties do account for some credits
    """

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, position: str = None,
                 equipment=None, event_id: int = None) -> None:
        super().__init__(route=route, scheduled_itinerary=scheduled_itinerary, event_id=event_id)
        self.position = position
        self.equipment = equipment

    @staticmethod
    def create_ground_duty_parameters() -> dict:
        """
        Given an event_dict as a dict, turn it into a Ground Duty object
            ground_duty_string = 100818 E3 MEX 0823 1345

        """
        event_parameters = Event.create_event_parameters()
        event_parameters['position'] = input("Is this an EJE or SOB position? ").capitalize()[:3]
        return event_parameters

    @property
    def report(self) -> datetime:
        return self.begin

    @property
    def release(self) -> datetime:
        return self.end

    def as_robust_string(self, rpt=4 * '', rls=4 * '', turn=4 * ''):
        """Prints a Ground Duty following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        05JUN 0900 E6     MEX 0900 MEX 1500 1500 0000

        OR ********************************************************************
        Prints a Flight following this heather template
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN       EQ
        03JUN 1400 0924   MEX 1500 MTY 1640 1720 0140       0000       738


        Following arguments being optional
        rpt : report
        rls : release
        turn: turn around time
        eq : equipment"""

        template = """
        {0.begin:%d%b} {rpt:4s} {0.name:<6s} {0.route.origin} {0.begin:%H%M} {0.route.destination} {0.end:%H%M} {rls:4s} {block}       {turn:4s}       {0.equipment}"""
        self.compute_credits()
        block = self._credits['block']
        return template.format(self, rpt=rpt, rls=rls, turn=turn, block=block)

    # def save_to_db(self):
    #     if not self.event_id:
    #         if not self.route.route_id:
    #             self.route.load_route_id()
    #         with CursorFromConnectionPool() as cursor:
    #             # cursor.execute('SELECT * FROM public.reserves '
    #             #                'WHERE name=%s, dated=%s ')
    #             # gd_data = cursor.fetchone()
    #             # if not gd_data:
    #             try:
    #                 cursor.execute('INSERT INTO public.reserves('
    #                                '            route_id, begin, duration, gposition) '
    #                                'VALUES (%s, %s, %s, %s);',
    #                                (self.route.route_id, self.begin, self.duration.as_timedelta(),
    #                                 self.position))
    #             except psycopg2.IntegrityError:
    #                 print("{} has already been stored".format(str(self)))

    # def update_to_db(self):
    #     """Will store GroundDuty into database without validating data"""
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('UPDATE public.reserves '
    #                        'SET route_id = %s, begin_time_stamp = %s, duration = %s, gposition = %s '
    #                        'WHERE name = %s and dated = %s;',
    #                        (self.scheduled_itinerary.begin.time(), self.duration.as_timedelta(),
    #                         self.route.departure_airport, self.position))

    # def update_from_database(self):
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('SELECT * FROM public.reserves '
    #                        'WHERE name = %s '
    #                        'AND dated=%s ',
    #                        (self.name, self.report.date()))
    #         ground_duty_data = cursor.fetchone()
    #         if ground_duty_data:
    #             begin = datetime.combine(ground_duty_data[1], ground_duty_data[2])
    #             duration = ground_duty_data[3]
    #             location = ground_duty_data[4]
    #             self.position = ground_duty_data[5]
    #             self.scheduled_itinerary = Itinerary(begin, begin + duration)
    #             self.route = Route.load_from_db_by_fields(name='0000', departure_airport=location,
    #                                                       arrival_airport=location)
    #             self.route.flight_number = ground_duty_data[0]


class Flight(GroundDuty):

    def __init__(self, route: Route, scheduled_itinerary: Itinerary = None, actual_itinerary: Itinerary = None,
                 equipment: Equipment = None, carrier: str = 'AM', event_id: int = None, dh=False, position=None):
        """
        Holds those necessary fields to represent a Flight Itinerary
        """
        super().__init__(route=route, scheduled_itinerary=scheduled_itinerary, equipment=equipment,
                         event_id=event_id, position=position)
        self.actual_itinerary = actual_itinerary
        self.carrier = carrier
        self.dh = dh
        # self.is_flight = True

    @property
    def begin(self) -> datetime:
        return self.actual_itinerary.begin if self.actual_itinerary else self.scheduled_itinerary.begin

    @begin.setter
    def begin(self, new_begin: datetime):
        if self.actual_itinerary:
            self.actual_itinerary.begin = new_begin
        else:
            self.scheduled_itinerary.begin = new_begin

    @property
    def end(self) -> datetime:
        return self.actual_itinerary.end if self.actual_itinerary else self.scheduled_itinerary.end

    @end.setter
    def end(self, new_end: datetime):
        if self.actual_itinerary:
            self.actual_itinerary.end = new_end
        else:
            self.scheduled_itinerary.end = new_end

    # @classmethod
    # def from_string(cls, flight_data: str):
    #     """Given a Flight as a list of type:
    #        DDMMYYYY AC#### ORG HHMM DES HHMM EQ
    #        v.gr. 23062018 0403 MEX 0700 JFK 1300 7S8
    #     Turn it into a corresponding object
    #     """
    #     date, flight_number, origin, begin, destination, end, eq = flight_data.split()
    #     route = Route(flight_number[-4:], Airport(origin), Airport(destination))
    #     scheduled_itinerary = Itinerary.from_string(date + " " + begin + " " + end)
    #     equipment = Equipment(eq) if len(eq) == 3 else None
    #     carrier = "AM"
    #     dh = False
    #     if not flight_number.isnumeric():
    #         carrier = "AM" if flight_number[0:2] == "DH" else flight_number[0:2]
    #         dh = True
    #
    #     return cls(route=route, scheduled_itinerary=scheduled_itinerary, actual_itinerary=None,
    #                equipment=equipment, carrier=carrier, event_id=None, dh=dh)
    #
    # @staticmethod
    # def create_flight_parameters() -> dict:
    #     """
    #         Given a Flight as a string turn it into an object
    #                 flight_string = 100818 E3 MEX 0823 1345
    #         """
    #     event_parameters = GroundDuty.create_ground_duty_parameters()
    #     answer = input("Is this a (S)cheduled or an (A)ctual itineray? ").capitalize()
    #     if answer[0] != 'A':
    #         # Stored itinerary is a scheduled one and not an actual
    #         answer = input("Input an actual itinerary? Y/N")
    #         if answer[0] == 'Y':
    #             event_parameters['actual_itinerary'] = Itinerary.create_itinerary()
    #     else:
    #         # Stored itinerary is an actual and now we should ask for tis scheduled one
    #         print("Input a scheduled itinerary? Y/N")
    #         if answer[0] == 'Y':
    #             event_parameters['actual_itinerary'] = event_parameters['scheduled_itinerary']
    #             event_parameters['scheduled_itinerary'] = Itinerary.create_itinerary()
    #
    #     dh = input("Is this a DH flight? Y/N ").capitalize()[0]
    #     if dh.startswith('Y'):
    #         event_parameters['dh'] = True
    #     else:
    #         event_parameters['dh'] = False
    #     event_parameters['equipment'] = Equipment(
    #         input("What is the 3 letter code for the aircraft flown?  ").capitalize())
    #
    #     return event_parameters
    #
    # def modify_event(self):
    #     """Given a flight, modify its actual or scheduled itinerary
    #         Note: although you could modify other parameters, this will rarely happen
    #     """
    #
    #     # answer = input("¿Quieres modificar la ruta del vuelo? Y/N ").capitalize()
    #     # if answer == 'Y':
    #     #     route = create_route()
    #     #     print("route {} changed to : ".format(flight.route))
    #     #     print("route {} ".format(route))
    #     #     flight.route = route
    #
    #     answer = input("Would you like to modify its (S)cheduled or (A)ctual itineary? ")
    #     print("For flight: ")
    #     print(self)
    #     print("Enter new itinerary")
    #     itinerary = Itinerary.create_itinerary()
    #
    #     print("{} will replace: ".format(itinerary))
    #     if answer == "S":
    #         print(self.scheduled_itinerary)
    #         o = input("Are you sure? Changes can't be undone Y/N ").capitalize()
    #         if o == "Y":
    #             self.scheduled_itinerary = itinerary
    #     elif answer == "A":
    #         print(self.actual_itinerary)
    #         o = input("Are you sure? Changes can't be undone Y/N ").capitalize()
    #         if o == "Y":
    #             self.actual_itinerary = itinerary

    @property
    def name(self) -> str:
        """
        Returns the full flight name, composed of a prefix and a flight_number
        prefix indicates a DH flight by AM or any other company
        """
        prefix = ''
        if self.dh:
            if self.carrier == 'AM' or self.carrier == '6D':
                prefix = 'DH'
            else:
                prefix = self.carrier
        return prefix + self.route.name

    @property
    def report(self) -> datetime:
        """Flight's report time"""
        if not self.scheduled_itinerary:
            return self.actual_itinerary.begin - timedelta(hours=1)
        else:
            return self.scheduled_itinerary.begin - timedelta(hours=1)

    @property
    def release(self) -> datetime:
        """Flights's release time """
        if not self.actual_itinerary:
            return self.scheduled_itinerary.end + timedelta(minutes=30)
        else:
            return self.actual_itinerary.end + timedelta(minutes=30)

    def compute_credits(self, creditator=None):
        if self.dh:
            dh = self.duration
            block = Duration(0)
        else:
            block = self.duration
            dh = Duration(0)
        self._credits = {'block': block, 'dh': dh}

    # TODO : Modify to save a flight with all its known values
    # TODO : ALL save_to_db() methods should be first check that event is not stored before creating it
    def save_to_db(self) -> int:
        # Is this a new route?
        self.route.save_to_db()
        if not self.event_id:
            scheduled_begin = self.scheduled_itinerary._begin.replace(tzinfo=None)
            with CursorFromConnectionPool() as cursor:
                cursor.execute('INSERT INTO public.flights('
                               '            airline_iata_code, route_id, scheduled_begin, '
                               '            scheduled_block, equipment)'
                               'VALUES (%s, %s, %s, %s, %s)'
                               'RETURNING flight_id;',
                               (self.carrier, self.route.route_id, scheduled_begin,
                                self.duration.as_timedelta(), self.equipment.airplane_code))
                self.event_id = cursor.fetchone()[0]
        return self.event_id

    def delete(self):
        """Remove flight from DataBase"""
        try:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('DELETE FROM public.flights '
                               '    WHERE flight_id = %s',
                               (self.event_id,))
        except psycopg2.IntegrityError:
            # TODO : Better build methods directly into the class
            print("flight {} ".format(self))
            print("Can't be deleted because it belongs to another trip ")
            print("Would you rather update it? ")
            begin = input("Enter begin time as HHMM :")
            duration = input("Enter duration as HHMM :")
            self.begin.replace(hour=int(begin[:2]), minute=int(begin[2:]))
            self.end = self.begin + Duration.from_string(duration).as_timedelta()
            self.update_to_db()

    def update_to_db(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE public.flights '
                           'SET airline_iata_code = %s, route_id = %s, scheduled_begin = %s, '
                           'scheduled_block = %s, equipment = %s '
                           'WHERE flight_id = %s;',
                           (self.carrier, self.route.route_id, self.begin,
                            self.duration.as_timedelta(), self.equipment.airplane_code, self.event_id))

    # def update_from_database(self):
    #     """Load all fields for this event, compare each field to its corresponding parameter
    #        and update accordingly """
    #     loaded_flight = self.load_from_db_by_fields(airline_iata_code=self.carrier, scheduled_begin=self.begin,
    #                                                 route=self.route)
    #     if not loaded_flight:
    #         # This is typical of a return to TARMAC, where flight will now be AM0025 MEX MEX before AM0025 MEX AMS
    #         # TODO : Create scheduled itinerary for returned flight automatically instead of prompting for fields
    #         print(80 * '*')
    #         print("Event {} does not exist in DB \n".format(self))
    #         print("Create scheduled itinerary for event \n\n")
    #         flight_parameters = Flight.create_flight_parameters()
    #         created_flight = Flight(**flight_parameters)
    #         created_flight.save_to_db()
    #         loaded_flight = self.load_from_db_by_fields(airline_iata_code=self.carrier, scheduled_begin=self.begin,
    #                                                     route=self.route)
    #     self.event_id = loaded_flight.event_id
    #
    #     # 1. Scheduled itineraries should be the same
    #     if self.scheduled_itinerary:
    #         if loaded_flight.scheduled_itinerary and (self.scheduled_itinerary != loaded_flight.scheduled_itinerary):
    #             print("scheduled_itinerary discrepancy, which one would you like to keep ? ")
    #             print("1. {} ".format(self.scheduled_itinerary))
    #             print("2. {} ".format(loaded_flight.scheduled_itinerary))
    #             option = input()
    #             if option != 1:
    #                 self.scheduled_itinerary = loaded_flight.scheduled_itinerary
    #     elif loaded_flight.scheduled_itinerary:
    #         self.scheduled_itinerary = loaded_flight.scheduled_itinerary
    #
    #     # 2. Actual itineraries should be, and should be the same
    #     if self.actual_itinerary:
    #         if loaded_flight.actual_itinerary and (self.actual_itinerary != loaded_flight.actual_itinerary):
    #             print("actual_itinerary discrepancy, which one would you like to keep ? ")
    #             print("1. {} ".format(self.actual_itinerary))
    #             print("2. {} ".format(loaded_flight.actual_itinerary))
    #             option = input()
    #             if option != 1:
    #                 self.actual_itinerary = loaded_flight.actual_itinerary
    #     elif loaded_flight.actual_itinerary:
    #         self.actual_itinerary = loaded_flight.actual_itinerary
    #
    #     # This is tricky, because the DH condition is loaded in the duty_days table, not in each flight
    #     # if self.dh != loaded_flight.dh:
    #     #     print(self)
    #     #     answer = input("is flight a DH flight? y/n").upper()
    #     #     if answer[0] == 'Y':
    #     #         self.dh = True
    #     #     else:
    #     #         self.dh = False
    #
    #     if loaded_flight.equipment:
    #         if self.equipment and (self.equipment != loaded_flight.equipment):
    #             print("equipment discrepancy, which one would you like to keep ? ")
    #             print("1. {} ".format(self.equipment))
    #             print("2. {} ".format(loaded_flight.equipment))
    #             option = input()
    #             if option != 1:
    #                 self.equipment = loaded_flight.equipment
    #         else:
    #             self.equipment = loaded_flight.equipment
    #
    @classmethod
    def load_from_db_by_id(cls, flight_id: int):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           'INNER JOIN public.routes ON flights.route_id = routes.route_id '
                           'WHERE flights.flight_id=%s', (flight_id,))
            flight_data = cursor.fetchone()
            if flight_data:
                route = Route.load_by_id(route_id=flight_data[2])
                itinerary = Itinerary.from_timedelta(begin=flight_data[3],
                                                     a_timedelta=flight_data[4])
                equipment = Equipment(airplane_code=flight_data[5])
                carrier = flight_data[1]
                return cls(route=route, scheduled_itinerary=itinerary, equipment=equipment,
                           carrier=carrier, event_id=flight_id)

    @classmethod
    def load_from_db_by_fields(cls, airline_iata_code: str, scheduled_begin: datetime, route: Route):
        """Load from Data Base. """
        built_flights = None
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.flights '
                           '    WHERE airline_iata_code = %s '
                           '      AND route_id=%s'
                           '      AND scheduled_begin::date=%s;',
                           (airline_iata_code, route.route_id, scheduled_begin.date()))
            flights_data = cursor.fetchall()
            if flights_data:
                built_flights = []
                for flight_data in flights_data:
                    flight_id = flight_data[0]
                    carrier_code = flight_data[1]
                    scheduled_begin = flight_data[3]
                    scheduled_block = flight_data[4]
                    equipment = Equipment(flight_data[5])
                    actual_begin = flight_data[6]
                    actual_block = flight_data[7]
                    scheduled_itinerary = Itinerary.from_timedelta(begin=utc.localize(scheduled_begin),
                                                                   a_timedelta=scheduled_block)
                    if actual_begin:
                        actual_itinerary = Itinerary.from_timedelta(begin=utc.localize(actual_begin),
                                                                    a_timedelta=actual_block)
                    else:
                        actual_itinerary = None
                    built_flights.append(
                        cls(route=route, scheduled_itinerary=scheduled_itinerary, actual_itinerary=actual_itinerary,
                            equipment=equipment, carrier=carrier_code, event_id=flight_id))
        return built_flights

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            self.scheduled_itinerary.astimezone(begin_timezone=timezone,
                                                end_timezone=timezone)
            if self.actual_itinerary:
                self.actual_itinerary.astimezone(begin_timezone=timezone,
                                                 end_timezone=timezone)
        else:
            self.scheduled_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                end_timezone=self.route.destination.timezone)
            if self.actual_itinerary:
                self.actual_itinerary.astimezone(begin_timezone=self.route.origin.timezone,
                                                 end_timezone=self.route.destination.timezone)

    def __str__(self):
        template = """
        {0.report:%d%b} {0.name:>6s} {0.route.origin} {0.begin:%H%M} {0.route.destination} {0.end:%H%M}\
        {0.duration:2}        {0.equipment}
        """
        return template.format(self)


class DutyDay(object):
    """
    A DutyDay is a collection of Events, it is not a representation of a regular calendar day,
    but rather the collection of Events to be served within a given Duty.
    """

    def __init__(self):
        self.events = []
        self._credits = {}
        self._report = None

    # @classmethod
    # def create_duty_day(cls):
    #     """Enter events into a duty day, one by one"""
    #     answer = 'Y'
    #     event = None
    #     duty_day = cls()
    #     while answer == 'Y':
    #         option = input("Enter F for a new FLIGHT or G for a new GROUND DUTY: ").capitalize()
    #         if option == 'F':
    #             event = Flight(**create_flight_parameters())
    #         elif option == 'G':
    #             event = GroundDuty(**create_ground_duty_parameters())
    #         else:
    #             r = input("Invalid option")
    #
    #         if event:
    #             duty_day.append(event)
    #             print()
    #             print(duty_day)
    #             print()
    #         answer = input("Would you like to add a new event to duty day?  y/n: ").capitalize()
    #         print()
    #         event = None
    #
    #     return duty_day
    #
    @property
    def begin(self):
        return self.events[0].begin

    @property
    def end(self):
        return self.events[-1].end

    @property
    def report(self):
        return self._report if self._report else self.events[0].report

    @property
    def release(self):
        return self.events[-1].release

    @property
    def delay(self):
        delay = Duration.from_timedelta(self.begin - self.report) - Duration(60)
        return delay

    @property
    def duration(self):
        """How long is the DutyDay"""
        return Duration.from_timedelta(self.release - self.report)

    @property
    def turns(self):
        return [Duration.from_timedelta(j.begin - i.end) for i, j in zip(self.events[:-1], self.events[1:])]

    @property
    def origin(self):
        return self.events[0].route.origin

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):
        """Cares only for block, dh, total and daily"""
        # TODO : Take into consideration whenever there is a change in month
        if creditator:
            creditator.credits_from_duty_day(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            for event in self.events:
                event.compute_credits(creditator)
                self._credits['block'] += event._credits['block']
                self._credits['dh'] += event._credits['dh']

            self._credits.update({'daily': self.duration,
                                  'total': self._credits['block'] + self._credits['dh']})
        return [self._credits]

    def append(self, current_duty):
        """Add a duty, one by one  to this DutyDay"""
        self.events.append(current_duty)

    # def merge(self, other):
    #     if self.report <= other.report:
    #         all_events = self.events + other.events
    #     else:
    #         all_events = other.events + self.events
    #     self.events = []
    #     for event in all_events:
    #         self.events.append(event)
    #
    # def how_many_sundays(self):
    #     sundays = []
    #     if self.report.isoweekday() == '7':
    #         sundays.append(self.report.date())
    #     if self.release.isoweekday() == '7':
    #         sundays.append(self.release.date())
    #     return len(sundays)
    #

    def save_to_db(self, container_trip):
        with CursorFromConnectionPool() as cursor:
            report = self.report.time()
            for flight in self.events:
                if not flight.event_id:
                    # First store flight in DB
                    # TODO : Before saving, check that flight does not already exist
                    flight.save_to_db()
                else:
                    cursor.execute('SELECT duty_day_id FROM public.duty_days '
                                   'WHERE flight_id=%s AND trip_id=%s AND trip_date=%s',
                                   (flight.event_id, container_trip.number, container_trip.dated))
                    flight_to_trip_id = cursor.fetchone()
                    if not flight_to_trip_id:
                        cursor.execute('INSERT INTO public.duty_days('
                                       '            flight_id, trip_id, trip_date, '
                                       '            report, dh)'
                                       'VALUES (%s, %s, %s, %s, %s)'
                                       'RETURNING duty_day_id;',
                                       (flight.event_id, container_trip.number, container_trip.dated,
                                        report, flight.dh))
                        flight_to_trip_id = cursor.fetchone()[0]
                report = None
        with CursorFromConnectionPool() as cursor:
            release = self.release.time()
            cursor.execute('UPDATE public.duty_days '
                           'SET rel = %s '
                           'WHERE duty_day_id = %s;',
                           (release, flight_to_trip_id))

    # def update_with_actual_itineraries(self, duty_day):
    #     for flight, actual_flight in zip(self.events, duty_day.events):
    #         flight.actual_itinerary = actual_flight.actual_itinerary

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            for event in self.events:
                event.astimezone(timezone)
        else:
            # TODO : To be implemented
            pass

    def __str__(self):
        """The string representation of the current DutyDay"""
        rpt = '{:%H%M}'.format(self.report)
        rls = '    '
        body = ''
        if len(self.events) > 1:
            for event, turn in zip(self.events, self.turns):
                turn = format(turn, '0')
                body = body + event.as_robust_string(rpt, rls, turn)
                rpt = 4 * ''
            rls = '{:%H%M}'.format(self.release)
            body = body + self.events[-1].as_robust_string(rls=rls)
        else:
            rls = '{:%H%M}'.format(self.release)
            body = self.events[-1].as_robust_string(rpt, rls, 4 * '')

        return body


class Trip(object):
    """
    A trip_match is a collection of DutyDays for a specific crew_base
    """

    def __init__(self, number: str, dated: date, crew_position: str, crew_base: Airport) -> None:
        """A trip is identified by a 4 digit number and its report date.
        Trip's report date should be localized in trip's crew_base
        """
        self.number = number
        self.dated = dated
        self.crew_position = crew_position
        self.crew_base = crew_base
        self._credits = {}
        self.duty_days = []

    # @property
    # def dated(self):
    #     return self.check_in.date()

    # @classmethod
    # def create_trip(cls):
    #     """ Create a trip manually and enter duty days one by one """
    #     answer = 'Y'
    #     trip_number, trip_date = input("Enter trip_number and date v.gr 7009 130818    #").split()
    #     trip_dated = create_date(trip_date)
    #     trip = cls(number=trip_number, dated=trip_dated)
    #     while answer == 'Y':
    #         duty_day = DutyDay.create_duty_day()
    #         trip.append(duty_day)
    #         answer = input("Would you like to add a new duty_day to trip?  y/n: ").capitalize()
    #         print()
    #     return trip
    #

    @classmethod
    def load_by_id(cls, trip_number: str, dated):
        trip = Trip.load_trip_info(trip_number=trip_number, dated=dated)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT duty_days.flight_id, report, rel, trip_date, dh FROM public.duty_days '
                           'INNER JOIN flights ON duty_days.flight_id = flights.flight_id '
                           'WHERE trip_id = %s AND trip_date = %s '
                           'ORDER BY scheduled_begin ASC;',
                           (int(trip_number), dated))
            trip_data = cursor.fetchall()
            duty_day = None
            if trip_data:
                for row in trip_data:
                    if row[1]:
                        # Beginning of a DutyDay
                        duty_day = DutyDay()
                    flight = Flight.load_from_db_by_id(flight_id=row[0])
                    if not flight:
                        print("Enter flight as DDMMYYYY AC#### ORG HHMM DES HHMM EQU")
                        flight_data = input("v.gr. 23062018 0403 MEX 0700 JFK 1300 7S8")
                        flight = Flight.from_string(flight_data)
                        flight.save_to_db()
                    if row[4]:
                        # dh boolean indicates this flight is a DH flight
                        flight.dh = True
                    duty_day.append(flight)
                    if row[2]:
                        # Ending of a DutyDay
                        trip.append(duty_day)
        return trip

    @classmethod
    def load_trip_info(cls, trip_number: str, dated):
        """
        Used as a simple read from trip information

        """
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * '
                           'FROM trips '
                           'WHERE number = %s AND dated = %s ',
                           (int(trip_number), dated))
            trip_data = cursor.fetchone()
            if trip_data:
                trip = cls(number=trip_number, dated=trip_data[1], crew_position=trip_data[6], crew_base=trip_data[7])
                return trip
            else:
                raise UnstoredTrip

    @property
    def report(self):
        return self.duty_days[0].report

    @property
    def release(self):
        return self.duty_days[-1].release

    @property
    def rests(self):
        """Returns a list of all calculated rests between each duty_day"""
        return [Duration.from_timedelta(j.report - i.release) for i, j in zip(self.duty_days[:-1], self.duty_days[1:])]

    @property
    def layovers(self):
        """Returns a list of all layover stations """
        return [duty_day.events[-1].destination for duty_day in self.duty_days]

    @property
    def duration(self):
        "Returns total time away from base or TAFB"
        return Duration.from_timedelta(self.release - self.report)

    def get_elapsed_dates(self):
        """Returns a list of dates in range [self.report, self.release]"""
        delta = self.release.date() - self.report.date()
        all_dates = [self.report.date() + timedelta(days=i) for i in range(delta.days + 1)]
        return all_dates

    def compute_credits(self, creditator=None):

        if creditator:
            return creditator.credits_from_trip(self)
        else:
            self._credits['block'] = Duration(0)
            self._credits['dh'] = Duration(0)
            self._credits['daily'] = Duration(0)
            for duty_day in self.duty_days:
                duty_day.compute_credits(creditator)
                self._credits['block'] += duty_day._credits['block']
                self._credits['dh'] += duty_day._credits['dh']
                self._credits['daily'] += duty_day._credits['daily']
            self._credits.update({'total': self._credits['block'] + self._credits['dh'],
                                  'tafb': self.duration})

    def append(self, duty_day):
        """Simply append a duty_day"""
        self.duty_days.append(duty_day)

    def pop(self, index=-1):
        return self.duty_days.pop(index)

    # def how_many_sundays(self):
    #     sundays = filter(lambda date: date.isoweekday() == 7, self.get_elapsed_dates())
    #     return len(list(sundays))
    #
    # def __delitem__(self, key):
    #     del self.duty_days[key]
    #
    # def __getitem__(self, key):
    #     try:
    #         item = self.duty_days[key]
    #     except:
    #         item = None
    #     return item
    #
    # def __setitem__(self, key, value):
    #     self.duty_days[key] = value

    def astimezone(self, timezone='local'):
        """Change event's itineraries to given timezone"""
        if timezone != 'local':
            for duty_day in self.duty_days:
                duty_day.astimezone(timezone)
        else:
            # TODO : To be implemented
            print("duty_daty.astimzone('local') needs to be implemented ")
            pass

    def __str__(self):
        self.compute_credits()
        header_template = """
        # {0.number}                                                  CHECK IN AT {0.report:%H:%M}
        {0.report:%d%b%Y}
        DATE  RPT  FLIGHT DEPARTS  ARRIVES  RLS  BLK        TURN        EQ"""

        body_template = """{duty_day}
                     {destination} {rest}                   {block:0}BL {dh:0}CRD {total:0}TL {daily:0}DY"""

        footer_template = """

          TOTALS     {total:2}TL     {block:2}BL     {dh:2}CR           {tafb:2}TAFB"""

        header = header_template.format(self)
        body = ''

        for duty_day, rest in zip(self.duty_days, self.rests):
            rest = repr(rest)
            body = body + body_template.format(duty_day=duty_day,
                                               destination=duty_day.events[-1].route.destination,
                                               rest=rest,
                                               **duty_day._credits)
        else:
            duty_day = self.duty_days[-1]
            body = body + body_template.format(duty_day=duty_day,
                                               destination='    ',
                                               rest='    ',
                                               **duty_day._credits)

        footer = footer_template.format(**self._credits)
        return header + body + footer

    def save_to_db(self):
        """Save to db should be only concerned with saving a trip regardless of
           its previous status, i.e. if it has been stored before or not

           Before storing a Trip it must be converted to utc time
        """
        self.astimezone(utc)
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM public.trips '
                           'WHERE trips.number=%s AND trips.dated=%s', (self.number, self.dated))
            trip_data = cursor.fetchone()

            if not trip_data:
                cursor.execute('INSERT INTO public.trips (number, dated, crew_position, crew_base) '
                               'VALUES (%s, %s, %s, %s);', (self.number, self.dated, self.crew_position,
                                                            self.crew_base.iata_code))
        for duty_day in self.duty_days:
            duty_day.save_to_db(self)
    #
    # def update_with_actual_itineraries(self, actual_trip):
    #     """Beacuse self.trip already has all published information loaded from the DB,
    #     this method allows to insert missing actual information for all duties within"""
    #     for duty_day, actual_duty_day in zip(self.duty_days, actual_trip.duty_days):
    #         duty_day.update_with_actual_itineraries(duty_day=actual_duty_day)
    #
    # def update_from_database(self):
    #     """ 1. Loop over each event
    #         2. Load each event's stored data
    #     """
    #     for duty_day in self.duty_days:
    #         for event in duty_day.events:
    #             event.update_from_database()
