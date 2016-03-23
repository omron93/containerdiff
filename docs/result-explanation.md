# Explanation of a format of test results

Lets look closer to the output of individual tests.

### Packages test

* To know changes in installed RPM packages.

```python
>>> # For each added/removed package result list contains lists/tuples in form: '(package-name, package-version&release)'
>>> # To get list of added packages
>>> result["packages"]["added"]
[['bind-license', '9.9.4-29.el7'], ['pygobject3-base', '3.14.0-3.el7'], ['acl', '2.2.51-12.el7'], ['hostname', '3.13-3.el7'], ['systemd', '219-19.el7'], ['passwd', '0.79-4.el7'], ['gobject-introspection', '1.42.0-1.el7'], ['tar', '1.26-29.el7'], ['libss', '1.42.9-7.el7'], ['kmod', '20-5.el7'], ['qrencode-libs', '3.4.1-3.el7'], ['cryptsetup-libs', '1.6.7-1.el7'], ['dbus', '1.6.12-13.el7'], ['dracut', '033-359.el7'], ['dbus-python', '1.1.1-9.el7'], ['elfutils-libs', '0.163-3.el7'], ['dbus-glib', '0.100-7.el7']]

>>> # To get list of removed packages
>>> result["packages"]["removed"]
[['iptables', '1.4.21-13.el7'], ['libmnl', '1.0.3-7.el7'], ['libcroco', '0.6.8-5.el7'], ['less', '458-8.el7'], ['which', '2.20-7.el7'], ['libgomp', '4.8.3-9.el7'], ['groff-base', '1.22.2-8.el7'], ['iproute', '3.10.0-21.el7'], ['libunistring', '0.9.3-9.el7'], ['libnfnetlink', '1.0.1-4.el7'], ['fakesystemd', '1-17.el7.centos'], ['file', '5.11-21.el7'], ['iptables-services', '1.4.21-13.el7'], ['libnetfilter_conntrack', '1.0.4-2.el7']]

>>> # For each modified package result list contains a list/tuple in form: '(package-name, package-version&release-in-IMAGE1, package-version&release-in-IMAGE2)'
>>> result["packages"]["modified"]
[['libgcrypt', '1.5.3-12.el7', '1.5.3-12.el7_1.1'], ['libssh2', '1.4.3-8.el7', '1.4.3-10.el7'], ['glibc', '2.17-78.el7', '2.17-105.el7'], ['yum', '3.4.3-125.el7.centos', '3.4.3-132.el7.centos.0.1'], ['libstdc++', '4.8.3-9.el7', '4.8.5-4.el7'], ['grep', '2.20-1.el7', '2.20-2.el7'], ['ca-certificates', '2014.1.98-72.el7', '2015.2.4-71.el7'], ['filesystem', '3.2-18.el7', '3.2-20.el7'], ... 
```

### Files test

* To test files not from RPM 
* It has a really similar output format to package test

```python
>>> # For each added/removed file result list contains a lists/tuples in form: '(file-path, file-type)'
>>> # To get list of added files
>>> result["files"]["added"]
[['/var/lib/yum/yumdb/g/b3855cbde4b7f74665a9363a61b4c46440597123-glibc-2.17-105.el7-x86_64/installed_by', 'text/plain; charset=us-ascii'], ['/var/lib/yum/yumdb/l/a093aa861f1c40cd778340605ff9bc294b28603e-libffi-3.0.13-16.el7-x86_64/reason', 'text/plain; charset=us-ascii'], ['/var/lib/yum/yumdb/s/27f7f0189d0898d0e87007d97102619629a4de6d-sqlite-3.7.17-8.el7-x86_64/installed_by', 'text/plain; charset=us-ascii'], ...

>>> # To get list of removed files
>>> result["files"]["removed"]
[['/usr/share/locale/de@hebrew/LC_MESSAGES', 'inode/directory; charset=binary'], ['/etc/sysconfig/i18n', 'text/plain; charset=us-ascii'], ['/etc/localtime', 'application/octet-stream; charset=binary'], ['/usr/share/kde4/apps/kdm', 'inode/directory; charset=binary'], ['/usr/lib/systemd/system', 'inode/directory; charset=binary'], ['/etc/sysconfig/network-scripts/ifcfg-eth0', 'text/plain; charset=us-ascii'], ['/var/lib/yum/rpmdb-indexes/obsoletes', 'text/plain; charset=us-ascii'], ['/usr/share/locale/en@greek', 'inode/directory; charset=binary'], ['/run/lock', 'inode/directory; charset=binary'], ...

>>> # For each modified file result list contains a lists/tuples in form: '(file-path, file-type, unified-diff-of-files, file-metadata-diff)'
>>> # file-metadata-diff is is dictionary - key is a name of file property and value is is list '[value-in-IMAGE1, value-in-IMAGE2]'
>>> result["files"]["modified"]
[['/etc/openldap/certs/password', 'text/plain; charset=us-ascii', ['--- /tmp/tmpu6ijci8u/etc/openldap/certs/password', '+++ /tmp/tmpe_ejvo6j/etc/openldap/certs/password', '@@ -1 +1 @@', '-T676qEFUwqfJ22zRjdbTj1jkePLXXdsWmrNQ4L71afY=', '+oeBw3KWKOl86kSLVXDNOwcLOEXdbhnYlOx1XNEYo0Ak='], {}], ['/etc/sysconfig/network', 'text/plain; charset=us-ascii', ['--- /tmp/tmpu6ijci8u/etc/sysconfig/network', '+++ /tmp/tmpe_ejvo6j/etc/sysconfig/network', '@@ -1,3 +1 @@', '-NETWORKING=yes', '-NETWORKING_IPV6=no', '-HOSTNAME=localhost.localdomain', '+# Created by anaconda'], {'size': [65, 22]}], ...
```

### History test

* Docker history command returns a list of commands used to create an image. This test shows diff (in unified format) of these lists for first and second image.

```python
>>> result["history"]
['-MAINTAINER The CentOS Project <cloud-ops@centos.org> - ami_creator', '-ADD file:d68b6041059c394e0f95effd6517765405402b4302fe16cf864f658ba8b25a97 in /', '+MAINTAINER The CentOS Project <cloud-ops@centos.org>', '+ADD file:0f306a349a3c88d5686633e59384a6454e4058eb12195770971ee1e7c2305920 in /', '+LABEL name=CentOS Base Image', '+LABEL vendor=CentOS', '+LABEL license=GPLv2']
```

### Metadata test

* Docker inspect returns complex JSON structure. To be able to compare two similar structures they are "converted" into lists.
For example this dict `{"foo" : 1, "bar" : {"a" : 2, "b" : ["x=1", "y=2"]}}` is converted into `["foo = 1", "bar:a = 2", "bar:b = x=1", "bar:b = y=2"]`.
For more information see help for tests.metadata. This test shows a diff (in unified format) of converted lists for first and second image.

```
>>> result["metadata"]
['-Author = The CentOS Project <cloud-ops@centos.org> - ami_creator', '+Author = The CentOS Project <cloud-ops@centos.org>', '-Config:Hostname = deb8962cb3c5', '+Config:Hostname = e386f1033735', '-Config:Labels = None', '+Config:Labels:license = GPLv2', '+Config:Labels:vendor = CentOS', '+Config:Labels:name = CentOS Base Image', '-Config:Image = 172633e384200b683dd587c350fd568fbc50758b54bdba44c03666f9b4089daf', '+Config:Image = d16051f61d95102f090d660987f804c371791c3384cfea6b99fdf8df1072709d']
```
