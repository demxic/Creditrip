import pickle
import sys
from pathlib import Path

from App.ObjectBuilders import build_trips
from FileParsers.filereaders import verify_files, page_number_remover, create_trips_as_dict, number_of_trips_in_pbs_file
from data.database import Database

from models.scheduleClasses import Trip

files = []
data_folder = Path("C:/Users/Xico/Google Drive/Sobrecargo/PBS/2019 PBS/201901 PBS")
pickled_unsaved_trips_file = 'pickled_unsaved_trips'
Database.initialise(database="orgutrip", user="postgres", password="0933", host="localhost")


class Menu:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self.choices = {
            "1": self.choose_trip_files,
            "2": self.parse_trips_from_files,
            "3": self.figure_out_unsaved_trips,
            "4": self.search_for_trip,
            "5": self.choose_reserve_files,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Elejir los archivos con los trips.
        2. Leer cada archivo con los trips y generar los objetos.
        3. Trabajar con los trips que no pudieron ser creados.
        4. Buscar un trip en especìfico.
        5. Leer los archivos con las reservas.
        10. Quit
        ''')

    def run(self):
        """Display the menu and respond to choices"""
        while True:
            self.display_menu()
            choice = input("¿Qué deseas realizar?: ")
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print("{0} is not a valid choice".format(choice))

    def choose_trip_files(self):
        """This option chooses the files that are to be read and turned into meaningful data

        """
        global files, data_folder
        file_names = ["201901 - PBS vuelos SOB A.txt",
                      "201901 - PBS vuelos SOB B.txt",
                      "201901 - PBS vuelos EJE.txt"]
        files = verify_files(data_folder, file_names)

    def parse_trips_from_files(self):
        """Will read each pbs trip file and turn it into usable dictionaries

        First run: from scaderd data in the pbs file to readable strings
        Second run: from strings into dictionaries
        Third run: from dictionaries into objects"""
        
        unstored_trips = list()
        for file in files:
            # 1. Read in and clean the txt.file
            print("\n Parsing file : {}".format(file))
            position = input("Is this a PBS file for EJE or SOB? ").upper()
            crew_base = 'MEX'
            cleaned_content = page_number_remover(file)
            total_trips_in_pbs_file = number_of_trips_in_pbs_file(cleaned_content)
            trips_as_dict = create_trips_as_dict(trips_as_strings=cleaned_content)
            if total_trips_in_pbs_file != len(trips_as_dict):
                print("Warning! {} trips should be processed but only {} were found".format(
                    total_trips_in_pbs_file, len(trips_as_dict)
                ))
            pending_trips = build_trips(trips_as_dict, position, crew_base=crew_base)
            print("{} trips contained in PBS pdf file".format(total_trips_in_pbs_file))
            print("{} trips were not built!".format(len(pending_trips)))
            unstored_trips.extend(pending_trips)
        outfile = open(data_folder / pickled_unsaved_trips_file, 'wb')
        pickle.dump(unstored_trips, outfile)
        outfile.close()

    def figure_out_unsaved_trips(self):
        infile = open(data_folder / pickled_unsaved_trips_file, 'rb')
        unstored_trips = pickle.load(infile)
        print("Listing {} unsaved_trips :".format(len(unstored_trips)))
        for trip_dict in unstored_trips:
            print("Trip {}/{} unsaved!".format(trip_dict['number'], trip_dict['dated']))
        # 1. Let us go over all trips again, some might now be discarded
        # irreparable_trips = build_trips(unstored_trips, None, postpone=False)
        # print(" {} unsaved_trips".format(len(irreparable_trips)))
        # outfile = open(data_folder / pickled_unsaved_trips_file, 'wb')
        # pickle.dump(irreparable_trips, outfile)
        # outfile.close()

    def search_for_trip(self):
        entered = input("Enter trip/dated to search for ####/YYYY-MM-DD ")
        trip_id, trip_dated = entered.split('/')
        trip = Trip.load_by_id(trip_id, trip_dated)
        print(trip)

    def choose_reserve_files(self):
        """This option chooses the files that are to be read and turned into meaningful data

                """
        global files, data_folder
        file_names = ["201901 - PBS reservas SOB A.txt",
                      "201901 - PBS reservas EJE.txt"]
        files = verify_files(data_folder, file_names)

    def quit(self):
        print("adiós")
        sys.exit(0)


if __name__ == '__main__':
    Menu().run()
