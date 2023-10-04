# a-tools
Automate imaging, processing, analysis and reporting of digital storages, forensic images and information by different tools.
All tools can be used with [queue](https://github.com/daniel-radesjo/queue) to process images with multiple tools using multiple computers.

# Tools list
- axiom7.6.py [Win]: Processing and export of portable case with [Magnet Forensics Axiom](https://www.magnetforensics.com/products/magnet-axiom)

# axiom7.6.py [Win] (Magnet Forensics Axiom 7.6)
```
axiom7.6.py [-h] -n NAME -i IMG -p PATH [-w WORDLIST] [-t THREADS] [--type TYPE] [--temp TEMP] [--perf] [-v]
-h: Show help message
-n NAME: Case name
-i IMG: Image file
-p PATH: Case folder path (must exist)
-w WORDLIST: Wordlist file with passwords (one line/password)
-t THREADS: Set Processing threads count. Max supported by Axiom is 32 threads.
--type TYPE: Image type (win, mac, linux). Default is win.
--temp TEMP: Temp folder path
--perf: Show performance information
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
python axiom7.6.py -n CASE_1 -i Z:\CASE_1.E01 -p Z:\Axiom7.6 -w Z:\wordlist.txt -t 32 --perf
```
