# 1000–850 mb Thickness Analysis

Python tools for collecting upper-air and daily climate data and analyzing the relationship between 1000–850 mb thickness and Miami.

The project combines NOAA/NWS upper-air observations with the daily Miami climate report, then uses the resulting dataset to create an interactive analysis dashboard.

## Workflow

NOAA/NWS Data
↓
Upper-Air + Climate Data Collection
This is scheduled to run after the Morning Climate Summary the following day which reports the high temperature the day before, sounding data gets 18Z yesterday and today 00Z and averages the value.
If only one sounding is available then it just uses that value. 
↓
Analysis-Ready CSV
↓
Thickness Analysis Dashboard

## Features

* Retrieves Miami daily climate observations from the National Weather Service
* Retrieves upper-air sounding data NOAA/SPC Sounding Page
* Calculates 1000–850 mb thickness
* Calculates 500 mb temperature and precipitable water
* Combines upper-air data with daily high/low temperatures and other climate observations
* Calculates the statistical relationship between 1000–850 mb thickness and high temperature
* Identifies days with larger temperature errors from the regression
* Provides an interactive Plotly/Dash dashboard
* Allows a user to enter a thickness value and see the corresponding regression-based temperature estimate

## Data Sources

* National Weather Service — Miami Climate Reports
* NOAA/SPC Upper-Air Sounding

## Running the Project

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the data collection script first:

```bash
python get_thickness_data.py
```

This creates/updates:

```text
daily_upperair_climate.csv
```

The dashboard script reads that CSV and launches a local interactive dashboard in the default web browser:

```bash
python thickness_dashboard.py
```

The dashboard runs locally at:

```text
http://127.0.0.1:8050
```

## Purpose

This project was developed as a meteorological analysis tool to examine how lower-tropospheric thickness relates to observed high temperatures in South Florida.

The dashboard provides a visual way to explore the relationship, identify unusual days, and examine individual observations.
