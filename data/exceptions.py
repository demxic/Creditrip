from models.scheduleClasses import DutyDay, Itinerary


class MissingAirport(Exception):

    def __init__(self, missing_airport: str):
        super().__init__("{} airport not stored in the DB".format(missing_airport))
        self.airport_iata_code = missing_airport


class DutyDayBlockError(Exception):

    def __init__(self, duty_day_dict: dict, duty_day: DutyDay) -> None:
        super().__init__("DutyDay's expected daily time {} is different from actual {}".format(duty_day_dict['dy'],
                                                                                               duty_day.duration))
        self.duty_day_dict = duty_day_dict
        self.duty_day = duty_day

    def delete_invalid_flights(self):
        found_one_after_dh = False
        for flight in self.duty_day.events:
            if not flight.name.isnumeric() or found_one_after_dh:
                # TODO : Instead of deleting flight, try erasing only the inconsistent data
                print("Dropping from DataBase flight: {} ".format(flight))
                flight.delete()
                found_one_after_dh = True

    def correct_invalid_events(self):
        for flight in self.duty_day.events:
            print(flight)
            r = input("Is flight properly built? y/n").capitalize()
            if 'N' in r:
                itinerary_string = input("Enter itinerary as string (date, begin, blk) 31052018 2206 0122 ")
                itinerary = Itinerary.from_string(itinerary_string)
                flight.scheduled_itinerary = itinerary
                flight.update_to_db()


class TripBlockError(Exception):

    def __init__(self, expected_block_time, trip):
        super().__init__("Trip's expected block time {} is different from actual {}"
                         "".format(expected_block_time, trip.duration))
        self.expected_block_time = expected_block_time
        self.trip = trip

    def delete_invalid_duty_days(self):
        pass


class UnbuiltTripError(Exception):
    pass


class UnstoredTrip(Exception):
    pass


class UndefinedBlockTime(Exception):
    pass
