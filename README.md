# N.E.F.S.' Simulator

## How to run

````shell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\run.ps1
````
### Alternatively: run the installer and install the program according to the dialog.

## Open files
1. start the program
2. select any vending machine
3. select a file in the menu under File > Open

## How to program executes step-by-step

### config.py gets loaded

config.py sets up the environment for our app.
This changes depending on some factors for example INDEV, which makes the app produce more output.

When checking for a suitable environment, it looks at the OS and the Python version.

It automatically looks if the app is compiled and changes the current working directory accordingly.

We then clone the default-config folder to %LOCALAPPDATA%/nefs_simulator. This is done so that the app can be installed on a global level.

Lastly we set the current working directory to be the appdata folder we cloned everything to earlier.

### main.py setup

First in main.py we declare some global variables that help with the compilation process.

Later in the __name__ == "__main__": section, we register different exit codes and get arguments using argparse.

Lastly we start the MainWindow class and the app class in a try except block to prevent any crashes without clear errors.

### App class

The initializer of the app class within a try except block:

- Set important storage locations using os.path.join
- Init IOManager for logs and popups
- Init AppSettings
- Configure logging level
- Start ThreadPool and submit extension loader
- Wait for extension_loader to be done
- Submit update check to thread pool
- Register automaton using the UiAutomaton class
- Load themes and styles
- Setup MainWindow GUI
  - This initializes all gui components, so a lot of work is done here
- Check for input path and load if it was given
- Start backend thread
- Set window size and position
- Apply themes (assign names iterative beforehand)
- Update window icon and title, and connect settings
- Start window (shows window) and load font after
  - Some gui components also use this to load certain things
- Start timer tick

The UiAutomaton is only initialized once and used for every automaton afterwards.

### Project Structure

default-config:
- config is for all settings files
- core is for all script (.py) files
  - libs is to overwrite included libraries like argparse with a different version
  - modules if for the different modules within the app
    - automaton is for everything to do with simulating
    - gui is for gui
    - abstractions is used to define abstract classes
    - ...
    - painter parses and draws the designs for states
    - serializer parses or serializes automaton (loading or saving)
    - storage handles everything related to AppSettings
- data is for all data files like icons, logs, or styles and themes
- extensions is for extensions

## How to compile N.E.F.S

- Run ./compile.bat, disable your Antivirus real-time protection, as that is known to interfere
- Install Inno Setup Script
- Open ./nefs_install_script.iss
- Hit the compile button
- You're done! The installer should be in ./ named something like nefs-v...-win10-11-x64-installer.exe
- Some people may have problems installing N.E.F.S, as it is unsigned and downloaded from the internet. Antivirus real-time protection if often the cause.
