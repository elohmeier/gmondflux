class gmond2influx (
  Enum['present', 'absent', 'file'] $binary_ensure,
  Stdlib::Absolutepath $binary_path,
  String $binary_owner,
  String $binary_group,
  Stdlib::Filemode $binary_mode,
  Boolean $binary_replace,
  Optional[Stdlib::Filesource] $binary_source,
  
  Stdlib::Ensure::Service $service_ensure,
  String $service_name,
  Boolean $service_enable,
  Optional[Boolean] $service_hasrestart,
  Optional[Stdlib::Absolutepath] $service_file_path,
  Optional[Stdlib::Filemode] $service_file_mode,
  Optional[Stdlib::Filesource] $service_file_source,
) {
  file { 'gmond2influx.py':
    ensure  => $gmond2influx::binary_ensure,
    path    => $gmond2influx::binary_path,
    owner   => $gmond2influx::binary_owner,
    group   => $gmond2influx::binary_group,
    mode    => $gmond2influx::binary_mode,
    source  => $gmond2influx::binary_source,
  }

  service { 'gmond2influx':
    ensure     => $gmond2influx::service_ensure,
    name       => $gmond2influx::service_name,
    enable     => $gmond2influx::service_enable,
    hasrestart => $gmond2influx::service_hasrestart,
  }

  systemd::unit_file { 'gmond2influx.service':
    source => $gmond2influx::service_file_source,
  }

  Class['systemd::systemctl::daemon_reload'] -> Service['gmond2influx']
}
