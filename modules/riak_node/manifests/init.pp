

class base {

    include firewall
    firewall { '1 Riak ports' :
        port => [8087, 8098, 8099, 44440-44444],
        proto => tcp,
        action => accept
    }
    firewall { '2 epmd port' :
        port => 4369,
        proto => tcp,
        action => accept
    }
    firewall { '3 solr port' :
        port => 8093,
        proto => tcp,
        action => accept
    }
    firewall { '4 jmx port' :
        port => 8985,
        proto => tcp,
        action => accept
    }

    class { 'ntp' :
        servers => ['marx.home']
    }
    
    package { 'riak' :
        name   => "riak",
        ensure => installed,
    }
    
    service { 'riak' :
        enable => true,
        ensure => running,
        require => Package['riak'],
    }
    
    file { '/etc/riak/riak.conf' :
        ensure      =>      file,
        content     =>      template('base/riak.conf.erb'),
        path        =>      '/etc/riak/riak.conf',
        notify      =>      Service['riak'],
    }
    
    file { '/etc/security/limits.d/riak.conf' :
        ensure      =>      file,
        content     =>      template('base/limits.conf.erb'),
        path        =>      '/etc/security/limits.d/riak.conf',
        notify      =>      Service['riak'],
    }
    
    package { 'rrdtool' :
        name   => "rrdtool",
        ensure => installed,
    }
    
    file { [ 
        "/opt",
        "/opt/collectd-5.4.2", 
        "/opt/collectd-5.4.2/etc",
        "/opt/collectd-5.4.2/etc/collectd.d",
        "/opt/collectd-5.4.2/share",
        "/opt/collectd-5.4.2/share/collectd",
        "/opt/collectd-5.4.2/lib",
        "/opt/collectd-5.4.2/lib/python",
        "/opt/collectd-5.4.2/lib/python/basho"
        ] :
        ensure => "directory",
    }
    
    file { "/opt/collectd-5.4.2/etc/collectd.conf" :
        path => "/opt/collectd-5.4.2/etc/collectd.conf",
        require => File['/opt/collectd-5.4.2/etc'],
        source => "puppet:///modules/base/collectd/etc/collectd.conf",
        notify => Service['collectd'],
    }
    
    file { "/opt/collectd-5.4.2/etc/collectd.d/riak.conf" :
        path => "/opt/collectd-5.4.2/etc/collectd.d/riak.conf",
        require => File['/opt/collectd-5.4.2/etc/collectd.d'],
        source => "puppet:///modules/base/collectd/etc/collectd.d/riak.conf",
        notify => Service['collectd'],
    }
    
    file { "/opt/collectd-5.4.2/etc/collectd.d/jmx.conf" :
        path => "/opt/collectd-5.4.2/etc/collectd.d/jmx.conf",
        require => File['/opt/collectd-5.4.2/etc/collectd.d'],
        source => "puppet:///modules/base/collectd/etc/collectd.d/jmx.conf",
        notify => Service['collectd'],
    }
    
    file { "/opt/collectd-5.4.2/share/collectd/basho-types.db" :
        path => "/opt/collectd-5.4.2/share/collectd/basho-types.db",
        require => File['/opt/collectd-5.4.2/share/collectd'],
        source => "puppet:///modules/base/collectd/share/collectd/basho-types.db",
        notify => Service['collectd'],
    }
    
    file { "/opt/collectd-5.4.2/lib/python/basho/riak.py" :
        path => "/opt/collectd-5.4.2/lib/python/basho/riak.py",
        require => File['/opt/collectd-5.4.2/lib/python/basho'],
        source => "puppet:///modules/base/collectd/lib/python/basho/riak.py",
        notify => Service['collectd'],
    }
    
    file { "/etc/init.d/collectd" :
        path => "/etc/init.d/collectd",
        source => "puppet:///modules/base/collectd/init.d/collectd",
        owner => "root",
        mode => "u+rwx"
    }
    
    service { 'collectd' :
        enable => true,
        ensure => running,
        require => File['/etc/init.d/collectd'],
    }
}
