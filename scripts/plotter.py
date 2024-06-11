# Script that plots the data from the csv files and saves them as png files
import random
import re
import sys
import os
from os import path
from glob import glob

import matplotlib
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to extract the number of processes from the filename
def extract_proc(filepath):
	match = re.search(r'_([^_]*)\.csv', filepath)
	if match:
		return int(match.group(1))
	else:
		return None

# If no filename passed, exit
if len(sys.argv) < 2:
	print("Usage: python plotter.py <plot_type> [basepath]")
	print("<plot_type>\tstrongcomp, strongsingle, polynomial, speedup, time")
	print("[basepath]\toptional path to the directory containing the output files (default: current directory)")
	print("\t\tbasepath must have: output_mf, output_mb, output_mg directories containing the .csv files")
	exit()

if len(sys.argv) > 2:
	basepath = path.abspath(sys.argv[2])
else:
	basepath = path.abspath(".")

print("Base directory: ", basepath)

# Make directory for the plots if it doesn't exist
if not os.path.exists(os.path.join(".", "plots")):
	os.makedirs(os.path.join(".", "plots"))

# Name of the output directories as out + put for put in put_types
out = "output_"
put_types = ("mf", "mb", "mg")
load_put_types = put_types + ("mf_threads", "mf_double")
marks = {"mf": 'o', "mb": '^', "mg": 'x', "mf_threads": '^', "mf_double": '^'}

# Set the style of the plots
plt.rcParams.update({'font.size': 12})

# Collection of dfs
df_dim = {}
df_poly = {}

# Load the data from the csv files
for put in load_put_types:
	## Dimension time data
	file_list = glob(path.join(basepath, out + put, "dimension_time_*.csv"))
	print("Analyzing", put, "files for dimension:")
	for file in file_list: print("\t", file)
	data = []

	# For each dimension time file, read the data and append it to the list
	for file in file_list:
		df_temp = pd.read_csv(file, comment='#')
		df_temp['proc'] = extract_proc(file)
		data.append(df_temp)

	# Concatenate the dataframes
	df_dim[put] = pd.concat(data, ignore_index=True)
	# Correct eventual errors in the column number of setup+assemble time
	if 'steup+assemble' in df_dim[put].columns:
		df_dim[put].rename(columns={'steup+assemble': 'setup+assemble'}, inplace=True)
	# Add a column for total time
	df_dim[put]['total'] = df_dim[put]['setup+assemble'] + df_dim[put]['solve']

	print(df_dim[put].info())

for put in put_types:
	## Polynomial degree data
	file = glob(path.join(basepath, out + put, "polynomial_degree_*.csv"))[0]
	print("Analyzing", put, "file for polynomial:")
	print("\t", file)
	df_poly[put] = pd.read_csv(file, comment='#')
	# Add a column for total time
	df_poly[put]['total'] = df_poly[put]['setup+assemble'] + df_poly[put]['solve']
	print(df_poly[put].info())




# ====== Plot for strong scaling for all the solvers ======
#	Plot the solve time as a function of the number of processes for the largest two values of n_dofs
#	for each of the solvers, with the ideal scaling reference.
#	Then do the same for the setup+assemble time.
if "strongcomp" in sys.argv[1]:
	print("Plotting strong scaling for all solvers")
	# Solve time as a function of the number of processes all in one plot for a single n_dof
	for time_type in ("solve", "setup+assemble", "total"):
		fig, ax = plt.subplots()
		for put in put_types:
			df = df_dim[put]
			# Sort the data by the number of processes
			df = df.sort_values(by='proc')
			# Get the largest two values of n_dofs and plot them
			for dof_value in df['n_dofs'].drop_duplicates().nlargest(2).tolist():
				df1 = df[df['n_dofs'] == dof_value]
				# Compose the label
				lab = put + " (" + str(round(dof_value/1e6, 1)) + "M DoFs)"
				ax.plot(df1['proc'], df1[time_type], label=lab, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)

		#Plot ideal scaling
		proc = df['proc']
		solve = df[time_type]
		ax.plot(proc, 1e2 / proc, label="Ideal scaling", linestyle='--', color='black')

		ax.set_xlabel("Number of processors")
		ax.set_ylabel(time_type + " time (s)")
		ax.set_yscale('log')
		ax.set_xscale('log')
		ax.grid(True, which="both", ls="--")
		ax.set_xticks(df['proc'].unique())
		ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
		ax.set_title("Strong scaling for " + time_type + " time for all the solvers")
		ax.legend(loc="upper right", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "strongcomp_" + time_type + ".png"))
		print("Strong scaling plot saved in", os.path.join(".", "plots", "strongcomp_" + time_type + ".png"))


# ====== Plot for strong scaling for each solver ======
#	Plot the previous quantities but for all the problem sizes and separately for each
# 	of the solvers.
if "strongsingle" in sys.argv[1]:
	print("Plotting strong scaling for each solver")
	# Solve time as a function of the number of processes all in one plot for a single n_dof
	for time_type in ("solve", "setup+assemble", "total"):
		for put in put_types:
			fig, ax = plt.subplots()
			df = df_dim[put]
			# Sort the data by the number of processes
			df = df.sort_values(by='proc')
			# Get the largest two values of n_dofs and plot them
			for dof_value in df['n_dofs'].drop_duplicates().tolist():
				df1 = df[df['n_dofs'] == dof_value]
				# Compose the label
				lab = put + " (" + str(round(dof_value/1e6, 2)) + "M DoFs)"
				ax.plot(df1['proc'], df1[time_type], label=lab, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)

			#Plot ideal scaling
			proc = df['proc']
			solve = df[time_type]
			ax.plot(proc, 1e3 / proc, label="Ideal scaling", linestyle='--', color='black')
			ax.plot(proc, 1e2 / proc, linestyle='--', color='black')
			ax.plot(proc, 1 / proc, linestyle='--', color='black')
			ax.set_xlabel("Number of processors")
			ax.set_ylabel(time_type + " time (s)")
			ax.set_yscale('log')
			ax.set_xscale('log')
			ax.grid(True, which="both", ls="--")
			ax.set_xticks(df['proc'].unique())
			ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
			ax.set_title("Strong scaling of " + time_type + " time for " + put)
			ax.legend(loc="upper right", fontsize='small', fancybox=True, framealpha=0.5)
			plt.savefig(os.path.join(".", "plots", "strong_" + put + "_" + time_type + ".png"))
			print("Strong scaling plot saved in", os.path.join(".", "plots", "strong_" + put + "_" + time_type + ".png"))


# ====== Plot for polynomial ======
#	Plot the MDofs/s metric as a function of the polynomial degree for all the solvers
if "polynomial" in sys.argv[1]:
	print("Plotting polynomial study for all solvers")
	for time_type in ("solve", "setup+assemble", "total"):
		fig, ax = plt.subplots()
		for put in put_types:
			df = df_poly[put]
			ax.plot(df['degree'], 1e-6 * df['dofs'] / df[time_type], label=put, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)
		ax.set_ylabel(time_type + " MDofs/s")
		ax.set_xlabel("Polynomial degree")
		ax.set_xticks(df['degree'].unique())
		ax.grid(True, which="both", ls="--")
		ax.set_title("Polynomial degree performance for " + time_type)
		ax.legend(loc="upper right", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "polynomial_" + time_type + ".png"))
		print("Polynomial plot saved in", os.path.join(".", "plots", "polynomial_" + time_type + ".png"))


# ====== Plot for solve time ======
#	Plot the solve time and setup time as a function of the number of the dofs number for all the solvers
if "time" in sys.argv[1]:
	print("Plotting time study for all solvers")
	for time_type in ("solve", "setup+assemble", "total"):
		fig, ax = plt.subplots()
		for put in put_types:
			df = df_dim[put]
			# Sort the data by the number of processes
			df = df.sort_values(by='n_dofs')
			# Get the largest two values of n_dofs and plot them
			for proc_value in (8, 16, 32):
				df1 = df[df['proc'] == proc_value]
				# Compose the label
				lab = put + " (" + str(proc_value) + " procs)"
				ax.plot(df1['n_dofs'], df1[time_type], label=lab, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)

		# Add reference
		dofs = df_dim['mf']['n_dofs']
		ax.plot(dofs, 1e-7*dofs, label="Linear", linestyle='--', linewidth=0.8, color='black')
		dofs = df_dim['mb']['n_dofs']
		dofs = dofs.loc[dofs > 1e3]
		ax.plot(dofs, 1e-9*dofs**2, label="Quadratic", linestyle='--', linewidth=0.8, color='blue')
		ax.set_xlabel("Number of DoFs")
		ax.set_ylabel(time_type + " time (s)")
		ax.set_yscale('log')
		ax.set_xscale('log')
		ax.grid(True, which="both", ls="--")
		ax.set_title(time_type + " time for all solvers")
		ax.legend(loc="upper left", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "time_" + time_type + ".png"))
		print("Time plot saved in", os.path.join(".", "plots", "time_" + time_type + ".png"))

# ====== Plot for thread mf comparison ======
#	!!! must load in the output the correct mf data with threading
if "threads" in sys.argv[1]:
	print("Plotting time study for threads in mf")
	for time_type in ("solve", "setup+assemble", "total"):
		fig, ax = plt.subplots()
		put = "mf_threads"
		df = df_dim[put]
		# Sort the data by the number of processes
		df = df.sort_values(by=['n_dofs', 'proc'])
		# Get the largest two values of n_dofs and plot them
		for proc_value in df['proc'].drop_duplicates().tolist():
			df1 = df[df['proc'] == proc_value]
			# Compose the label
			lab = put + " (" + str(proc_value) + " procs)"
			ax.plot(df1['n_dofs'], df1[time_type], label=lab, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)

		# Add reference
		ax.plot(df1['n_dofs'], 1e-6*df1['n_dofs'], label="Linear", linestyle='--', color='black')
		ax.plot(df1['n_dofs'], 1e-7*df1['n_dofs'], linestyle='--', color='black')
		ax.set_xlabel("Number of DoFs")
		ax.set_ylabel(time_type + " time (s)")
		ax.set_yscale('log')
		ax.set_xscale('log')
		ax.grid(True, which="both", ls="--")
		ax.set_title(time_type + " time for mf redistributing threads and processes")
		ax.legend(loc="upper left", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "threads_" + time_type + ".png"))
		print("Time plot saved in", os.path.join(".", "plots", "threads_" + time_type + ".png"))


# ====== Plot for speedup ======
#	Plot the solve speedup for mf with respect to mg in function of dofs number
if "speedup" in sys.argv[1]:
	print("Plotting time speedup for mf with respect to mg in function of dofs")
	fig, ax = plt.subplots()
	df_mf = df_dim["mf"]
	df_mg = df_dim["mg"]
	df_mf = df_mf.sort_values(by='n_dofs')
	df_mg = df_mg.sort_values(by='n_dofs')
	for proc_value in (8, 16, 32):
		df1_mf = df_mf[df_mf['proc'] == proc_value]
		df1_mg = df_mg[df_mg['proc'] == proc_value]
		speedup = df1_mg['total'] / df1_mf['total']
		ax.plot(df1_mf['n_dofs'], speedup, label=str(proc_value) + " procs", marker='o', linestyle='-.', linewidth=2.5, markersize=8)

	ax.plot(df1_mf['n_dofs'], np.log(df1_mf['n_dofs']) - 8, label="Log speedup", linestyle='--', color='black')
	ax.set_xlabel("Number of DoFs")
	ax.set_ylabel("Speedup")
	ax.set_xscale('log')
	ax.grid(True, which="both", ls="--")
	ax.set_title("Total time speedup for mf with respect to mg")
	ax.legend(loc="upper right", fontsize='small', fancybox=True, framealpha=0.5)
	plt.savefig(os.path.join(".", "plots", "speedup_mf_mg.png"))
	print("Speedup plot saved in", os.path.join(".", "plots", "speedup_mf_mg.png"))

# ====== Plot for parallel speedup ======
if "parallel" in sys.argv[1]:
	print("Plotting parallel speedup for all solvers")
	for time_type in ("solve", "setup+assemble", "total"):
		fig, ax = plt.subplots()
		for put in ('mf','mg'):
			df = df_dim[put]
			# Sort the data by the number of processes
			df = df.sort_values(by='proc')
			# Get the largest two values of n_dofs and plot them
			for dof_value in df['n_dofs'].drop_duplicates().nlargest(2).tolist():
				df1 = df[df['n_dofs'] == dof_value]
				# Compose the label
				lab = put + " (" + str(round(dof_value/1e6, 1)) + "M DoFs)"
				speedup = df['proc'].min() * df1[time_type].max() / df1[time_type]
				ax.plot(df1['proc'], speedup, label=lab, marker=marks[put], linestyle='-.', linewidth=2.5, markersize=8)

		# Plot the ideal speedup
		proc = df['proc']
		ax.plot(proc, proc, label="Ideal speedup", linestyle='--', color='black')
		ax.set_xlabel("Number of processors")
		ax.set_ylabel("Speedup")
		ax.set_xscale('log')
		ax.set_yscale('log')
		ax.grid(True, which="both", ls="--")
		ax.set_xticks(df['proc'].unique())
		ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
		ax.set_title("Parallel speedup for " + time_type + " time for all the solvers")
		ax.legend(loc="upper left", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "parallelspeedup_" + time_type + ".png"))
		print("Parallel speedup plot saved in", os.path.join(".", "plots", "parallelspeedup_" + time_type + ".png"))

# ====== Plot for double ======
#	Plot the total speedup for mf with double and with double precision
if "double" in sys.argv[1]:
	print("Plotting time speedup for mf with double and mixed precision in function of dofs")
	for time_type in ("solve", "total"):
		fig, ax = plt.subplots()
		df_mf = df_dim["mf"].sort_values(by='n_dofs')
		df_mf_double = df_dim["mf_double"].sort_values(by='n_dofs')
		for proc_value in (2, 4, 8, 12, 16, 32):
			df1_mf = df_mf[df_mf['proc'] == proc_value]
			df1_mf_double = df_mf_double[df_mf_double['proc'] == proc_value]
			speedup = df1_mf_double[time_type] / df1_mf[time_type]
			ax.plot(df1_mf['n_dofs'], speedup, label=str(proc_value) + " procs", marker='o', linestyle='-.', linewidth=2.5, markersize=8)

		ax.set_xlabel("Number of DoFs")
		ax.set_ylabel("Speedup")
		ax.set_xscale('log')
		ax.grid(True, which="both", ls="--")
		ax.set_title(time_type + " time speedup for mixed over double-only precision mf")
		ax.legend(loc="upper right", fontsize='small', fancybox=True, framealpha=0.5)
		plt.savefig(os.path.join(".", "plots", "speedup_double_" + time_type + ".png"))
		print("Speedup plot saved in", os.path.join(".", "plots", "speedup_double_" + time_type + ".png"))

# ====== If the plot type is not recognized ======
if all(s not in sys.argv[1] for s in ("strongcomp", "strongsingle", "polynomial", "speedup", "time", "threads" ,"parallel", "double")):
	print("Plot type not supported!!!!!")
	print("Run without arguments to see the usage")
	exit()