%if 0%{?rhel} <= 9
%global cuda_home /usr/local/cuda-12
%else
%global cuda_home /usr/local/cuda-13
%endif

%global cuda_arches 75;80;86;89;90;90a;120

# Do not generate debuginfo/debugsource subpackages.
%global debug_package %{nil}

# Do not generate /usr/lib/.build-id links.
%global _build_id_links none

%bcond_with test
%if %{with test}
%global build_test ON
%else
%global build_test OFF
%endif

%{!?upstream_version:%{error:upstream_version must be defined, e.g. rpmbuild --define 'upstream_version b8064'}}

Summary:        LLM inference in C/C++
Name:           llama-cpp
License:        MIT AND Apache-2.0
Version:        %{upstream_version}
Release:        1%{?dist}

URL:            https://github.com/ggml-org/llama.cpp
Source0:        %{name}-%{upstream_version}.tar.gz
Patch0:         tp-fix-ctx-size.patch
Patch1:         split-mode-tensor-kv-quant-enable.patch

BuildRequires:  cmake >= 3.14
BuildRequires:  gcc-c++
BuildRequires:  libcurl-devel
BuildRequires:  openssl-devel
BuildRequires:  libnccl-devel

# CUDA toolkit / nvcc.
# Adjust the package name if your CUDA repository uses different names.
%if 0%{?rhel} <= 9
BuildRequires:  cuda-toolkit-12-9
%else
BuildRequires:  cuda-toolkit-13-1
%endif

Requires:       nvidia-driver-cuda-libs libcublas cuda-cudart libnccl%{?_isa}


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

%if %{with test}
%package test
Summary:        Tests for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description test
Test binaries for %{name}.
%endif

%prep
%autosetup -p1 -n %{name}-%{upstream_version}

%build
export CUDA_HOME=%{cuda_home}
export PATH=%{cuda_home}/bin:$PATH
export LD_LIBRARY_PATH=%{cuda_home}/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

# AlmaLinux/RHEL RPM builds link executables with hardened PIE defaults.
# With CUDA 13, CMake's CUDA compiler probe can fail at link time unless
# nvcc forwards PIC-compatible host flags explicitly.
# Pass -fPIC through nvcc to the host compiler so CUDA try-compile and
# normal object builds are compatible with the hardened linker setup.
export CUDAFLAGS="${CUDAFLAGS:+$CUDAFLAGS }-Xcompiler=-fPIC"

# mock has the CUDA toolkit, but not the real NVIDIA driver library.
# The CUDA toolkit provides a build-time libcuda stub, but some link steps
# need to resolve the SONAME libcuda.so.1 from libggml-cuda.so.
# Create a local build-only libcuda.so.1 symlink to the toolkit stub and
# expose it via -rpath-link. This is not installed into the RPM.
cuda_stub_dir="$PWD/cuda-stubs"
mkdir -p "$cuda_stub_dir"
ln -sf "%{cuda_home}/lib64/stubs/libcuda.so" "$cuda_stub_dir/libcuda.so.1"
export LIBRARY_PATH="$cuda_stub_dir:%{cuda_home}/lib64/stubs${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$cuda_stub_dir:%{cuda_home}/lib64/stubs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Split functions/data into separate sections, then let the linker remove
# unused sections and emit stripped ELF binaries directly.  This avoids a
# separate strip pass, which can fail on EL9 with newer ELF sections such as
# .relr.dyn.
export CFLAGS="${CFLAGS:-} -ffunction-sections -fdata-sections"
export CXXFLAGS="${CXXFLAGS:-} -ffunction-sections -fdata-sections"
export LDFLAGS="${LDFLAGS:-} -Wl,--gc-sections -Wl,--strip-all -Wl,-rpath-link,$cuda_stub_dir -Wl,-rpath-link,%{cuda_home}/lib64/stubs"

mkdir -p build
rm -rf build/*

cmake -B build \
  -DGGML_CUDA=ON \
  -DGGML_CUDA_NCCL=ON \
  -DGGML_NATIVE=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_CUDA_ARCHITECTURES="%{cuda_arches}" \
  -DCMAKE_CUDA_COMPILER=%{cuda_home}/bin/nvcc \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA_FA_ALL_QUANTS=ON \
  -DGGML_RPC=ON \
  -DCMAKE_INSTALL_PREFIX=%{_prefix} \
  -DCMAKE_INSTALL_LIBDIR=%{_lib} \
  -DCMAKE_EXE_LINKER_FLAGS="$LDFLAGS" \
  -DCMAKE_SHARED_LINKER_FLAGS="$LDFLAGS" \
  -DLLAMA_BUILD_EXAMPLES=OFF \
  -DLLAMA_BUILD_TESTS=%{build_test} \
  -DLLAMA_BUILD_UI=OFF

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
%if %{with test}
%exclude %{_bindir}/test-*
%endif

%if %{with test}
%files test
%{_bindir}/test-*
%endif

%changelog
