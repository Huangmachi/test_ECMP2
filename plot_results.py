# Copyright (C) 2016 Huang MaChi at Chongqing University
# of Posts and Telecommunications, Chongqing, China.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import re
import matplotlib.pyplot as plt
import numpy as np


parser = argparse.ArgumentParser(description="Plot BFlows experiments' results")
parser.add_argument('--k', dest='k', type=int, default=4, choices=[4, 8], help="Switch fanout number")
parser.add_argument('--duration', dest='duration', type=int, default=60, help="Duration (sec) for each iperf traffic generation")
parser.add_argument('--dir', dest='out_dir', help="Directory to store outputs")
parser.add_argument('--fnum', dest='flows_num_per_host', type=float, default=1.0, help="Number of iperf flows per host")
args = parser.parse_args()


def read_file_1(file_name, delim=','):
	"""
		Read the bwmng.txt file.
	"""
	read_file = open(file_name, 'r')
	lines = read_file.xreadlines()
	lines_list = []
	for line in lines:
		line_list = line.strip().split(delim)
		lines_list.append(line_list)
	read_file.close()

	# Remove the last second's statistics, because they are mostly not intact.
	last_second = lines_list[-1][0]
	_lines_list = lines_list[:]
	for line in _lines_list:
		if line[0] == last_second:
			lines_list.remove(line)

	return lines_list

def read_file_2(file_name):
	"""
		Read the first_packets.txt and successive_packets.txt file.
	"""
	read_file = open(file_name, 'r')
	lines = read_file.xreadlines()
	lines_list = []
	for line in lines:
		if line.startswith('rtt') or line.endswith('ms\n'):
			lines_list.append(line)
	read_file.close()
	return lines_list

def calculate_average(value_list):
	average_value = sum(map(float, value_list)) / len(value_list)
	return average_value

def get_throughput(throughput, traffic, app, input_file):
	"""
		csv output format:
		(Type rate)
		unix_timestamp;iface_name;bytes_out/s;bytes_in/s;bytes_total/s;bytes_in;bytes_out;packets_out/s;packets_in/s;packets_total/s;packets_in;packets_out;errors_out/s;errors_in/s;errors_in;errors_out\n
		(Type svg, sum, max)
		unix timestamp;iface_name;bytes_out;bytes_in;bytes_total;packets_out;packets_in;packets_total;errors_out;errors_in\n
		The bwm-ng mode used is 'rate'.

		throughput = {
						'stag_0.5_0.3':
						{
							'realtime_bisection_bw': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'BFlows':x%, 'ECMP':x%, ...}
						},
						'stag_0.6_0.2':
						{
							'realtime_bisection_bw': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'BFlows':x%, 'ECMP':x%, ...}
						},
						...
					}
	"""
	full_bisection_bw = 10.0 * (args.k ** 3 / 4)   # (unit: Mbit/s)
	lines_list = read_file_1(input_file)
	first_second = int(lines_list[0][0])
	column_bytes_out_rate = 2   # bytes_out/s
	column_bytes_out = 6   # bytes_out

	if app == 'NonBlocking':
		switch = '1001'
	elif app in ['BFlows', 'BFlows-A', 'ECMP', 'PureSDN', 'Hedera']:
		switch = '3[0-9][0-9][0-9]'
	else:
		pass
	sw = re.compile(switch)

	if not throughput.has_key(traffic):
		throughput[traffic] = {}

	if not throughput[traffic].has_key('realtime_bisection_bw'):
		throughput[traffic]['realtime_bisection_bw'] = {}
	if not throughput[traffic].has_key('realtime_throughput'):
		throughput[traffic]['realtime_throughput'] = {}
	if not throughput[traffic].has_key('accumulated_throughput'):
		throughput[traffic]['accumulated_throughput'] = {}
	if not throughput[traffic].has_key('normalized_total_throughput'):
		throughput[traffic]['normalized_total_throughput'] = {}

	if not throughput[traffic]['realtime_bisection_bw'].has_key(app):
		throughput[traffic]['realtime_bisection_bw'][app] = {}
	if not throughput[traffic]['realtime_throughput'].has_key(app):
		throughput[traffic]['realtime_throughput'][app] = {}
	if not throughput[traffic]['accumulated_throughput'].has_key(app):
		throughput[traffic]['accumulated_throughput'][app] = {}
	if not throughput[traffic]['normalized_total_throughput'].has_key(app):
		throughput[traffic]['normalized_total_throughput'][app] = 0

	for i in xrange(args.duration + 1):
		if not throughput[traffic]['realtime_bisection_bw'][app].has_key(i):
			throughput[traffic]['realtime_bisection_bw'][app][i] = 0
		if not throughput[traffic]['realtime_throughput'][app].has_key(i):
			throughput[traffic]['realtime_throughput'][app][i] = 0
		if not throughput[traffic]['accumulated_throughput'][app].has_key(i):
			throughput[traffic]['accumulated_throughput'][app][i] = 0

	for row in lines_list:
		iface_name = row[1]
		if iface_name not in ['total', 'lo', 'eth0', 'enp0s3', 'enp0s8', 'docker0']:
			if switch == '3[0-9][0-9][0-9]':
				if sw.match(iface_name):
					if int(iface_name[-1]) > args.k / 2:   # Choose down-going interfaces only.
						if (int(row[0]) - first_second) <= args.duration:   # Take the good values only.
							throughput[traffic]['realtime_bisection_bw'][app][int(row[0]) - first_second] += float(row[column_bytes_out_rate]) * 8.0 / (10 ** 6)   # Mbit/s
							throughput[traffic]['realtime_throughput'][app][int(row[0]) - first_second] += float(row[column_bytes_out]) * 8.0 / (10 ** 6)   # Mbit
			elif switch == '1001':   # Choose all the interfaces. (For NonBlocking Topo only)
				if sw.match(iface_name):
					if (int(row[0]) - first_second) <= args.duration:
						throughput[traffic]['realtime_bisection_bw'][app][int(row[0]) - first_second] += float(row[column_bytes_out_rate]) * 8.0 / (10 ** 6)   # Mbit/s
						throughput[traffic]['realtime_throughput'][app][int(row[0]) - first_second] += float(row[column_bytes_out]) * 8.0 / (10 ** 6)   # Mbit
			else:
				pass

	for i in xrange(args.duration + 1):
		for j in xrange(i+1):
			throughput[traffic]['accumulated_throughput'][app][i] += throughput[traffic]['realtime_throughput'][app][j]   # Mbit

	throughput[traffic]['normalized_total_throughput'][app] = throughput[traffic]['accumulated_throughput'][app][args.duration] / (full_bisection_bw * args.duration)   # percentage

	return throughput

def get_value_list_1(throughput, traffic, item, app):
	"""
		Get the values from the "throughput" data structure.
	"""
	value_list = []
	for i in xrange(args.duration + 1):
		value_list.append(throughput[traffic][item][app][i])
	return value_list

def get_average_bisection_bw(throughput, traffics, app):
	value_list = []
	for traffic in traffics:
		value_list.append(throughput[traffic]['accumulated_throughput'][app][args.duration] / float(args.duration))
	return value_list

def get_value_list_2(value_dict, traffics, item, app):
	"""
		Get the values from the  data structure.
	"""
	value_list = []
	for traffic in traffics:
		value_list.append(value_dict[traffic][item][app])
	return value_list

def plot_results():
	"""
		Plot the results:
		1. Plot realtime bisection bandwidth
		2. Plot average bisection bandwidth
		3. Plot accumulated throughput
		4. Plot normalized total throughput

		throughput = {
						'stag_0.5_0.3':
						{
							'realtime_bisection_bw': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'BFlows':x%, 'ECMP':x%, ...}
						},
						'stag_0.6_0.2':
						{
							'realtime_bisection_bw': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'realtime_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'accumulated_throughput': {'BFlows':{0:x, 1:x, ..}, 'ECMP':{0:x, 1:x, ..}, ...},
							'normalized_total_throughput': {'BFlows':x%, 'ECMP':x%, ...}
						},
						...
					}
	"""
	full_bisection_bw = 10.0 * (args.k ** 3 / 4)   # (unit: Mbit/s)
	utmost_throughput = full_bisection_bw * args.duration
	# _traffics = "stag1_0.5_0.3 stag2_0.5_0.3 stag1_0.6_0.2 stag2_0.6_0.2 stag1_0.7_0.2 stag2_0.7_0.2 stag1_0.8_0.1 stag2_0.8_0.1"
	_traffics = "random stag_0.2_0.3 stag_0.3_0.3 stag_0.4_0.3 stag_0.5_0.3 stag_0.6_0.2 stag_0.7_0.2 stag_0.8_0.1"
	traffics = _traffics.split(' ')
	# apps = ['BFlows', 'BFlows-A', 'ECMP', 'PureSDN', 'Hedera']
	apps = ['ECMP', 'PureSDN']
	throughput = {}

	for traffic in traffics:
		for app in apps:
			bwmng_file = args.out_dir + '/%s/%s/%s/bwmng.txt' % (args.flows_num_per_host, traffic, app)
			throughput = get_throughput(throughput, traffic, app, bwmng_file)

	# 1. Plot realtime bisection bandwidth.
	item = 'realtime_bisection_bw'
	fig = plt.figure()
	fig.set_size_inches(16, 20)
	num_subplot = len(traffics)
	num_raw = 4
	num_column = num_subplot / num_raw
	NO_subplot = 1
	x = np.arange(0, args.duration + 1)
	for traffic in traffics:
		plt.subplot(num_raw, num_column, NO_subplot)
		y1 = get_value_list_1(throughput, traffic, item, 'ECMP')
		y2 = get_value_list_1(throughput, traffic, item, 'PureSDN')
		plt.plot(x, y1, 'b-', linewidth=2, label="ECMP")
		plt.plot(x, y2, 'g-', linewidth=2, label="PureSDN")
		plt.title('%s' % traffic, fontsize='x-large')
		plt.xlabel('Time (s)', fontsize='x-large')
		plt.xlim(0, args.duration)
		plt.xticks(np.arange(0, args.duration + 1, 10))
		plt.ylabel('Realtime Bisection Bandwidth\n(Mbps)', fontsize='x-large')
		# plt.ylim(0, full_bisection_bw)
		# plt.yticks(np.linspace(0, full_bisection_bw, 11))
		plt.legend(loc='lower right', ncol=len(apps), fontsize='small')
		plt.grid(True)
		NO_subplot += 1
	plt.subplots_adjust(top=0.95, bottom=0.05, left=0.1, right=0.95, hspace=0.25, wspace=0.35)
	plt.savefig(args.out_dir + '/%s-1.realtime_bisection_bw.png' % args.flows_num_per_host)

	# 2. Plot average bisection bandwidth.
	fig = plt.figure()
	fig.set_size_inches(12, 6)
	num_groups = len(traffics)
	num_bar = len(apps)
	ECMP_value_list = get_average_bisection_bw(throughput, traffics, 'ECMP')
	PureSDN_value_list = get_average_bisection_bw(throughput, traffics, 'PureSDN')
	index = np.arange(num_groups) + 0.15
	bar_width = 0.15
	plt.bar(index, PureSDN_value_list, bar_width, color='g', label='PureSDN')
	plt.bar(index + 1 * bar_width, ECMP_value_list, bar_width, color='b', label='ECMP')
	plt.xticks(index + num_bar / 2.0 * bar_width, traffics, fontsize='small')
	plt.ylabel('Average Bisection Bandwidth\n(Mbps)', fontsize='x-large')
	# plt.ylim(0, full_bisection_bw)
	# plt.yticks(np.linspace(0, full_bisection_bw, 11))
	plt.legend(loc='lower right', ncol=len(apps), fontsize='small')
	plt.grid(axis='y')
	plt.savefig(args.out_dir + '/%s-2.average_bisection_bw.png' % args.flows_num_per_host)

	# 3. Plot accumulated throughput.
	item = 'accumulated_throughput'
	fig = plt.figure()
	fig.set_size_inches(16, 20)
	num_subplot = len(traffics)
	num_raw = 4
	num_column = num_subplot / num_raw
	NO_subplot = 1
	x = np.arange(0, args.duration + 1)
	for traffic in traffics:
		plt.subplot(num_raw, num_column, NO_subplot)
		y1 = get_value_list_1(throughput, traffic, item, 'ECMP')
		y2 = get_value_list_1(throughput, traffic, item, 'PureSDN')
		plt.plot(x, y1, 'b-', linewidth=2, label="ECMP")
		plt.plot(x, y2, 'g-', linewidth=2, label="PureSDN")
		plt.title('%s' % traffic, fontsize='x-large')
		plt.xlabel('Time (s)', fontsize='x-large')
		plt.xlim(0, args.duration)
		plt.xticks(np.arange(0, args.duration + 1, 10))
		plt.ylabel('Accumulated Throughput\n(Mbit)', fontsize='x-large')
		# plt.ylim(0, utmost_throughput)
		# plt.yticks(np.linspace(0, utmost_throughput, 11))
		plt.legend(loc='upper left', fontsize='x-large')
		plt.grid(True)
		NO_subplot += 1
	plt.subplots_adjust(top=0.95, bottom=0.05, left=0.1, right=0.95, hspace=0.25, wspace=0.35)
	plt.savefig(args.out_dir + '/%s-3.accumulated_throughput.png' % args.flows_num_per_host)

	# 4. Plot normalized total throughput.
	item = 'normalized_total_throughput'
	fig = plt.figure()
	fig.set_size_inches(12, 6)
	num_groups = len(traffics)
	num_bar = len(apps)
	ECMP_value_list = get_value_list_2(throughput, traffics, item, 'ECMP')
	PureSDN_value_list = get_value_list_2(throughput, traffics, item, 'PureSDN')
	index = np.arange(num_groups) + 0.15
	bar_width = 0.15
	plt.bar(index, PureSDN_value_list, bar_width, color='g', label='PureSDN')
	plt.bar(index + 1 * bar_width, ECMP_value_list, bar_width, color='b', label='ECMP')
	plt.xticks(index + num_bar / 2.0 * bar_width, traffics, fontsize='small')
	plt.ylabel('Normalized Total Throughput\n', fontsize='x-large')
	plt.ylim(0, 1)
	plt.yticks(np.linspace(0, 1, 11))
	plt.legend(loc='upper right', ncol=len(apps), fontsize='small')
	plt.grid(axis='y')
	plt.savefig(args.out_dir + '/%s-4.normalized_total_throughput.png' % args.flows_num_per_host)


if __name__ == '__main__':
	plot_results()
