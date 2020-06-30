import unittest
import data_process as dp
import set_process as sp
import pandas as pd

def instantiate_room_assignment_model():

    course_data_filepath = "~/Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_courses_example.xlsx"
    room_data_filepath = "~/Documents/Madgie_Cleaned_Directory/Data/room_assignment_opt_rooms_example.xlsx"
    course_data = dp.read_and_clean_course_data(course_data_filepath)
    room_data = dp.read_and_clean_room_data(room_data_filepath)
    assign_opt = RoomAssignmentOpt(course_data, room_data)
    return assign_opt

def instantiate_mock_course(course_attribute_val_dict):
	if any(key not in dp.course_columns for key in course_attribute_val_dict.keys()):
		raise Exception('Course attributes {} not in {}'.format(course_attribute_val_dict.keys(), dp.course_columns))
	course_row = pd.DataFrame(columns = dp.course_columns)
	course_row = course_row.append(course_attribute_val_dict, ignore_index=True)
	return course_row

class TestSetProcesses(unittest.TestCase):

	def test_get_section_set(self):
		# Add two unique sections for course 0001
		course_data = instantiate_mock_course({"subject_code" : 'SUBJ0', "course_number" : '0001', "course_section" : 'A'})
		course_data = course_data.append(instantiate_mock_course({"subject_code" : 'SUBJ0', "course_number" : '0001', "course_section" : 'B'}))
		# Add two duplicate setions for course 0002
		course_data = course_data.append(instantiate_mock_course({"subject_code" : 'SUBJ0', "course_number" : '0002', "course_section" : 'A'}))
		course_data = course_data.append(instantiate_mock_course({"subject_code" : 'SUBJ0', "course_number" : '0002', "course_section" : 'A'}))
		course_data = dp.clean_course_data(course_data)
		self.assertTrue(len(course_data) == 4)

		# test number of sections with no courses
		section_course_dict = sp.get_section_set(course_data, set())
		self.assertTrue(len(section_course_dict) == 0)
		# test number of sections for 0001, 0002, 0003, and empty course
		all_courses = sp.get_all_courses(course_data)
		section_course_dict = sp.get_section_set(course_data, all_courses)
		self.assertTrue(len(section_course_dict) == 3)
		self.assertTrue(len(section_course_dict['SUBJ0_0001_A']) == 1)
		self.assertTrue(len(section_course_dict['SUBJ0_0001_B']) == 1)
		self.assertTrue(len(section_course_dict['SUBJ0_0002_A']) == 2)

	def test_get_overlapping_time_slots_time_overlap(self):

		all_timeslot = ['MWF_800_900', 'MWF_900_1000','MWF_1000_1100', 'MWF_1100_1200', 'MWF_1200_1300', 'MWF_1300_1400', 'MWF_1400_1500', 'MWF_1500_1600']
		
		#test single time 
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'MWF_1300_1400'), {'MWF_1300_1400'})

		#no overlap
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'MWF_600_700'), set())

		#multiple overlap, between times. Should only return earlier time
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'MWF_1230_1330'), {'MWF_1200_1300'})

		#multiple overlap, long timeframe
		# self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'MWF_900_1300'), {'MWF_900_1000','MWF_1000_1100', 'MWF_1100_1200', 'MWF_1200_1300'})

		self.assertEqual(sp.get_overlapping_time_slots(['MWF_900_1300'], 'MWF_1000_1100'), {'MWF_900_1300'})

	def test_get_overlapping_time_slots_dow_overlapt(self):

		all_timeslot = ['MWF_800_900', 'M_800_900', 'W_800_900', 'F_800_900', 'T_800_900', 'R_800_900', 'TR_800_900']

		#if timeslot is includes multiple days, then timeslots including any of those days should be returned
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'MWF_800_900'), {'MWF_800_900', 'M_800_900','W_800_900', 'F_800_900'})
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'TR_800_900'), {'TR_800_900', 'T_800_900','R_800_900'})

		#if timeslot includes only one day, only the same day should be returned 
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'M_800_900'), {'M_800_900', 'MWF_800_900'})
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'W_800_900'), {'W_800_900', 'MWF_800_900'})
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'F_800_900'), {'F_800_900', 'MWF_800_900'})
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'T_800_900'), {'T_800_900', 'TR_800_900'})
		self.assertEqual(sp.get_overlapping_time_slots(all_timeslot, 'R_800_900'), {'R_800_900', 'TR_800_900'})


if __name__ == '__main__':
    unittest.main()