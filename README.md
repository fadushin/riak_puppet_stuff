# riak_puppet_stuff


This repository contains puppet recipes for managing my local riak cluster.  It is not really intended for general consumption, though there are parts of this repository that may be of general interest, particularly the collectd plugin for generating stats from Riak and dispatching into collectd, described below.



## Collectd Plugin

This repository contains a simple Python plugin for the collectd service, a UNIX daemon that is used to collect and aggregate statistics from runtime services.  This plugin is designed to connect to a Riak endpoint over the HTTP interface, GET the JSON object returned from a REST-ful stats call, and dispatch collectd stats 


### How to use this Plugin




### Supported Features:

* Ability to connect to Riak over HTTP interface
* Generates statistics for defined Riak statistics
* Aggregates Exometer histograms into histogram stats, which contain median, mean, 95th, 99th, and 99.9th percentiles.
* Aggregates OTP memory statistics into a single collectd multi-valued stat
* Treats stats that end in _total as collected counter types
* All other stats are treated as gauges


### To Do:

* Support connections to multiple Riak nodes (e.g., devrels)
* Filtering (includes/excludes, though you can also use the filtering capabilities already built into collectd
