# A-Tools
Automated imaging, processing, analysis and reporting of digital storages, forensic images and information by different tools.
All tools/scripts can be used with [queue](https://github.com/daniel-radesjo/queue) to process images with multiple tools using multiple computers.

Remember to turn off antivirus, screensaver, automatic screen lock, etc. Don't lock the screen when script is running. GUI automation cannot be running when screen is locked/visible. Power off screen manually when needed. Don't use the computer when script is running.

# Tools list
- [axiom77.py](#axiom77py-win-magnet-forensics-axiom-77) [Win]: Processing and export of portable case with [Magnet Forensics Axiom](https://www.magnetforensics.com/products/magnet-axiom)

# Required applications and modules
- Main tool used by the script must be installed, started and configured
- Python 3.8+
- Python modules for Windows: uiautomation, psutil, pywin32 (pip install uiautomation psutil pywin32)

# axiom77.py [Win] (Magnet Forensics Axiom 7.7)
Configure Axiom license/dongle before running script.
```
axiom77.py [-h] -n NAME -i IMG -p PATH [-w WORDLIST] [-t THREADS] [--type TYPE] [--temp TEMP] [--perf] [--checkdb] [-v]
-h: Show help message
-n NAME: Case name
-i IMG: Image file
-p PATH: Case folder path (must exist)
-w WORDLIST: Wordlist file with passwords (one password/line)
-t THREADS: Set Processing threads count. Max supported by Axiom is 32 threads.
--type TYPE: Image type (win, mac, linux). Default is win.
--temp TEMP: Temp folder path
--perf: Show performance information
--checkdb: Show settings database values and exit
-v: Show more verbose output

axiom.ini:
- [default]
  - Execute: Path to AXIOMProcess.exe
  - WaitTime: Seconds to wait between different actions and performance output
  - LogLevel: Default log level (ERROR, INFO, DEBUG)
- [steps]
  - Start: Start Axiom
  - Process: Process image
  - PortableCase: Export to portable case
  - Close: Close Axiom

Example:
python axiom77.py -n CASE_1 -i Z:\CASE_1.E01 -p Z:\Axiom7.6 -w Z:\wordlist.txt -t 32 --perf
```
