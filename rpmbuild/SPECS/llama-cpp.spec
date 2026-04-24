%if 0%{?rhel} <= 9
%global cuda_home /usr/local/cuda-12
%else
%global cuda_home /usr/local/cuda-13
%endif

%global cuda_arches 75;80;86;89;90;90a;120

%{!?upstream_version:%{error:upstream_version must be defined, e.g. rpmbuild --define 'upstream_version b8064'}}

Summary:        LLM inference in C/C++
Name:           llama-cpp
License:        MIT AND Apache-2.0
Version:        %{upstream_version}
Release:        1%{?dist}

URL:            https://github.com/ggml-org/llama.cpp
Source0:        %{name}-%{upstream_version}.tar.gz

BuildRequires:  cmake >= 3.14
BuildRequires:  gcc-c++
BuildRequires:  libcurl-devel
BuildRequires:  openssl-devel

# CUDA toolkit / nvcc.
# Adjust the package name if your CUDA repository uses different names.
%if 0%{?rhel} <= 9
BuildRequires:  cuda-toolkit-12-9
%else
BuildRequires:  cuda-toolkit-13-1
%endif

Requires:       nvidia-driver-cuda-libs libcublas cuda-cudart cuda-libraries


%description
The main goal of llama.cpp is to enable LLM inference with minimal setup and state-of-the-art performance on a wide
range of hardware - locally and in the cloud.

* Plain C/C++ implementation without any dependencies
* Apple silicon is a first-class citizen - optimized via ARM NEON, Accelerate and Metal frameworks
* AVX, AVX2, AVX512 and AMX support for x86 architectures
* RVV, ZVFH, ZFH, ZICBOP and ZIHINTPAUSE support for RISC-V architectures
* 1.5-bit, 2-bit, 3-bit, 4-bit, 5-bit, 6-bit, and 8-bit integer quantization for faster inference and reduced memory use
* Custom CUDA kernels for running LLMs on NVIDIA GPUs (support for AMD GPUs via HIP and Moore Threads GPUs via MUSA)
* CPU+GPU hybrid inference to partially accelerate models larger than the total VRAM capacity

The llama.cpp project is the main playground for developing new features for the ggml library.

%prep
%autosetup -p1 -n %{name}-%{upstream_version}

%build
export CUDA_HOME=%{cuda_home}
export PATH=%{cuda_home}/bin:$PATH
export LD_LIBRARY_PATH=%{cuda_home}/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

mkdir -p build
rm -rf build/*

cmake -B build \
  -DGGML_CUDA=ON \
  -DGGML_NATIVE=OFF \
  -DCMAKE_CUDA_ARCHITECTURES="%{cuda_arches}" \
  -DCMAKE_CUDA_COMPILER=%{cuda_home}/bin/nvcc \
  -DGGML_CUDA_FA_ALL_QUANTS=ON \
  -DGGML_RPC=ON \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_TESTS=OFF

cd build
cmake --build . -j --config Release

%install
cd build
DESTDIR=%{buildroot} cmake --install .

# Keep .so files, but remove headers/CMake/pkgconfig development metadata.
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_libdir}/cmake
rm -rf %{buildroot}%{_libdir}/pkgconfig

%files
%license LICENSE
%doc README.md

# Keep every installed shared library and .so symlink.
%{_libdir}/*.so
%{_libdir}/*.so.*

# Keep every installed executable.
%{_bindir}/*

%changelog
