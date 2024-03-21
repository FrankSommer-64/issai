#!/usr/bin/bash
cp -p pyproject-all.toml ../pyproject.toml
cd ..
hatchling build
