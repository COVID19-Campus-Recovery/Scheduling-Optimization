# CCMAP

-----
## Purpose

This codebase was initially developed during the start of the Covid-19 pandemic at the Georgia Institue of Technology. At this time, university campuses began considering the need for physical (or ‘social’) distancing. While physical distancing is an important public health intervention
during airborne pandemics, physical distancing dramatically reduces the effective capacity of classrooms. This presented a unique problem to campus planners who hoped to deliver a meaningful amount of in-person instruction in a way that respected physical distancing. This process involved 1) assigning a mode to each offered class as either remote, residential (in-person) or hybrid, and 2) reassigning classrooms under severely reduced capacities to the non-remote classes. These decisions need to be made quickly and under several constraints and competing priorities such as restrictions on changes to the timetable of classes, trade-offs between classroom density and educational benefits of in-person vs. online instruction, and administrative preferences for course modes and classrooms reassignments.

Specifically, this package implements an hierarchnical integer program to handle the multiple criteria according to priorities. The criteria considereed are: maximizing satisfaction of mode preferences, maximizing in-person contact hours, and minimizing classroom reallocation.

For more details regarding the mathematical model, please reference:

Navabi-Shirazi, Mehran, Mohamed El Tonbari, Natashia Boland, Dima Nazzal, and Lauren N. Steimle. ``[Multi-criteria Course Mode Selection and Classroom Assignment Under Sudden Space Scarcity](http://www.optimization-online.org/DB_FILE/2021/08/8527.pdf)" _Manufacturing & Service Operations Management_ (Forthcoming)

If you make use of this package, please cite the above article.

This package may be particularly valuable in the event that the Covid-19 pandemics, or future airborn pandemics, again increase the need for physical distancing, and thereby result in sudden space scarcity for universities.

-----
## Installation

Gurobi 9.1.0 and the gurobipy package are required and can be downloaded from Gurobi's website.

Additional python requirements can be installed via:

```pip3 install -r requirements.txt```

-----
## How to Use

The optimization model can be run by using the following command:

```python3 room_assignment_stability_mode_preferences_contact_opt.py <course section file name> <classroom file name> <building coordinates file name> <folder to store output file> <mininum number of touch poitns (int)> <number of weeks in the semester (int)>```

The three input files (course, classroom, building coordinates) may be csv or excel.

Please refer to the input files in the example directory for reference on how to structure the input files.


-----
## Credits

Faculty advisors and collaborators: Dr. Lauren N. Steimle, Dr. Dima Nazzal, Dr. Natashia Boland

Project developers: Mehran Navabi-Shirazi, Dr. Mohamed El Tonbari, Kaiwen Luo, Dr. Faramroze Engineer

This work was supported by a grant from the Thos and Clair Muller Research Endowment Fund of the Georgia Institute of Technology’s H. Milton Stewart School of Industrial and Systems Engineering, and a grant from the Georgia Institute of Technology Executive Vice President for Research COVID-19 Rapid Response Seed Grant Program. 

