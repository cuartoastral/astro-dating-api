#!/bin/bash

set -e

echo "Installing dependencies and building Swiss Ephemeris..."

# Install build tools and dependencies
apt-get update && apt-get install -y \
  build-essential \
  wget \
  unzip \
  libatlas-base-dev \
  libblas-dev \
  liblapack-dev \
  && rm -rf /var/lib/apt/lists/*

# Download and extract Swiss Ephemeris source
wget http://www.astro.com/ftp/swisseph/ephe/archive_zip/sweph_2.10.03.zip -O sweph.zip
unzip sweph.zip -d sweph_src
cd sweph_src/src

# Compile the shared library
make -f Makefile.sharedlib
make -f Makefile.sharedlib install

# Move the .so file to a location Python can find
cp libswisseph.so.2.0.0 /usr/local/lib/libswisseph.so.2
ln -s /usr/local/lib/libswisseph.so.2 /usr/local/lib/libswisseph.so

# Update ldconfig cache
ldconfig

cd ../..

# Now run pip install
pip install --no-cache-dir -r requirements.txt

echo "Build complete"
