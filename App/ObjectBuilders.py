import datetime

from data.exceptions import TripBlockError, UnbuiltTripError, DutyDayBlockError
from models.scheduleClasses import Trip, DutyDay, Flight, Airport, Route, Itinerary, Equipment
from models.timeClasses import DateTimeTracker
from copy import copy


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


def build_flight(dt_tracker: DateTimeTracker, flight_dict: dict,
                 postpone: bool) -> Flight:
    # TODO: Rename dt_tracker to date_time_tracker
    # 1. Get the route
    # take into consideration the last 4 digits Because some flights start with 'DH'
    # origin = get_airport(flight_dict['origin'])
    # destination = get_airport(flight_dict['destination'])
    origin = Airport.load_from_db_by_iata_code(flight_dict['origin'])
    destination = Airport.load_from_db_by_iata_code(flight_dict['destination'])
    route = build_route(flight_dict['name'][-4:], origin, destination)

    # 2. We need the airline code
    carrier_code = build_carrier(flight_dict)

    # 3. Find the flight in the DB
    begin = copy(dt_tracker.dt)
    flight = None
    # flight = Flight.load_from_db_by_fields(airline_iata_code=carrier_code,
    #                                        scheduled_begin=begin,
    #                                        route=route)

    # 4. Create and store flight if not found in the DB
    if not flight:

        # 4.a Found a regular flight, create it
        end = dt_tracker.no_name(time_string=flight_dict['end'],
                                 destination_timezone=destination.timezone)
        itinerary = Itinerary(begin=begin, end=end)
        equipment = Equipment(flight_dict['equipment'])
        flight = Flight(route=route, scheduled_itinerary=itinerary,
                        equipment=equipment, carrier=carrier_code)
        #flight.save_to_db()

    flight.dh = not flight_dict['name'].isnumeric()
    return flight


def build_duty_day(dt_tracker, duty_day_dict, postpone):
    """Returns a DutyDay object from a dictionary"""
    duty_day = DutyDay()

    for flight_dict in duty_day_dict['flights']:
        flight = build_flight(dt_tracker, flight_dict, postpone)
        if flight:
            duty_day.append(flight)
            dt_tracker.forward(flight_dict['turn'])
    dt_tracker.release()
    dt_tracker.forward(duty_day_dict['layover_duration'])

    # Assert that duty day was built properly
    if str(duty_day.duration) != duty_day_dict['dy']:
        raise DutyDayBlockError(duty_day_dict, duty_day)

    return duty_day


def build_trip(trip_dict: dict, postpone: bool) -> Trip:
    # TODO : timezone parameter inside DateTimeTracker should be a variable
    base_timezone = Airport.load_from_db_by_iata_code('MEX').timezone
    dt_tracker = DateTimeTracker(begin=trip_dict['dated']+trip_dict['check_in'],
                                 timezone=base_timezone)
    trip = Trip(number=trip_dict['number'], check_in=dt_tracker.dt)
    if trip.number == '5525':
         s = input()
    for duty_day_dict in trip_dict['duty_days']:
        try:
            dt_tracker.start()
            duty_day = build_duty_day(dt_tracker, duty_day_dict, postpone)
            trip.append(duty_day)

        except DutyDayBlockError as e:
            print("For trip {0} dated {1}, ".format(trip_dict['number'], trip_dict['dated']), end=' ')
            print("found inconsistent duty day : ")
            print("       ", e.duty_day)
            if postpone:
                e.delete_invalid_flights()
                raise UnbuiltTripError
            else:
                print("... Correcting for inconsistent duty day: ")
                e.correct_invalid_events()
                print("Corrected duty day")
                print(e.duty_day)
                trip.append(e.duty_day)

    return trip
# def build_trip(trip_dict: dict, postpone: bool) -> Trip:
#     dt_tracker = DateTimeTracker(trip_dict['date_and_time'])
#     trip = Trip(number=trip_dict['number'], dated=dt_tracker.date)
#
#     for json_dd in trip_dict['duty_days']:
#         try:
#             duty_day = build_duty_day(dt_tracker, json_dd, postpone)
#             trip.append(duty_day)
#
#         except DutyDayBlockError as e:
#             print("For trip {0} dated {1}, ".format(trip_dict['number'], trip_dict['dated']), end=' ')
#             print("found inconsistent duty day : ")
#             print("       ", e.duty_day)
#             if postpone:
#                 e.delete_invalid_flights()
#                 raise UnbuiltTripError
#             else:
#                 print("... Correcting for inconsistent duty day: ")
#                 e.correct_invalid_events()
#                 print("Corrected duty day")
#                 print(e.duty_day)
#                 trip.append(e.duty_day)
#
#     return trip


def build_trips(trips_as_dict, position, postpone=True):
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
        if 'position' not in trip_as_dict:
            trip_as_dict['position'] = position
        try:
            trip = build_trip(trip_as_dict, postpone)
            trip_dict_count += 1
            if trip.duration.no_trailing_zero() != trip_as_dict['tafb']:
                print(trip_as_dict)
                raise TripBlockError(trip_as_dict['tafb'], trip)

        except TripBlockError as e:
            # TODO : Granted, there's a trip block error, what actions should be taken to correct it? (missing)
            print("trip {0.number} dated {0.dated} {0.duration}"
                  " does not match expected TAFB {1}".format(e.trip, e.expected_block_time))
            print("Trip {0} dated {1} unsaved!".format(trip_as_dict['number'], trip_as_dict['dated']))
            unstored_trips.append(trip_as_dict)

        except UnbuiltTripError:
            print("Trip {0} dated {1} unsaved!".format(trip_as_dict['number'], trip_as_dict['dated']))
            unstored_trips.append(trip_as_dict)

        else:
            print("Trip {0.number} dated {0.dated} saved".format(trip))
            trip.position = position
            # trip.save_to_db()

    print("{} json trips found ".format(trip_dict_count))
    return None
    #return unstored_trips
