Throughput Testing
------------------

Determines the time it takes to perform HTTP POSTs and GETs of various sizes
through SARA-R4/N4 modems.

`serverscript.py` should be run on a computer with a public IP address (or port
forwarding set up)

`serialscript.py` should be run on a computer with a USB connection to an LTE
modem. It was written for the SARA-R410M and SARA-N410. It should be run with
its output directed to a file, for example:
`python3 -u serialscript.py | tee saraR4_serialscript10_results.txt`

`parse-results.py` is run on that text output and prints statistical properties
of the results (mean, median, confidence interval, etc.).

`wake-and-post.py` is an alternative to `serialscript.py` meant to be used with
a modem in PSM deep sleep. Once the `PWR_ON` button is manually pressed, the
script detects the wakeup of the radio and performs an HTTP POST as soon as the
network has re-attached.

