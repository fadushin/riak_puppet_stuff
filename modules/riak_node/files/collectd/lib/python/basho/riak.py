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
import httplib
import json

class Connection :

    def __init__(self, host, port, context) :
        self.connection = None
        self.host = host
        self.port = int(port)
        self.context = context

    def get(self) :
        try :
            if self.connection == None :
                self.connection = httplib.HTTPConnection(self.host, self.port)
                collectd.info("[collectd riak plugin] connection initialized to %s" % connection.str())
            self.connection.request("GET", self.context)
            response = self.connection.getresponse()
            body = response.read()
            return body
        except Exception as e :
            self.connection = None
            raise Exception("Connection error: %s to %s:%s" % (e, self.host, self.port))
    
    def str(self) :
        return "http://" + self.host + ":" + str(self.port) + self.context

connection = None
config = {}

#
# Callbacks
#

def configure(cfg):
    global config
    config = config_to_dict(cfg)
    collectd.info("[collectd riak plugin] config: %s" % str(config))
    
def init():
    global config
    global connection
    connection = Connection(
        config['connection'][0]['host'],
        int(config['connection'][0]['port']),
        config['connection'][0]['context']
    )

def read(data=None):
    global config
    global connection
    #
    # Get the stats JSON from riak
    # If there is a stat defined in config for it,
    # dispatch the stat into collectd
    #
    try :
        doc = json.loads(connection.get())
        grouped = group_by_type(doc)
        #print("%s" % grouped)
        dispatch_memory(grouped['otp_memory'])
        dispatch_counters(grouped['counter'])
        dispatch_gauges(grouped['gauge'])
        dispatch_histograms(grouped['histogram'])        
    except Exception as e:
        collectd.error("Error in read: %s" % e)


#
# Register callbacks
#

collectd.register_config(configure)
collectd.register_init(init)
collectd.register_read(read)


##
## internal operations
##

def group_by_type(doc) :
    ret = {'histogram': {}, 'gauge': {}, 'counter': {}, 'otp_memory': {}}
    for key in doc :
        nkey = key.encode('utf8')
        value = doc[key]
        if not is_number(value) :
            pass
        elif nkey.startswith("memory_") :
            suffix = nkey[7:]
            ret['otp_memory'][suffix] = value
        elif nkey.startswith("mem_") :
            suffix = nkey[4:]
            ret['otp_memory'][suffix] = value
        elif nkey.endswith("_100") :
            prefix = nkey[:nkey.index("_100")]
            if not prefix in ret['histogram'] :
                ret['histogram'][prefix] = {}
            ret['histogram'][prefix]["100"] = value
        elif nkey.endswith("_999") :
            prefix = nkey[:nkey.index("_999")]
            if not prefix in ret['histogram'] :
                ret['histogram'][prefix] = {}
            ret['histogram'][prefix]["100"] = value
        elif nkey.endswith("_99") :
            prefix = nkey[:nkey.index("_99")]
            if not prefix in ret['histogram'] :
                ret['histogram'][prefix] = {}
            ret['histogram'][prefix]["99"] = value
        elif nkey.endswith("_95") :
            prefix = nkey[:nkey.index("_95")]
            if not prefix in ret['histogram'] :
                ret['histogram'][prefix] = {}
            ret['histogram'][prefix]["95"] = value
        elif nkey.endswith("_mean") :
            prefix = nkey[:nkey.index("_mean")]
            if not prefix + "_99" in doc :
                ret['gauge'][nkey] = value
            else :
                if not prefix in ret['histogram'] :
                    ret['histogram'][prefix] = {}
                ret['histogram'][prefix]["mean"] = value
        elif nkey.endswith("_median") :
            prefix = nkey[:nkey.index("_median")]
            if not prefix + "_99" in doc :
                ret['gauge'][nkey] = value
            else :
                if not prefix in ret['histogram'] :
                    ret['histogram'][prefix] = {}
                ret['histogram'][prefix]["median"] = value
        elif nkey.endswith("_total") :
            ret['counter'][nkey] = value
        else :
            ret['gauge'][nkey] = value
    return ret

def is_number(o) :
    try :
        float(o)
        return True
    except Exception :
        return False

def dispatch_counters(counters) :
    for name, value in counters.iteritems() :
        dispatch("counter", name, value)
    
def dispatch_gauges(counters) :
    for name, value in counters.iteritems() :
        dispatch("gauge", name, value)

def dispatch(type_, name, value) :
    collectd.Values(
        plugin = 'riak',
        type = type_,
        type_instance = name
    ).dispatch(values=[value])
    
def dispatch_memory(otp_memory) :
    values = []
    for key in ["ets", "processes", "code", "binary", "atom_used", "atom", "system", "processes_used", "allocated", "total"] :
        values.append(otp_memory[key] if key in otp_memory else 0)
    collectd.Values(
        plugin = 'riak',
        type = "otp_memory"
    ).dispatch(values=values)

def dispatch_histograms(histograms) :
    for name, values in histograms.iteritems() :
        dispatch_histogram(name, values)
        
def dispatch_histogram(name, vals) :
    values = []
    for key in ["median", "mean", "95", "99", "100"] :
        values.append(vals[key] if key in vals else 0)
    collectd.Values(
        plugin = 'riak',
        type = "histogram",
        type_instance = name
    ).dispatch(values=values)

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
