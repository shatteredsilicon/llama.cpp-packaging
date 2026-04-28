Name:           cuda-virtual-provides
Version:        1.0.0
Release:        2%{?dist}
Summary:        Virtual provides for CUDA libs required by package
License:        MIT
BuildArch:      noarch

# Satisfy package’s name-based deps:
Provides:       libcublas
Provides:       cuda-cudart

# Ensure the *actual* libraries exist (works with 12.9 or 13.0, any vendor pkg):
%if 0%{?rhel} <= 9
Requires:       libcublas.so.12()(64bit)
Requires:       libcudart.so.12()(64bit)
%else
Requires:       libcublas.so.13()(64bit)
Requires:       libcudart.so.13()(64bit)
%endif

%description
Metapackage that maps package's generic CUDA deps to the real shared objects.

%files
# no files

%changelog
* Sat Dec 13 2025 Gordan Bobic <gordan@shatteredsilicon.net - 1.0.0-2
- Add EL10 compatibility

* Thu Nov 13 2025 Thien Nguyen <nthien86@gmail.com> - 1.0.0-1
- Initial release
