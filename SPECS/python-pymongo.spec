%bcond_without python3
%bcond_with python36_module

# Only build on architectures supported by mongodb in RHEL8
%global mongodb_arches x86_64 ppc64le aarch64 s390x

# Fix private-shared-object-provides error
%{?filter_setup:
%filter_provides_in %{python2_sitearch}.*\.so$
%filter_setup
}

# Conditionalize tests
%bcond_with tests

%if 0%{?rhel} > 7
# Disable python2 build by default
%bcond_with python2
%else
%bcond_without python2
%endif

Name:           python-pymongo
Version:        3.7.0
Release:        1%{?dist}

# All code is ASL 2.0 except bson/time64*.{c,h} which is MIT
License:        ASL 2.0 and MIT
Summary:        Python driver for MongoDB
URL:            http://api.mongodb.org/python
Source0:        https://github.com/mongodb/mongo-python-driver/archive/%{version}/pymongo-%{version}.tar.gz

# Only build on architectures supported by mongodb in RHEL8
ExclusiveArch:  %{mongodb_arches}

# This patch removes the bundled ssl.match_hostname library as it was vulnerable to CVE-2013-7440
# and CVE-2013-2099, and wasn't needed anyway since Fedora >= 22 has the needed module in the Python
# standard library. It also adjusts imports so that they exclusively use the code from Python.
Patch01:        0001-Use-ssl.match_hostname-from-the-Python-stdlib.patch

%if %{with tests}
%ifnarch armv7hl ppc64 s390 s390x
# These are needed for tests, and the tests don't work on armv7hl.
# MongoDB server is not available on big endian arches (ppc64, s390(x)).
BuildRequires:  mongodb-server
BuildRequires:  net-tools
BuildRequires:  procps-ng
%endif
%endif # with tests

%if %{with python2}
BuildRequires:  python2-tools
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
%endif # with python2

%if %{with python3}
%if %{with python36_module}
BuildRequires:  python36-devel
BuildRequires:  python36-rpm-macros
%else
BuildRequires:  python3-devel
%endif
BuildRequires:  python3-setuptools
BuildRequires:  python3-sphinx
%endif

%description
The Python driver for MongoDB.


%if %{with python3}
%package doc
BuildArch: noarch
Summary:   Documentation for python-pymongo


%description doc
Documentation for python-pymongo.
%endif

%if %{with python2}
%package -n python2-bson
Summary:        Python bson library
%{?python_provide:%python_provide python2-bson}


%description -n python2-bson
BSON is a binary-encoded serialization of JSON-like documents. BSON is designed
to be lightweight, traversable, and efficient. BSON, like JSON, supports the
embedding of objects and arrays within other objects and arrays.
%endif # with python2


%if %{with python3}
%package -n python3-bson
Summary:        Python bson library
%{?python_provide:%python_provide python3-bson}


%description -n python3-bson
BSON is a binary-encoded serialization of JSON-like documents. BSON is designed
to be lightweight, traversable, and efficient. BSON, like JSON, supports the
embedding of objects and arrays within other objects and arrays.  This package
contains the python3 version of this module.
%endif


%if %{with python2}
%package -n python2-pymongo
Summary:        Python driver for MongoDB

Requires:       python2-bson%{?_isa} = %{version}-%{release}
Obsoletes:      pymongo <= 2.1.1-4
%{?python_provide:%python_provide python2-pymongo}


%description -n python2-pymongo
The Python driver for MongoDB.  This package contains the python2 version of
this module.
%endif # with python2


%if %{with python3}
%package -n python3-pymongo
Summary:        Python driver for MongoDB
Requires:       python3-bson%{?_isa} = %{version}-%{release}
%{?python_provide:%python_provide python3-pymongo}


%description -n python3-pymongo
The Python driver for MongoDB.  This package contains the python3 version of
this module.
%endif

%if %{with python2}
%package -n python2-pymongo-gridfs
Summary:        Python GridFS driver for MongoDB
Requires:       python2-pymongo%{?_isa} = %{version}-%{release}
Obsoletes:      pymongo-gridfs <= 2.1.1-4
%{?python_provide:%python_provide python2-pymongo-gridfs}


%description -n python2-pymongo-gridfs
GridFS is a storage specification for large objects in MongoDB.
%endif # with python2


%if %{with python3}
%package -n python3-pymongo-gridfs
Summary:        Python GridFS driver for MongoDB
Requires:       python3-pymongo%{?_isa} = %{version}-%{release}
%{?python_provide:%python_provide python3-pymongo-gridfs}


%description -n python3-pymongo-gridfs
GridFS is a storage specification for large objects in MongoDB.  This package
contains the python3 version of this module.
%endif


%prep
%setup -q -n mongo-python-driver-%{version}
%patch01 -p1 -b .ssl

# Remove the bundled ssl.match_hostname library as it was vulnerable to CVE-2013-7440
# and CVE-2013-2099, and isn't needed anyway since Fedora >= 22 has the needed module in the Python
# standard library.
rm pymongo/ssl_match_hostname.py

%build
%if %{with python2}
%py2_build
%endif # with python2

%if %{with python3}
%py3_build

pushd doc
SPHINXBUILD=sphinx-build-3 make %{?_smp_mflags} html
popd
%endif


%install
%if %{with python2}
%py2_install
# Fix permissions
chmod 755 %{buildroot}%{python2_sitearch}/bson/*.so
chmod 755 %{buildroot}%{python2_sitearch}/pymongo/*.so
%endif # with python2

%if %{with python3}
%py3_install
# Fix permissions
chmod 755 %{buildroot}%{python3_sitearch}/bson/*.so
chmod 755 %{buildroot}%{python3_sitearch}/pymongo/*.so
%endif


%if %{with tests}
%check
# For some reason, the tests never think they can connect to mongod on armv7hl even though netstat
# says it's listening. mongod is not available on big endian arches (ppc64, s390(x)).
%ifnarch armv7hl ppc64 s390 s390x

if [ "$(netstat -ln | grep :27017)" != "" ]
then
    pkill mongod
fi

mkdir ./mongod
mongod --fork --dbpath ./mongod --logpath ./mongod/mongod.log
# Give MongoDB some time to settle
while [ "$(netstat -ln | grep :27017)" == "" ]
do
    sleep 1
done

%if %{with python2}
%{__python2} setup.py test || (pkill mongod && exit 1)
%endif # with python2

%if %{with python3}
%{__python3} setup.py test || (pkill mongod && exit 1)
%endif

pkill mongod
%endif
%endif # with tests


%if %{with python3}
%files doc
%license LICENSE
%doc doc/_build/html/*
%endif

%if %{with python2}
%files -n python2-bson
%license LICENSE
%doc README.rst
%{python2_sitearch}/bson
%endif # with python2


%if %{with python3}
%files -n python3-bson
%license LICENSE
%doc README.rst
%{python3_sitearch}/bson
%endif

%if %{with python2}
%files -n python2-pymongo
%license LICENSE
%doc README.rst
%{python2_sitearch}/pymongo
%{python2_sitearch}/pymongo-%{version}-*.egg-info
%endif # with python2


%if %{with python3}
%files -n python3-pymongo
%license LICENSE
%doc README.rst
%{python3_sitearch}/pymongo
%{python3_sitearch}/pymongo-%{version}-*.egg-info
%endif

%if %{with python2}
%files -n python2-pymongo-gridfs
%license LICENSE
%doc README.rst
%{python2_sitearch}/gridfs
%endif # with python2


%if %{with python3}
%files -n python3-pymongo-gridfs
%license LICENSE
%doc README.rst
%{python3_sitearch}/gridfs
%endif


%changelog
* Fri Oct 09 2020 Lukas Javorsky <ljavorsk@redhat.com> - 3.7.0-1
- Rebase to 3.7.0
- Includes new SCRAM-SHA-256 authentication
  Resolves: rhbz#1879852

* Fri Jun 07 2019 Tomas Orsava <torsava@redhat.com> - 3.6.1-11
- Fix unversioned python macro that's causing a FTBFS
- Related: rhbz#1678920

* Thu Apr 25 2019 Tomas Orsava <torsava@redhat.com> - 3.6.1-10
- Bumping due to problems with modular RPM upgrade path
- Resolves: rhbz#1695587

* Thu Mar 28 2019 Charalampos Stratakis <cstratak@redhat.com> - 3.6.1-9
- Disable the test suite as mongodb is not available anymore

* Tue Oct 09 2018 Lumír Balhar <lbalhar@redhat.com> - 3.6.1-8
- Remove unversioned provides
- Resolves: rhbz#1628242

* Tue Jul 31 2018 Lumír Balhar <lbalhar@redhat.com> - 3.6.1-7
- Make possible to disable python3 subpackage

* Wed Jul 18 2018 Tomas Orsava <torsava@redhat.com> - 3.6.1-6
- BuildRequire the python36-devel package when building for the python36 module
- BuildRequire also python36-rpm-macros as part of the python36 module build

* Tue Jun 26 2018 Tomas Orsava <torsava@redhat.com> - 3.6.1-5
- Fix checking of running mongod - test only open ports (not I-Node number)

* Mon Jun 25 2018 Tomas Orsava <torsava@redhat.com> - 3.6.1-4
- Only build on architectures supported by mongodb in RHEL8
- Re-enable tests

* Tue Jun 19 2018 Charalampos Stratakis <cstratak@redhat.com> - 3.6.1-3
- Conditionalize the python2 subpackage
- Conditionalize tests and disable them for now

* Thu Jun 14 2018 Tomas Orsava <torsava@redhat.com> - 3.6.1-2
- Switch to using Python 3 version of sphinx

* Sat Mar 10 2018 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.6.1-1
- Update to 3.6.1 (#1550757).
- http://api.mongodb.com/python/3.6.1/changelog.html

* Mon Feb 19 2018 Marek Skalický <mskalick@redhat.com> - 3.6.0-1
- Rebase to latest release

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Sep 22 2017 Marek Skalický <mskalick@redhat.com> - 3.5.1-1
- Update to latest version

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 07 2017 Igor Gnatenko <ignatenko@redhat.com> - 3.4.0-5
- Rebuild due to bug in RPM (RHBZ #1468476)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Jan 06 2017 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.4.0-3
- Run the test suite in the check section (#1409251).

* Tue Dec 20 2016 Miro Hrončok <mhroncok@redhat.com> - 3.4.0-2
- Rebuild for Python 3.6

* Sun Dec 18 2016 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.4.0-1
- Update to 3.4.0 (#1400227).
- Use new install macros.
- Drop unneeded BuildRequires on python-nose.
- pymongo now requires bson by arch as it should.

* Fri Dec 09 2016 Charalampos Stratakis <cstratak@redhat.com> - 3.3.0-6
- Rebuild for Python 3.6

* Tue Nov 29 2016 Dan Horák <dan[at]danny.cz> - 3.3.0-5
- Update test BRs

* Fri Nov 25 2016 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.3.0-4
- Run the tests with setup.py test instead of with nosetests.

* Fri Nov 25 2016 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.3.0-3
- Run the tests against a live mongod.

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Fri Jul 15 2016 Randy Barlow <bowlofeggs@fedoraproject.org> - 3.3.0-1
- Update to 3.3.0 (#1356334).
- Remove the exclude arch on big endian systems, since 3.3.0 now supports them.
- Use the newer Python build macros.
- Add a skip test on another test that requires a running mongod.
- Convert the -doc subpackage into a noarch, as it should be.
- python2-pymongo-gridfs now requires python2-pymongo(isa) instead of python-pymongo(isa).
- Build the docs in parallel.

* Tue Mar 15 2016 Randy Barlow <rbarlow@redhat.com> - 3.2.2-1
- Update to 3.2.2 (#1318073).

* Wed Feb 03 2016 Randy Barlow <rbarlow@redhat.com> - 3.2.1-1
- Remove use of needless defattr macros (#1303426).
- Update to 3.2.1 (#1304137).
- Remove lots of if statements as this spec file will only be used on Rawhide.
- Remove dependency on python-backports-ssl_match_hostname as it is not needed in Fedora.
- Rework the patch for CVE-2013-7440 and CVE-2013-2099 so that it exclusively uses code from Python.

* Tue Jan 19 2016 Randy Barlow <rbarlow@redhat.com> - 3.2-1
- Update to 3.2.
- Rename the python- subpackages with a python2- prefix.
- Add a -doc subpackage with built html docs.
- Skip a few new tests that use MongoDB.
- Reorganize the spec file a bit.
- Use the license macro.
- Pull source from GitHub.

* Mon Jan 18 2016 Randy Barlow <rbarlow@redhat.com> - 3.0.3-3
- Do not use 2to3 for Python 3 (#1294130).

* Wed Nov 04 2015 Matej Stuchlik <mstuchli@redhat.com> - 3.0.3-2
- Rebuilt for Python 3.5

* Thu Oct 01 2015 Haïkel Guémar <hguemar@fedoraproject.org> - 3.0.3-1
- Upstream 3.0.3
- Fix CVE-2013-7440 (RHBZ#1231231 #1231232)

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 14 2014 Bohuslav Kabrda <bkabrda@redhat.com> - 2.5.2-4
- Rebuilt for https://fedoraproject.org/wiki/Changes/Python_3.4

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Jun 13 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5.2-2
- Bump the obsoletes version for pymongo-gridfs

* Wed Jun 12 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5.2-1
- Update to pymongo 2.5.2

* Tue Jun 11 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5-5
- Bump the obsoletes version

* Wed Apr 24 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5-4
- Fix the test running procedure

* Wed Apr 24 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5-3
- Exclude tests in pymongo 2.5 that depend on MongoDB

* Mon Apr 22 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.5-1
- Update to PyMongo 2.5 (bug #954152)

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jan  5 2013 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-6
- Fix dependency of python3-pymongo-gridfs (bug #892214)

* Tue Nov 27 2012 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-5
- Fix the name of the python-pymongo-gridfs subpackage

* Tue Nov 27 2012 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-4
- Fix obsoletes for python-pymongo-gridfs subpackage

* Tue Nov 27 2012 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-3
- Fix requires to include the arch, and add docs to all subpackages

* Tue Nov 27 2012 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-2
- Remove preexisting egg-info

* Mon Nov 26 2012 Andrew McNabb <amcnabb@mcnabbs.org> - 2.3-1
- Rename, update to 2.3, and add support for Python 3

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Apr 10 2012 Silas Sewell <silas@sewell.org> - 2.1.1-1
- Update to 2.1.1

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Jul 24 2011 Silas Sewell <silas@sewell.org> - 1.11-1
- Update to 1.11

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.9-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Nov 18 2010 Dan Horák <dan[at]danny.cz> - 1.9-5
- add ExcludeArch to match mongodb package

* Tue Oct 26 2010 Silas Sewell <silas@sewell.ch> - 1.9-4
- Add comment about multi-license

* Thu Oct 21 2010 Silas Sewell <silas@sewell.ch> - 1.9-3
- Fixed tests so they actually run
- Change python-devel to python2-devel

* Wed Oct 20 2010 Silas Sewell <silas@sewell.ch> - 1.9-2
- Add check section
- Use correct .so filter
- Added python3 stuff (although disabled)

* Tue Sep 28 2010 Silas Sewell <silas@sewell.ch> - 1.9-1
- Update to 1.9

* Tue Sep 28 2010 Silas Sewell <silas@sewell.ch> - 1.8.1-1
- Update to 1.8.1

* Sat Dec 05 2009 Silas Sewell <silas@sewell.ch> - 1.1.2-1
- Initial build
