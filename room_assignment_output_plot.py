import pandas as pd
import csv
import matplotlib.pyplot as plt
import data_process as dp
# import set_process as sp


def plot_delivery_mode_satisfied(output_filepath):
	"""
	Return a bar plot representing fraction of satisfied delievery modes.

	Parameters
	----------
	output_filepath : str
	Filepath to output file.

	Returns
	-------
	plt : matplotlib.pyplot module
	satisfied_count : dict(str, float)
	Maps raw preference to number of times it is satisfied.
	total_count : dict(str, float)
	Maps raw preference to total number of times it appears in the data.
	"""
	model_output_column = "delivery_mode"
	preference_column = "preference"
	plot_by_column = "raw_preference"

	satisfied_count = {}
	total_count = {}
	with open(output_filepath, "r") as file:
		reader = csv.DictReader(file)
		for row in reader:
			model_output = row[model_output_column]
			preference = row[preference_column]
			model_output_formatted, preference_formatted = format_delivery_mode(
			model_output, preference)

			bar_name = row[plot_by_column].strip()
			if bar_name not in satisfied_count.keys():
				satisfied_count[bar_name] = 0
				total_count[bar_name] = 0

			if model_output_formatted in preference_formatted:
				satisfied_count[bar_name] += 1
			total_count[bar_name] += 1

	percent_satisfied = {p: satisfied_count[p] / total_count[p]
	for p in satisfied_count.keys()}
	plt.bar(percent_satisfied.keys(), percent_satisfied.values())
	plt.title("Fraction of Satisfied Delivery Modes")
	return plt, satisfied_count, total_count


def format_delivery_mode(*args):
	"""Format string arguments.
	
	Lowercase all letters and remove leading/trailing whitespaces. If the 
	string is multiple comma-separated words, split the string into a list
	containing each individual word. 

	"Residential" and "Hybrid" are changed to "residential_spread" and
	"hybrid_split,hybrid_touchpoint,residential_spread", respectively,
	to maintain consistency across columns.
	"""
	formatted = []
	for a in args:
		a.lower().strip()
		if a == "residential":
			a += "_spread"
		if a == "hybrid":
			a = "hybrid_split,hybrid_touchpoint,residential_spread"
		f = [s.strip() for s in a.split(",")]
		formatted.append(f[0] if len(f) == 1 else f)
	return formatted


def room_assignment_output_plot(plot_type, directory, output_filename, title=None, room_use_filter=None, bins=10):

	if plot_type not in {"density", "delivery_mode"}:
		raise Exception("plot_type must be either 'density' or 'delivery mode'")

	if title is None:
		title = output_filename.split(".")[0]

	output_df = dp.read_data(directory + output_filename)

	if room_use_filter is not None:
		output_df = output_df[output_df['room_use'].isin(room_use_filter)]

	if plot_type == 'density':
		plot_density(output_df, title, bins=bins)
		image_filepath = directory + title + "_density_hist.png"
	elif plot_type == 'delivery_mode':
		plot_delivery_mode_count(output_df, title)
		image_filepath = directory + title + "_delivery_mode_count.png"

	plt.savefig(image_filepath, bbox_inches='tight')
	plt.clf()


def plot_delivery_mode_count(output_df, title):

	plt.title(title)
	plt.ylabel("number sections")
	plt.xlabel("delivery mode")
	delivery_mode_counts = output_df['delivery_mode'].value_counts()
	possible_delivery_modes = ['residential_spread','hybrid_split', 'hybrid_touchpoint', 'remote']
	delivery_mode_counts = delivery_mode_counts.to_dict()
	delivery_mode_counts = [delivery_mode_counts[delivery_mode] if delivery_mode in delivery_mode_counts else 0 for delivery_mode in possible_delivery_modes]
	delivery_mode_counts = pd.Series(delivery_mode_counts, index=possible_delivery_modes)
	print(delivery_mode_counts.index)
	print(delivery_mode_counts)
	plt.bar(delivery_mode_counts.index, delivery_mode_counts)
	return plt


def plot_density(output_df, title, bins=10):

	output_df['density'] = output_df['enrollment'] / output_df['capacity'] 
	mean_density = output_df['density'].mean()
	std_density = output_df['density'].std()
	plt.title(title)
	plt.ylabel("number sections")
	plt.xlabel("density")
	plt.hist(output_df['density'], bins=bins)
	return plt


def output_metrics(output_filepath_all, room_use_filter=None, capacity_scaling_factor= 1.0):

	metrics_list = list()
	for output_filepath in output_filepath_all:

		output_filename = output_filepath.split("/")[-1]
		output_df = dp.read_data(output_filepath)
		if room_use_filter is not None:
			output_df = output_df[output_df['room_use'].isin(room_use_filter)]
		output_df['density'] = output_df['enrollment'] / (output_df['capacity'] * capacity_scaling_factor)
		current_output_metrics = {
			"mean_density": output_df['density'].mean(),
			"std_density": output_df['density'].std(),
			"median_density": output_df['density'].quantile(0.5),
			"first_quantile_density": output_df['density'].quantile(0.25),
			"third_quantile_density:": output_df['density'].quantile(0.75)
		}
		metrics_list.append(current_output_metrics)
	return pd.DataFrame(metrics_list)


def count_consistent_assignments(output_filepath_a, output_filepath_b):

	output_df_a = dp.clean_room_assignment_output_data(output_filepath_a)
	output_df_b = dp.clean_room_assignment_output_data(output_filepath_b)
	room_section_dict_a = sp.get_section_room_assignment(output_df_a)
	room_section_dict_b = sp.get_section_room_assignment(output_df_b)

	num_consistent_assignments = sum([1 for section in room_section_dict_a if section in room_section_dict_b and room_section_dict_b[section]==room_section_dict_a[section]])

	return num_consistent_assignments


if __name__ == "__main__":
	output_filepath = ("/home/mtonbari/Projects/covid_recovery/Output/room_assignment_opt_output_full_enrollment_2020_Class_20_percent_social_distance_preferences_contact_max.csv")
	plt, satisfied, total = plot_delivery_mode_satisfied(output_filepath)
	for k in satisfied.keys():
	    print(k +":", satisfied[k] / total[k])
	plt.show()
	print(type(plt))
