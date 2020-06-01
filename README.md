# Scheduling Optmization 

-----

Jun-1
-----

### data\_process.py

**A new function added:** def clean\_detail\_room\_data(filepath, buildings).

This is the data cleaning of new room raw data with deta​​il capacity information. The output format should be same as the above function. I kept the previous one, so you can choose use which one in your formulation.

### set\_process.py

**1\. set `T_x` changed:** since the timeslots are fixed, the timeslot of the section should be same as 2019.

```python
  T_x = dict()
    for x in X:
        T_x[x] = course_data[course_data["subject_number_section_orrurance"] == x]["full_time"].tolist()
```

**2\. New sets added:**

`n_rf`: capacity of room r under safe distance f

`S_x`: the set of students choosing section x.

`p_x`: class size of section x.

`X_wo_room`: a set of sections that have no room assignment in 2019 fall

`X_wo_time`: a set of sections that have no time assignment in 2019 fall

`F:` Safe distance level `[0, 6, 8, 12]`

`k_f:` risk factors when not achieve f safe distance. `{0:10000,6:20,8:10,12:5}`

### assignment\_opt.py

Room assignment optimization model.
