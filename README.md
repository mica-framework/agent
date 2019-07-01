# The MiCA Agent
Welcome to the MiCA-Framework. 
MiCA stands for "Microservice-based Simulation of Cyber Attacks". This Agent is going to 
run at the victims system, which represents a already infiltrated and hacked client. To
be able to run commands on this system over the MiCA-Framework, the agent is required.
Running commands and attacks on the victim-side is not always possible for the MiCA-Framework,
so we need this Agent to guarantee the execution the commands on the client host.

## How to install
There are three ways to install the client on the system. You can clone the repo, download
the repo as a zip package or run download the executable from the repo through the console.

#### Download the executable by console - WINDOWS
```powershell
curl https://raw.githubusercontent.com/mica-framework/agent/master/dist/mica-agent-windows.exe --output mica-agent.exe
```

#### Download the executable by console - LINUX
```powershell
curl https://raw.githubusercontent.com/mica-framework/agent/master/dist/mica-agent-linux --output mica-agent
```


## How to build a executable
This agent can be executed by cloning the repository and interpreting the python
code, as well as by an executable. Therefore we usually need a executable for
a linux and a windows distribution.

At first it is necessary to go to clone the repository and then `cd`into the project
directory. Within this directory we are able to use the `pyinstaller` from `cdrx`
to create an executable with the help of a docker container. This allows us a OS independent
creation of an executable.

The <b>windows</b> executable can be created by running the following command:
```bash
docker run -v "$(pwd):/src/" cdrx/pyinstaller-windows "pyinstaller mica-agent.py --onefile"
```

The <b>linux</b> executable can be created by running the command:
```bash
docker run -v "$(pwd):/src/" cdrx/pyinstaller-linux "pyinstaller mica-agent.py --onefile"
```

The final executable will be available within the `/dist` directory. This directory contains
the .exe or binary which was generated.

If you'd like to create both executables for windows and linux, you can also use the provided
build script `build_executables`. This automatically creates the corresponding executables with
respect to the naming conventions of this project.


## License
This project is licensed under the terms of the MIT license. See the [LICENSE](https://raw.githubusercontent.com/mica-framework/agent/master/LICENSE) file.

## Contribution
If you like to contribute, don't hesitate to contact me or create a pull request or issue!
I'm looking forward to your feedback! :-)
