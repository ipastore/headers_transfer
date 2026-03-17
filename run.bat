@echo off
call venv\Scripts\activate
python extract.py assets\screens\ assets\ScoutDecisionPlayerImport.xlsx %*
