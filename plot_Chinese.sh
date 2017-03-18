#!/bin/bash
# Copyright (C) 2016 Huang MaChi at Chongqing University
# of Posts and Telecommunications, China.

k=$1
duration=60
out_dir='./results'

flows_num_per_host="0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0"

for fnum in $flows_num_per_host
do
	sudo python ./plot_results_Chinese.py --k $k --duration $duration --dir $out_dir --fnum $fnum
done
