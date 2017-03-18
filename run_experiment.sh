#!/bin/bash
# Copyright (C) 2016 Huang MaChi at Chongqing University
# of Posts and Telecommunications, China.

k=$1
cpu=$2
duration=$3

# Exit on any failure.
set -e

# Check for uninitialized variables.
set -o nounset

ctrlc() {
	killall python
	killall -9 ryu-manager
	mn -c
	exit
}

trap ctrlc INT

# Output directory.
out_dir="./results"
rm -f -r ./results
mkdir -p $out_dir

flows_num_per_host="0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0"

# Run experiments.
for fnum in $flows_num_per_host
do
	./run_experiment2.sh $k $cpu $fnum $duration $out_dir

done
