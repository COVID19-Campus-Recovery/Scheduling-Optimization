import pandas as pd
import matplotlib.pyplot as plt
import data_process as dp
import set_process as sp


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

