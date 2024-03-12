# %%define _binaries_in_noarch_packages_terminate_build 0
# %%define _unpackaged_files_terminate_build 0
%undefine _hardened_build
%undefine _annotated_build
%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11

# NEON support is by default enabled on aarch64 and disabled on other ARMs (it can be overridden)
%ifarch aarch64
%bcond_without neon
%else
%bcond_with neon
%endif

%ifarch %{arm}
%if %{with neon}
%global my_optflags %(echo -n "%{optflags}" | sed 's/-mfpu=[^ \\t]\\+//g'; echo " -mfpu=neon")
%{expand: %global optflags %{my_optflags}}
%global mfpu_neon -Dhave_mfpu_neon=1
%else
%global mfpu_neon -Dhave_mfpu_neon=0
%endif
%endif


# fmt API change workaround
%global optflags %(echo %{optflags} -DFMT_DEPRECATED_OSTREAM)

# For versions not yet on ftp, pull from git
#%%global git_commit 441a3767e05d15e62c519ea66b848b5adb0f4b3a
%global debug_package %{nil}
#%%global alphatag rc1

Name:		gnuradiopv
%global real_name gnuradio
Version:	3.10.7.0
Release:	2%{?alphatag:.%{alphatag}}%{?dist}
Summary:	Software defined radio framework

License:	GPLv3
URL:		https://www.github.com/pervices/gnuradio
#Source0:	http://gnuradio.org/releases/gnuradio/gnuradio-%%{version}%%{?alphatag}.tar.xz
#Source0:	http://gnuradio.org/releases/gnuradio/gnuradio-%%{version}.tar.gz
#Source0:	https://github.com/gnuradio/%%{real_name}/archive/v%%{version}/%%{real_name}-%%{version}.tar.gz
Source0:    gnuradiopv.tar.gz

Requires(pre):	shadow-utils
BuildRequires:	cmake
BuildRequires:	gcc-toolset-13
BuildRequires:	libtool
BuildRequires:	alsa-lib-devel
BuildRequires:	boost169-devel
BuildRequires:	codec2-devel
BuildRequires:	cppzmq-devel
BuildRequires:	desktop-file-utils
BuildRequires:	doxygen
BuildRequires:	fftw-devel
BuildRequires:	findutils
BuildRequires:	gmp-devel
BuildRequires:	graphviz
BuildRequires:	gsl-devel
BuildRequires:	gsm-devel
BuildRequires:	gtk3-devel
BuildRequires:	jack-audio-connection-kit-devel
BuildRequires:	portaudio-devel
BuildRequires:	python%{python3_pkgversion}-setuptools
BuildRequires:	python%{python3_pkgversion}-packaging
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-cairo
BuildRequires:	python%{python3_pkgversion}-click-plugins
BuildRequires:	python%{python3_pkgversion}-gobject
BuildRequires:	python%{python3_pkgversion}-numpy
BuildRequires:	python%{python3_pkgversion}-pyyaml
BuildRequires:	python%{python3_pkgversion}-lxml
BuildRequires:	python%{python3_pkgversion}-mako
BuildRequires:	python%{python3_pkgversion}-qt5-devel
BuildRequires:	python%{python3_pkgversion}-scipy
BuildRequires:	python%{python3_pkgversion}-thrift
BuildRequires:	python%{python3_pkgversion}-zmq
BuildRequires:	qwt-qt5-devel
BuildRequires:	tex(latex)
BuildRequires:	SDL-devel
BuildRequires:	thrift
# BuildRequires:	uhd-devel
BuildRequires:	uhdpv
BuildRequires:	xdg-utils
BuildRequires:	xmlto
BuildRequires:	zeromq-devel
BuildRequires:	python%{python3_pkgversion}-gobject
BuildRequires:	pybind11-devel
BuildRequires:	volk-devel
BuildRequires:	libsndfile-devel
BuildRequires:	SoapySDR-devel
BuildRequires:	spdlog-devel
# for pygccxml
#BuildRequires:	castxml

Requires:	python%{python3_pkgversion}-%{real_name} = %{version}-%{release}
Requires:	python%{python3_pkgversion}-numpy
Requires:	python%{python3_pkgversion}-thrift
%if ! 0%{?rhel}
Requires:	python%{python3_pkgversion}-pyopengl
%endif
Requires:	python%{python3_pkgversion}-pyyaml
Requires:	python%{python3_pkgversion}-gobject
Requires:	python%{python3_pkgversion}-mako
Requires:	python%{python3_pkgversion}-click-plugins
Requires:	python%{python3_pkgversion}-qt5
Requires:	python%{python3_pkgversion}-scipy 
Requires:	python%{python3_pkgversion}-pyqtgraph
Requires:	python%{python3_pkgversion}-zmq
Requires:	gtk3
Suggests:	soapy-rtlsdr

%description
GNU Radio is a collection of software that when combined with minimal
hardware, allows the construction of radios where the actual waveforms
transmitted and received are defined by software. What this means is
that it turns the digital modulation schemes used in today's high
performance wireless devices into software problems.

%package -n python%{python3_pkgversion}-%{name}
Summary:	GNU Radio Python 3 module

%description -n python%{python3_pkgversion}-%{name}
GNU Radio Python 3 module

%package devel
Summary:	GNU Radio
Requires:	%{name}%{?_isa} = %{version}-%{release}
Requires:	cmake
Requires:	boost169-devel%{?_isa}

%description devel
GNU Radio Headers

%package doc
Summary:	GNU Radio
Requires:	%{name} = %{version}-%{release}

%description doc
GNU Radio Documentation

%package examples
Summary:	GNU Radio
Requires:	%{name} = %{version}-%{release}

%description examples
GNU Radio examples

%prep
%setup -q -n %{name}

%build
source /opt/rh/gcc-toolset-13/enable
mkdir build
cd build
%cmake \
-DSYSCONFDIR=%{_sysconfdir} \
-DGR_PKG_DOC_DIR=%{_docdir}/%{real_name} \
-DGR_PYTHON_DIR=%{python3_sitearch} \
-DPYTHON_EXECUTABLE=%{__python3} \
-DENABLE_UHD_RFNOC=OFF \
-DENABLE_GR_ZEROMQ=OFF \
-Dspdlog_DIR=/usr/lib64 \
%{?mfpu_neon} \
..
#-DENABLE_DOXYGEN=FALSE \

%make_build CFLAGS="%{optflags} -fno-strict-aliasing" CXXFLAGS="%{optflags} -fno-strict-aliasing"

%install
%make_install -C build

# desktop file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications \
  grc/scripts/freedesktop/gnuradio-grc.desktop
# mime
install -Dp grc/scripts/freedesktop/gnuradio-grc.xml \
  %{buildroot}%{_datadir}/mime/packages/gnuradio-grc.xml
# metainfo
install -Dp grc/scripts/freedesktop/org.gnuradio.grc.metainfo.xml \
  %{buildroot}%{_datadir}/metainfo/org.gnuradio.grc.metainfo.xml
# icons
for i in 16 24 32 48 64 128 256
do
  install -Dp grc/scripts/freedesktop/grc-icon-${i}.png \
    %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/gnuradio-grc.png
done

%ldconfig_scriptlets

%files
%license COPYING
%{_bindir}/*
%{_libdir}/lib*.so.*
%{_datadir}/gnuradio
%{_datadir}/applications/gnuradio-grc.desktop
%{_datadir}/mime/packages/gnuradio-grc.xml
%{_datadir}/icons/hicolor/*/apps/gnuradio-grc.png
%{_datadir}/metainfo/org.gnuradio.grc.metainfo.xml
%{_mandir}/man1/*
%config(noreplace) %{_sysconfdir}/gnuradio
%exclude %{_datadir}/gnuradio/examples
%exclude %{_docdir}/%{real_name}/html
%exclude %{_docdir}/%{real_name}/xml
%doc %{_docdir}/%{real_name}

%files -n python%{python3_pkgversion}-%{name}
%{python3_sitearch}/%{real_name}/
%{python3_sitearch}/pmt/

%files devel
%{_includedir}/*
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_libdir}/cmake/gnuradio

%files doc
%doc %{_docdir}/%{real_name}/html
%doc %{_docdir}/%{real_name}/xml

%files examples
%{_datadir}/gnuradio/examples

%changelog
