## -------------------------------------------------------------------
##
## Copyright (c) 2015 Basho Technologies, Inc.
##
## This file is provided to you under the Apache License,
## Version 2.0 (the "License"); you may not use this file
## except in compliance with the License.  You may obtain
## a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
## -------------------------------------------------------------------

import collectd
import os
import sys
import subprocess
import traceback

config = {}

#
# Callbacks
#

def configure(cfg):
    global config
    config = config_to_dict(cfg)
    collectd.info("[collectd proc_stats plugin] config: %s" % str(config))
    
def init():
    global config
    collectd.info("[collectd proc_stats plugin] initialized: %s" % str(config))

def read(data=None):
    global config
    try :
        dispatch_stats(
            [
                {'name': "riak", 'proc': "beam.smp"},
                {'name': "solr", 'proc': "java"}
            ],
            lambda proc : get_stats(proc)
        )
        dispatch_stats(
            [
                {'name': "riak", 'proc': "beam.smp"},
                {'name': "solr", 'proc': "java"}
            ],
            lambda proc : get_io(proc)
            )
    except Exception as e:
        tb = traceback.format_exc()
        collectd.error("Error in read: %s %s" % (e, tb))


##
## Register callbacks
##

collectd.register_config(configure)
collectd.register_init(init)
collectd.register_read(read)


##
## internal operations
##

##
## @param specs     list of dict containing 'name' and 'proc' keys
## @param fun       function taking 'proc' field from a spec in each specs
##                  returning a stats dict
##
def dispatch_stats(specs, fun) :
    for spec in specs :
        stats = fun(spec['proc'])
        for name, value in stats.iteritems() :
            dispatch(spec['name'], name, value)



ticks_per_sec = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

def get_stats(proc) :
    pid = get_pid(proc)
    if (pid == "") :
        return {}
    else :
        file = open("/proc/%s/stat" % pid,  "r")
        lines = file.read().split("\n")
        stats = lines[0].split()
        return {
            'utime':        ('counter', int(stats[13])/float(ticks_per_sec)), 
            'stime':        ('counter', int(stats[14])/float(ticks_per_sec)),
            'num_threads':  ('gauge', int(stats[19])),
            'vsize':        ('gauge', int(stats[22])),
            'rss':          ('gauge', int(stats[23]))
        }


def get_io(proc) :
    pid = get_pid(proc)
    if (pid == "") :
        return {}
    else :
        file = open("/proc/%s/io" % pid,  "r")
        lines = file.read().split("\n")
        entries = {}
        for line in lines :
            fields = line.split(':')
            if len(fields) > 1 :
                entries[fields[0]] = fields[1].strip()
        ret = {}
        for i in ['write_bytes', 'read_bytes', 'wchar', 'rchar'] :
            if i in entries :
                ret[i] = ('counter', entries[i])
        return ret


def get_pid(proc) :
    try :
        return invoke("pgrep %s" % proc).split("\n")[0]
    except Exception as e :
        collectd.error("An error occurred getting pid for %s: %s" % (proc, e))
        return ""
    
def invoke(command) :
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    if proc.returncode != 0 :
        raise Exception(
            "An error occurred executing command '%s'.  Return code: %s.  stdout: '%s'.  stderr: '%s'" %
            (command, proc.returncode, stdout, stderr)
        )
    return stdout

def dispatch(name, type_, value) :
    t, v = value
    collectd.Values(
        plugin = "proc_" + type_,
        type = t,
        type_instance = name
    ).dispatch(values=[v])

def config_to_dict(config) :
    ret = {}
    for child in config.children :
        if len(child.children) > 0 :
            if not child.key in ret :
                ret[child.key] = []
            ret[child.key].append(config_to_dict(child))
        else :
            if len(child.values) == 1 :
                ret[child.key] = child.values[0]
            else : 
                ret[child.key] = child.values
    return ret

