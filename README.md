# SIG Preprocess

This project goal is to extract NDVI information to create a time series for a specific farm.

## Requirements

Necessary packages are listed in requirements.txt
Recommend creating a virtual enviroment for this installation.

## Directory structure

    .
    ├── data 
    │   ├── IMAGENS_PLANET     # Raw files
    │   ├── ndvi_images        # NDVI extracted files
    │   ├── clip_images        # NDVI and clipped files
    │   ├── gleba01.geojson    # Shape file
    ├── main.py                # Main file to run all preprocess
    ├── ndvi_band.ipynb        # Python notebook used to experiment and visualize NDVI extraction
    ├── clip.ipynb             # Python notebook used to clip images
    ├── ndvi_average.ipynb     # Python notebook used to get average NDVI of clipped NDVI images
    ├── README.md              # This document
    ├── requirements.txt       # Package requirements list

Data folder is private, it's creation should be done manually.