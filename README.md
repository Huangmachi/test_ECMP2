## test_ECMP

test_ECMP is a test experiment to compare the transmitting performance of ECMP and PureSDN.


### Prerequisites

The following softwares should have been installed in your machine.
* Mininet: git clone git://github.com/mininet/mininet; mininet/util/install.sh -a
* Ryu: git clone git://github.com/osrg/ryu.git; cd ryu; pip install .
* Networkx: pip install networkx
* Numpy: pip install numpy
* Matplotlib: apt-get install python-matplotlib


### Start

Just start it as follows, you will find the results in the 'results' directory. It will takes you about 4 hours.

    $ ./run_experiment.sh 4 2.0 60


### Author

Brought to you by Huang MaChi (Chongqing University of Posts and Telecommunications, Chongqing, China.).

If you have any question, you can email me at huangmachi@foxmail.com.

Enjoy it!
