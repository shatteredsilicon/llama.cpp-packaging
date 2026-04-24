#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
spec_file="$script_dir/../SPECS/llama-cpp.spec"

if [[ ! -f "$spec_file" ]]; then
  echo "error: spec file not found: $spec_file" >&2
  exit 1
fi

VERSION="${1:-${VERSION:-$(awk '
  /^%global[[:space:]]+upstream_version[[:space:]]+/ { print $3; found=1; exit }
  /^Version:[[:space:]]+/ && !found { print $2; exit }
' "$spec_file")}}"

if [[ -z "${VERSION}" ]]; then
  echo "error: VERSION is empty; pass a tag or define upstream_version/Version in llama-cpp.spec" >&2
  exit 1
fi

cd "$script_dir"

archive_url="https://github.com/ggml-org/llama.cpp/archive/refs/tags/${VERSION}.tar.gz"
download_tar="${VERSION}.tar.gz"
source_dir="llama-cpp-${VERSION}"
output_tar="${source_dir}.tar.gz"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

echo "Downloading llama.cpp ${VERSION}"
wget -O "$tmpdir/$download_tar" "$archive_url"

tar -zxf "$tmpdir/$download_tar" -C "$tmpdir"

extracted_dir="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d -name 'llama.cpp-*' | head -n 1)"

if [[ -z "$extracted_dir" ]]; then
  echo "error: could not find extracted llama.cpp source directory" >&2
  exit 1
fi

rm -f "$output_tar"
rm -rf "$source_dir"

mv "$extracted_dir" "$source_dir"

tar \
  --sort=name \
  --mtime="@0" \
  --owner=0 \
  --group=0 \
  --numeric-owner \
  -czf "$output_tar" \
  "$source_dir"

rm -rf "$source_dir"

echo "Created $output_tar"
