#!/bin/bash

echo ">> Cleanup dist directory..."
rm ./dist/mica-agent-linux
rm ./dist/mica-agent-windows.exe

echo ">> Building Windows executable..."
docker run -v "$(pwd):/src/" cdrx/pyinstaller-windows "pyinstaller mica-agent.py --onefile --windowed"
mv dist/mica-agent.exe dist/mica-agent-windows.exe

echo ">> Building Linux executable..."
docker run -v "$(pwd):/src/" cdrx/pyinstaller-linux "pyinstaller mica-agent.py --onefile --windowed"
mv dist/mica-agent dist/mica-agent-linux

echo ">> Finished building executables!"