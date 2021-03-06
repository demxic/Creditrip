import re

#*******************************************************************
# FOLLOWING REGEX ARE USED TO IDENTIFY OBJECTS WHEN READING PBS FILES
#
#*******************************************************************
# Used to find the total number of trips stored in the PBS file
trips_total_RE = re.compile(r"""
    trips:\s+       #The Total number of trips legend followed by one ore more white spaces 
    (?P<trips_total>\d{1,4})        #Up to 4 digit total number of trips in the PBS trips file
    """, re.VERBOSE | re.DOTALL)

# Used to find page numbers in a PBS_trips_file
page_number_RE = re.compile(r"""
    =+\d+=+
    """, re.VERBOSE | re.DOTALL)

# Used to read a flight form a PBS_trips_file
flights_RE = re.compile(r"""
    (?P<name>\w{4,6})\s+            #4 digits for FLIGHT number
    (?P<origin>[A-Z]{3})\s          #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s+             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s     #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})\s+               #4 digit end time
    (?P<blk>\d{4})\s+               #4 digits for RLS or BLK time.  
    (?P<turn>\d{4})\s+              #4 digits for BLK or TURN time.
    (?P<equipment>\w{3})            #3 digits for EQ
    """, re.VERBOSE)

# Used to parse a duty day from a PBS_trips_file
dutyday_RE = re.compile(r'''
    (?P<day>\d{2})                               #DD departure day for the first flight in the dutyday
    (?P<month>[A-Z]{3})\s+                       #MMM departure month for the first flight in the dutyday
    (?P<report>\d{4})\s+                         #duty day's first flight report time
    (?P<flights>.*?)                             #All flights data to be further examined
    ((?P<layover_city>[A-Z]{3})\s+               # Layover city      v.gr. GDL
     (?P<layover_duration>\d{2,3}:\d{2}))?\s+      # Layover duration  v.gr. 23:54
    (?P<bl>\d{4})BL\s+                           #As a named group ---> (?P<bl>\d{4})BL\s+
    (?P<crd> [-\d]{4,5})CRD\s+                          #As a named group ---> (?P<crd>\d{4})CRD\s+
    (?P<tl>\d{4})TL\s+                               #As a named group ---> (?P<tl>\d{4})TL\s+
    (?P<dy>\d{4})DY                                  #As a named group ---> (?P<dy>\d{4})DY
    ''', re.VERBOSE | re.DOTALL)

# Used to parse a trip from a PBS_trips_file
trip_RE = re.compile(r"""
    \#\s*                           #Ignore the first hashtag and whitespace
    (?P<number>\d{4})\s*             #Next comes the Trip number or TripId
    .*?                             #We don't care for the "CHECK IN AT" legend that follows
    (?P<check_in>\d{2}:\d{2})\s*    #Only for the actual_itinerary check in time
    (?P<dated>\d{2}[A-Z]{3}\d{4})\s*#But we are interested in the trip_match's starting date
    (?P<duty_days>.*?)              #What comes next are all further dutydays to be examined.
    TOTALS\s*                       #And down here come all credits for the trip_match, just in case
    (?P<tl>\d{1,2}:\d{2})TL\s*
    (?P<bl>\d{1,2}:\d{2})BL\s*
    (?P<cr>\d{1,2}:\d{2})CR\s*
    (?P<tafb>\d{1,3}:\d{2})TAFB
    """, re.VERBOSE | re.DOTALL)

#*******************************************************************
# WHILE THIS REGEX ARE USED WHEN READING ROSTER FILES
#
#*******************************************************************
roster_data_RE = re.compile(r'''
    (?P<month>\w{3,10})\s+         #Any month from enero to diciembre (or january to december) 
    (?P<year>\d{4})\s+             #4 digit year, v.gr. 2018 
    (?P<header>.+)
    DH:\s+                         #Header ends when DH:  3:45 is found
    (?P<DH>\d{1,2}:\d{1,2}).+      
    DAY.+?DH\s+
    (?P<body>.*)                   #What comes next is the body
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

# RegEx que se debe utilizar cuando el rol no contiene Crew Type
crewstats_no_type = re.compile(r"""
    (?P<crew_member_id>\d{6})\s+    #6 digits at start followed by one or more spaces        v.gr. 102711
    (?P<name>(\w{1,12}|(\w{1,11}\s\w{1,11})))\s+           #One or twelve alphanumeric crew member line name        v.gr. XICOTENCATL
    (?P<pos>[A-Z]{3})\s+            #Three letter postion id                                 v.gr. SOB
    (?P<group>\w{4})\s+             #Group for member                                        v.gr. S001
    (?P<base>[A-Z]{3})\s+           #Three letter code for homebase airport                  v.gr. MEX
    (?:\d)\s+                       #Line number, whatever that means                        v.gr. 0
    (?P<seniority>\d{1,4})\s+       #Crewmember's line number                                v.gr. 694
    (Time\sZone:)
    (?P<timeZone>\w).*              #TimeZone for all events                                v.gr. Time
    """, re.VERBOSE | re.IGNORECASE)

carryInRE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - or a whitespace
    (?:\s|-)
    (?P<endDay>\w{2})\s+           #The day when the sequence ends (if any)        v.gr. 07-08
    ''', re.VERBOSE)

non_trip_RE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - 
    -
    (?P<end_day>\d{2})\s+          #The day when the sequence ends (if any)        v.gr. 07-08
    (?P<name>[A-Z]{1,2}|[A-Z]\d)\s+#One or two letters or a letter and a digit
    ''', re.VERBOSE | re.DOTALL)

roster_trip_RE = re.compile(r'''
    (?P<day>\d{2})\s+
    (?P<end_day>[A-Z]{2})\s+
    (?P<name>\d{4})\s+
    (?P<flights>(\w{4,6}\s+\w{3}\s+\d{4}\s+\w{3}\s+\d{4}\s+)+)
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

airItineraryRE = re.compile(r"""
    (?P<name>\w{4,6})\s          #An opt 2char airlinecode + 4 digit number + " "    v.gr   AM0001, DH0403, 0170
    (?P<origin>[A-Z]{3})\s         #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s    #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})                 #4 digit end time
    """, re.VERBOSE)