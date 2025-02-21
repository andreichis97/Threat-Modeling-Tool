# Threat-Modeling-Tool

This repository contains the scripts and the ABL file for the Threat Modeling Tool

In order to use the tool you will firstly need to download ADOxx https://www.adoxx.org/live/download-guided ADOxx comes with 2 parts: ADOxx Development Toolkit and ADOxx Modeling Toolkit. The ThreatModeling_v2.abl file needs to be imported in the ADOxx Development Toolkit as a new library and then a user must be created and assigned to it. The Scripts folder contains all the files that implement the functionalities of the modeling tool such as generating Turtle code from diagrams. After the folder is downloaded, in the ADOxx Development Toolkit the following actions need to be done:

1) Select the "Library Management" tab
2) Click on "Settings"
3) Expand the GRAPHxx 1.0 library and click on "GRAPHxx 1.0 Dynamic"
4) Click on "Library attributes" from the side menu
5) Click on the "Add-ons" tab
6) In the "External Coupling" part click on "Large text field" (icon looking like a square)
7) You'll see some file paths that need to be modified in order to point to the location of the Scripts folder

All the Python scrips where developed using Python 3.10.4.
