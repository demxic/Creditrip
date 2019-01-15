from data.exceptions import TripBlockError, UnbuiltTripError, DutyDayBlockError, UnstoredTrip
from models.scheduleClasses import Trip, DutyDay, Flight, Airport, Route, Itinerary, Equipment
from models.timeClasses import DateTimeTracker
import pytz

utc = pytz.utc


# TODO : El horario de verano en MEX concluye en octubre a las 03:00 pytz no registra esto, ya envie rprt

def build_carrier(flight_dict):
    carrier_code = 'AM'
    code = flight_dict['name'][0:2]
    if code.startswith('DH'):
        # Found an AM or 6D flight
        if flight_dict['equipment'] == 'DHD':
            carrier_code = '6D'
    elif not code.isdigit():
        # Found a new airline
        carrier_code = code
    return carrier_code


def build_route(name: str, origin: Airport, destination: Airport) -> Route:
    route_key = name + origin.iata_code + destination.iata_code
    if route_key not in Route._routes:
        # Route has not been loaded from the DB
        route = Route.load_from_db_by_fields(name=name,
                                             origin=origin,
                                             destination=destination)
        if not route:
            # Route must be created and stored into DB
            route = Route(name=name, origin=origin, destination=destination)
            route.save_to_db()
    else:
        route = Route._routes[route_key]
    return route


def build_flight(dt_tracker: DateTimeTracker, flight_dict: dict) -> Flight:
    # 1. Get the route
    origin = Airport.load_from_db_by_iata_code(flight_dict['origin'])
    destination = Airport.load_from_db_by_iata_code(flight_dict['destination'])
    route = build_route(flight_dict['name'][-4:], origin, destination)

    # 2. We need the airline code
    carrier_code = build_carrier(flight_dict)

    # 3. Find the flight in the DB
    begin = dt_tracker.build_end_dt(time_string=flight_dict['begin'],
                                    destination_timezone=origin.timezone)

    flight_list = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
                                           scheduled_begin=begin.astimezone(utc),
                                           route=route)

    # 4. Create and store flight if not found in the DB
    if not flight_list:
        # 4.a Found a regular flight, create it
        end = dt_tracker.build_end_dt(time_string=flight_dict['end'],
                                      destination_timezone=destination.timezone)
        itinerary = Itinerary(begin=begin.astimezone(utc), end=end.astimezone(utc))
        itinerary.begin_timezone = begin.tzinfo
        itinerary.end_timezone = end.tzinfo
        equipment = Equipment(flight_dict['equipment'])
        flight = Flight(route=route, scheduled_itinerary=itinerary,
                        equipment=equipment, carrier=carrier_code)
        flight.save_to_db()
    else:
        if len(flight_list) > 1:
            print("Choose the right flight for this trip: ")
            for index, flight in enumerate(flight_list):
                print(index, flight.astimezone('local'))
            flight = flight_list[input("option: ")]
        else:
            flight = flight_list[0]
            flight.astimezone(timezone='local')
            dt_tracker.dt = flight.end

        # dt_tracker.astimezone(destination.timezone)

    flight.dh = not flight_dict['name'].isnumeric()
    return flight


def build_duty_day(dt_tracker, duty_day_dict):
    """Returns a DutyDay object from a dictionary"""
    duty_day = DutyDay()
    dt_tracker.build_date(month=duty_day_dict['month'], day=duty_day_dict['day'])
    for flight_dict in duty_day_dict['flights']:
        flight = build_flight(dt_tracker, flight_dict)
        if flight:
            duty_day.append(flight)

    # Assert that duty day was built properly
    if str(duty_day.duration) != duty_day_dict['dy']:
        raise DutyDayBlockError(duty_day_dict, duty_day)

    return duty_day


def build_trip(trip_dict: dict) -> Trip:
    """Given a trip_dict turn it into a Trip object"""

    try:
        trip = Trip.load_trip_info(trip_number=trip_dict['number'], dated=trip_dict['dated'])
        print("Trip {} dated {} was already stored!".format(trip_dict['number'], trip_dict['dated']))

    except UnstoredTrip as e:
        crew_base = Airport.load_from_db_by_iata_code(trip_dict['crew_base'])
        dt_tracker = DateTimeTracker(date=trip_dict['dated'], time=trip_dict['check_in'], timezone=crew_base.timezone)
        trip = Trip(number=trip_dict['number'], dated=dt_tracker.dt.date(), crew_position=trip_dict['position'],
                    crew_base=crew_base)
        for duty_day_dict in trip_dict['duty_days']:
            try:
                duty_day = build_duty_day(dt_tracker, duty_day_dict)
                trip.append(duty_day)

            except DutyDayBlockError as e:
                # TODO : Add method to correct flight
                print("For trip {0} dated {1}, ".format(trip_dict['number'], trip_dict['dated']), end=' ')
                print("found inconsistent duty day : ")
                print("       ", e.duty_day)
                raise UnbuiltTripError

        if trip.duration.no_trailing_zero() != trip_dict['tafb']:
            raise TripBlockError(trip_dict['tafb'], trip)
        else:
            trip.save_to_db()
            print("Trip {0.number} dated {0.dated} saved".format(trip))

    return trip


def build_trips(trips_as_dict: list, position: str, crew_base: str):
    """trip_as_dict fields:

    number: 4 digit str
    check_in: str representing time as HH:MM or %H:%M
    dated: str representing a date as DDMMMYY or %d%b%Y
    duty_days: list of duty_days; each duty_day is also a dictionary cf.
    tl: total block + credit time represented as an HH:MM str
    bl: total block time as an HH:MM str
    cr: total credit time as an HH:MM str
    tafb: Time Away From Base as an HH:MM str
    date_and_time: DDMMMYYHH:MM as a str
    position: SOB or EJE str
    """
    trip_dict_count = 0
    unstored_trips = list()
    for trip_as_dict in trips_as_dict:
        try:
            trip_as_dict['position'] = position
            trip_as_dict['crew_base'] = crew_base
            build_trip(trip_dict=trip_as_dict)
            trip_dict_count += 1

        except TripBlockError as e:
            # TODO : Granted, there's a trip block error, what actions should be taken to correct it? (missing)
            print("trip {0.number} dated {0.dated} {0.duration}"
                  " does not match expected TAFB {1}".format(e.trip, e.expected_block_time))
            print("Trip {0} dated {1} unsaved!".format(trip_as_dict['number'], trip_as_dict['dated']))
            unstored_trips.append(trip_as_dict)

        except UnbuiltTripError:
            print("Trip {0} dated {1} unsaved!".format(trip_as_dict['number'], trip_as_dict['dated']))
            unstored_trips.append(trip_as_dict)

    print("{} dict trips proccesed! ".format(trip_dict_count))
    return unstored_trips
