import sys
from pathlib import Path
from FileParsers.filereaders import verify_files

files = None

class Menu:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self.choices = {
            "1": self.choose_trip_files,
            "2": self.parse_trips_from_files,
            "3": self.figure_out_unsaved_trips,
            "4": self.search_for_trip,
            "5": self.read_reserve_file,
            "10": self.quit}

    @staticmethod
    def display_menu():
        print('''
        Orgutrip Menu

        1. Leer los archivos con los trips.
        2. Trabajar con los trips que no pudieron ser creados.
        3. Buscar un trip en especìfico.
        4. Leer los archivos con las reservas.
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
        global files
        data_folder = Path("C:/Users/Xico/Google Drive/Sobrecargo/PBS/2018 PBS/201810 PBS")
        file_names = ["201810 - PBS vuelos SOB A.txt", 
                      "201810 - PBS vuelos SOB B.txt",
                      "201810 - PBS vuelos EJE.txt"]
        files = verify_files(data_folder, file_names)

        # import re
        # with open(file_to_open, 'r') as f:
        #     content = f.read()
        #     content_new = re.sub('=+\d+=+', '', content, flags=re.M)
        # with open(file_to_open, 'w') as f:
        #     f.write(content_new)
        
    def parse_trips_from_files(self):
        print(files)

    def figure_out_unsaved_trips(self):
        pass

    def search_for_trip(self):
        pass

    def read_reserve_file(self):
        pass

    def quit(self):
        print("adiós")
        sys.exit(0)


if __name__ == '__main__':
    Menu().run()
