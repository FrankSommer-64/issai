#!/usr/bin/bash
cp -p pyproject-core.toml ../pyproject.toml
cd ..
hatchling build
