# Overview

Package `llama.cpp`

## Repository layout

~~~~ {.text}
llama.cpp-packaging/
├── README.md
├── Jenkinsfile.watcher
├── Jenkinsfile.build
├── keys/
│   └── RPM-GPG-KEY-llama-cpp.pub
└── rpmbuild/
    ├── SOURCES/
    │   └── prep-llama-cpp.sh
    └── SPECS/
        ├── cuda-virtual-provides.spec
        └── llama-cpp.spec
~~~~

The non-secret RPM public key is stored in this repository for package signing
verification and publication. The private signing key and passphrase remain
protected by Jenkins credentials.

# Build

~~~~ {.bash}
$ rpmbuild -bb --with test llama-cpp-<version>.src.rpm
~~~~

# Install

If you see an install error like:

~~~~ {.bash}
Error: 
 Problem: conflicting requests
  - nothing provides cuda-cudart needed by llama-cpp-0.12.10-1.el9.x86_64 from @commandline
  - nothing provides libcublas needed by llama-cpp-0.12.10-1.el9.x86_64 from @commandline
~~~~

Build and install a small `virtual provides` shim RPM that maps these generic names to the
actual CUDA SONAMEs present on your system (`libcudart.so.12` and `libcublas.so.12`).
Then install the `llama-cpp` RPM.

**1) Build the shim RPM**

~~~~ {.bash}
$ rpmbuild -bb cuda-virtual-provides.spec
~~~~

**2) Install the shim and then llama-cpp**

~~~~ {.bash}
sudo dnf install -y ./cuda-virtual-provides-1-1.noarch.rpm
sudo dnf install -y ./llama-cpp-<version>-1.el9.x86_64.rpm
~~~~

**Tip:** You should already have CUDA installed and `ldconfig` should see the libs:

~~~~ {.bash}
ldconfig -p | grep -E 'libcudart\.so\.12|libcublas\.so\.12'
~~~~
