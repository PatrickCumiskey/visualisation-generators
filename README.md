# Chronotopic Cartographies - Visualisation Generators, Texts, and Explanatory Guide

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/chronotopic-cartographies/visualisation-generators/HEAD)

NOTE: This respoity is a minor adaptation of https://github.com/chronotopic-cartographies/visualisation-generators , allowable under GPL reference and forked with same licnese permissions. We highly reccomened you use the online notebok editor to run the code, as the changes in this fork only pertain to generating the final graph as an image. 
We enconuted issues with the image wand libray and could not get it isntalled, and further issues when converting the graphs to images with how the geometric object was referecend, as such we needed to make minor changes. 
We beleive the issues reovled out a differnece in environemnts. Most likely a minor difference in the version of a libray or of the python version, but we were not able to determeine the exact root cause, but implemented out own minor fix that solves hte issue, 
We also added a TestVisual.py file , this filw allows the quick conversion and viewing of a .graphmhl file to an svg, allowing it to be viewed in your python cdoe ediotr of choice. This is merely here for quick iterations of parameter fine tuning. 

This repository contains marked up texts, visualisations, and Python scripts for generating visualisations related to the AHRC-funded [*Chronotopic Cartographies for Literature*](https://www.lancaster.ac.uk/chronotopic-cartographies/) project at Lancaster University. 

This readme file gives instructions on how to access the tools, either online or on your own computer. Once you're set up, you can get started using the tools by opening the 'start_here.ipynb' notebook.

## Accessing the Tools

### Python Notebooks
The tools for creating the Chronotopic Cartographies maps/graphs are a series of Jupyter iPython Notebooks (https://jupyter.org/), which are a way for running Python code in a (fairly) user-friendly way. 

There are two ways of running the notebooks. The easiest is to click on the link below, which will open an interactive version of this repository on mybinder.org. This is a good option if you want to try the tools without having to install anything on your own computer. 

https://mybinder.org/v2/gh/chronotopic-cartographies/visualisation-generators/HEAD

Once the binder has loaded, click on the 'start_here.ipynb' notebook, which contains information about the tools and how to start using them.

If you find them useful, you can open them on your own computer using Anaconda, which can be downloaded from here: https://www.anaconda.com/products/individual

Once you've downloaded Anaconda, download this repository to your computer using the green 'code' link in the toolbar above. Open Anaconda and navigate to the place where you saved this repository then open the 'start_here.inpyb' notebook.

### Gephi
Whichever way you choose to run the notebooks, you will also need to install [Gephi](https://gephi.org/) on your computer. We use Gephi to lay out and edit graphs before exporting them to create the finished visualisations.
