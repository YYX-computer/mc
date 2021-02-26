@echo off
for %% i in (excute/*.py) do python "%%i"
python -X faulthandler window.py %python startup.py%
if exist fault do python report_fault.py
python cleanup.py
