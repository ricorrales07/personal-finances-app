# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 07:46:42 2023

@author: Ricardo Corrales Barquero
"""

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvasQTAgg):
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.subplots(2, 1)
        #self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)