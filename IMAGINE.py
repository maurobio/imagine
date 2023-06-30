#!/usr/bin/env python
# -*- coding: utf-8 -*-
#=======================================================================#
#               IMAGINE - Biological Image Viewer & Processor           #
#                  (C) 2015 by Mauro J. Cavalcanti                      #
#                       <maurobio@gmail.com>                            #
#                                                                       #
#  This program is free software; you can redistribute it and/or modify #
#  it under the terms of the GNU General Public License as published by #
#  the Free Software Foundation; either version 3 of the License, or    #
#  (at your option) any later version.                                  #
#                                                                       #
#  This program is distributed in the hope that it will be useful,      #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        # 
#  GNU General Public License for more details.                         #
#                                                                       #
#  You should have received a copy of the GNU General Public License    #
#  along with this program. If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #       
#  Requirements:                                                        #
#    Python version 2.7+ (www.python.org)                               #
#    PyQt version 4.8+  (www.riverbankcomputing.com/software/pyqt)      #
#    NumPy version 1.9+  (www.numpy.org)                                #
#    OpenCV version 2.4+ (www.opencv.org)                               #
#    scikit-learn version 0.15+ (www.scikit-learn.org)                  #
#    Matplotlib version 0.98+ (www.matplotlib.org)                      #
#                                                                       #
#  REVISION HISTORY:                                                    #
#    Version 1.0.3, 02nd Feb 15 - Initial public release                #
#    Version 1.0.4, 13th Mar 15 - Second public release                 #
#    Version 1.0.5  16th Mar 15 - Third public release                  #
#=======================================================================#                                                

from __future__ import division
import sys, time, os, glob, platform, locale, math
import numpy as np
import cv2 #this is the main openCV class, the python binding file should be in /pythonXX/Lib/site-packages
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from os.path import basename
from PIL import Image
import sklearn
from sklearn.decomposition import RandomizedPCA
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QT_VERSION_STR
from PyQt4.Qt import PYQT_VERSION_STR

import resources

__version__ = "1.0.5"
APPNAME = "IMAGINE Biological Image Viewer & Processor"

#setup a standard image size; this will distort some images but will get everything into the same shape
STANDARD_SIZE = (300, 167)
def img_to_matrix(filename, verbose=False):
    """
    takes a filename and turns it into a numpy array of RGB pixels
    """
    img = Image.open(filename)
    if verbose==True:
        print filename, " changing size from %s to %s" % (str(img.size), str(STANDARD_SIZE))
    img = img.resize(STANDARD_SIZE)
    img = list(img.getdata())
    img = map(list, img)
    img = np.array(img)
    return img
 
def flatten_image(img):
    """
    takes in an (m, n) numpy array and flattens it
    into an array of shape (1, m * n)
    """
    s = img.shape[0] * img.shape[1]
    img_wide = img.reshape(1, s)
    return img_wide[0] 

class ImageViewer(QtGui.QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
        
        self.currentFile = None
        self.scaleFactor = 0.0
        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)
        
        self.statusBar()
        self.statusBar().showMessage(self.trUtf8("Ready"))
        
        self.createActions()
        self.createMenus()

        self.setWindowTitle(APPNAME)
        self.setGeometry(192, 107, 766, 441)
        self.setWindowIcon(QtGui.QIcon(":/icon.png"))

    def open(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 
                self.trUtf8("Open File"),
                QtCore.QDir.currentPath(),
                self.trUtf8("Image Files (*.jpg *.png *.tif)"))
        
        if fileName:
            os.chdir(str(QtCore.QFileInfo(fileName).path()))
            image = QtGui.QImage(fileName)
            if image.isNull():
                QtGui.QMessageBox.information(self, APPNAME,
                        self.trUtf8("Error loading %s.") % fileName)
                return

            self.imageLabel = QtGui.QLabel()
            self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
            self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                    QtGui.QSizePolicy.Ignored)
            self.imageLabel.setScaledContents(True)

            self.scrollArea = QtGui.QScrollArea()
            self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
            self.scrollArea.setWidget(self.imageLabel)
            self.setCentralWidget(self.scrollArea)

            self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            self.scrollArea.setWidgetResizable(True)
            self.currentFile = fileName

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()
        self.updateActions()

    def about(self):
        """Display About dialog box."""
        QtGui.QMessageBox.about(self, self.trUtf8("About IMAGINE"),
                "<b>IMAGINE Biological Image Viewer & Processor</b> v" + __version__ + "<p>" + \
                self.trUtf8("Detection, enumeration, and sizing of biological organisms by image analysis") + "<p>" + \
                "&copy; 2015 Mauro J. Cavalcanti<p>" + \
                "Python: " + platform.python_version() + \
                "<br>Qt: " + QT_VERSION_STR + \
                "<br>PyQt: " +  PYQT_VERSION_STR + \
                "<br>OpenCV: " + cv2.__version__ + \
                "<br>Matplotlib: " + matplotlib.__version__ + \
                "<br>scikit-learn: " + sklearn.__version__ + \
                "<br>OS: " + platform.system() + ' ' + platform.release())

    def createActions(self):
        self.openAct = QtGui.QAction(QtGui.QIcon(":/open.png"), self.trUtf8("&Open..."), self, 
                shortcut="Ctrl+O", statusTip=self.trUtf8("Open an existing file"), 
                triggered=self.open)

        self.exitAct = QtGui.QAction(QtGui.QIcon(":/exit.png"), self.trUtf8("E&xit"), 
                self, shortcut="Ctrl+Q", statusTip=self.trUtf8("Exit the application"), 
                triggered=self.close)

        self.zoomInAct = QtGui.QAction(self.trUtf8("Zoom &In (25%)"), self,
                shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QtGui.QAction(self.trUtf8("Zoom &Out (25%)"), self,
                shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QtGui.QAction(self.trUtf8("&Normal Size"), self,
                shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction(self.trUtf8("&Fit to Window"), self,
                enabled=False, checkable=True, shortcut="Ctrl+F",
                triggered=self.fitToWindow)
                
        self.countAct = QtGui.QAction(self.trUtf8("Cou&nt"), self,
                enabled=False, statusTip=self.trUtf8("Count objects"), 
                triggered=self.countObjects)
                
        self.classAct = QtGui.QAction(self.trUtf8("C&lassify"), self,
                enabled=True, statusTip=self.trUtf8("Classify objects"),
                triggered=self.classifyImages)

        self.aboutAct = QtGui.QAction(QtGui.QIcon(":/help.png"), self.trUtf8("&About"), self, 
                statusTip=self.trUtf8("Show the application's About box"), triggered=self.about)

        self.aboutQtAct = QtGui.QAction(QtGui.QIcon(":/qt.png"), self.trUtf8("About &Qt"), self,
                statusTip=self.trUtf8("Show the Qt library's About box"), triggered=QtGui.qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QtGui.QMenu(self.trUtf8("&File"), self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtGui.QMenu(self.trUtf8("&View"), self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        
        self.processMenu = QtGui.QMenu(self.trUtf8("&Process"), self)
        self.processMenu.addAction(self.countAct)
        self.processMenu.addAction(self.classAct)

        self.helpMenu = QtGui.QMenu(self.trUtf8("&Help"), self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.processMenu)
        self.menuBar().addMenu(self.helpMenu)
        
    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.countAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.classAct.setEnabled(self.fitToWindowAct.isChecked())
        
    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))
                                
    def countObjects(self):
        self.statusBar().showMessage(self.trUtf8("Processing..."))
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        filename = str(self.currentFile)
        # Image processing
        gwash = cv2.imread(filename) #import image
        gwashBW = cv2.cvtColor(gwash, cv2.COLOR_BGR2GRAY) #change to grayscale
        
        # Image threshold, erosion and contour extraction
        ret,thresh1 = cv2.threshold(gwashBW,15,255,cv2.THRESH_BINARY) #the value of 15 is chosen by trial-and-error to produce the best outline of the skull
        kernel = np.ones((5,5),np.uint8) #square image kernel used for erosion
        erosion = cv2.erode(thresh1, kernel,iterations = 1) #refines all edges in the binary image
        opening = cv2.morphologyEx(erosion, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel) #this is for further removing small noises and holes in the image
        contours, hierarchy = cv2.findContours(closing,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) #find contours with simple approximation

        # Calculating outline areas and extracting the skull outline
        i = 0
        areas = [] #list to hold all areas
        for contour in contours:
            ar = cv2.contourArea(contour)
            areas.append(ar)
            cnt = contours[i]
            cv2.drawContours(closing, [cnt], 0, (255, 255, 255), 3, maxLevel = 0)
            i += 1
        savefile = os.path.splitext(str(filename))[0] + "_img.png"
        cv2.imwrite(savefile, closing)
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(savefile)))
        self.scrollArea.setWidgetResizable(True)
        
        objects = []
        avg = np.mean(areas)
        for j in range(len(areas)):
            if areas[j] >= avg / 2:
                objects.append(areas[j])
        objects = np.sort(objects)
        nobj = len(objects)
        
        # Create html output file
        outf = os.path.splitext(os.path.basename(filename))[0] + ".htm"
        outfile = open(outf, "w")
        outfile.write("<!DOCTYPE HTML PUBLIC ""-//W3C//DTD HTML 3.2//EN"">")
        outfile.write("<html>\n")
        outfile.write("<head>\n")
        outfile.write("<title>" + APPNAME + "</title>\n")
        outfile.write("</head>\n")
        outfile.write("<body>\n\n")
        outfile.write("<h4>" + APPNAME + ' - ' + __version__ + "</h4>\n")
        outfile.write("<h4>" + self.trUtf8("Analysis of: ") + filename + "</h4>\n")
        outfile.write(self.trUtf8(u"Date: ") + time.strftime("%d/%m/%Y", time.localtime()) + "<br>\n")
        outfile.write(self.trUtf8(u"Time: ") + time.strftime("%H:%M:%S", time.localtime()) + "<br><br>\n\n")
        
        outfile.write("<table border=0 cellspacing=2 cellpadding=2 width=""80%"">\n")
        outfile.write("<tr>\n")
        outfile.write("<th>" + self.trUtf8("Original image") + "</th>")
        outfile.write("<th>" + self.trUtf8("Processed image") + "</th>")
        outfile.write("</tr>\n")
        outfile.write("<tr>")	
        outfile.write("<td align=""Center""><img src='" + os.path.basename(filename) + "' width=400 height=300>\n")
        outfile.write("<td align=""Center""><img src='" + os.path.basename(savefile) + "' width=400 height=300>\n")
        outfile.write("</tr>")
        outfile.write("</table>\n")
        
        outfile.write("<h4>Object sizes</h4>\n")
        outfile.write("<table border=0 cellspacing=1 cellpadding=1 width=""20%"">\n")
        outfile.write("<tr>\n")
        outfile.write("<td><b>" + self.trUtf8("Object") + "</b></td>")
        outfile.write("<td><b>" + self.trUtf8("Size (area)") + "</b></td>")
        outfile.write("</tr>\n")
        for i in range(len(objects)):
            outfile.write("<tr>")	
            outfile.write("<td align=""Left"">" + str(i+1) + "</td>\n")
            outfile.write("<td align=""Left"">" + "{:.1f}".format(objects[i]) + "</td>\n")
            outfile.write("</tr>")
        outfile.write("</table>\n")
        
        # Find number of size classes using Sturges algorithm
        k =  1 + 3.3 * np.log10(nobj)
        plt.clf()
        plt.hist(objects, bins=k)
        plt.xlabel(self.trUtf8("size"))
        plt.ylabel(self.trUtf8("frequency"))
        figurefile = os.path.splitext(str(filename))[0] + "_hist.png"
        plt.savefig(figurefile)
        outfile.write("<h4>" + self.trUtf8("Size distribution of objects") + "</h4>\n")
        outfile.write("<p><img src='" + os.path.basename(figurefile) + "' width=560 height=420></p>\n\n")
        
        outfile.write("</body>\n")
        outfile.write("</html>\n")
        outfile.close()
        
        self.statusBar().showMessage(self.trUtf8("Ready"))
        QtGui.QApplication.restoreOverrideCursor()
        QtGui.QMessageBox.information(self, APPNAME, str(nobj) + ' ' + self.trUtf8("object(s)"))
        self.textBrowser = QtGui.QTextBrowser()
        self.setCentralWidget(self.textBrowser)
        self.textBrowser.setSource(QtCore.QUrl(outf))
    
    def classifyImages(self):
        destDir = QtGui.QFileDialog.getExistingDirectory(None, 
                                                         self.trUtf8("Open working directory:"), 
                                                         "",  
                                                         QtGui.QFileDialog.ShowDirsOnly)
        if destDir:
            self.statusBar().showMessage(self.trUtf8("Processing..."))
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            os.chdir(str(destDir))
            images = glob.glob("*.jpg")
            data = []
            for image in images:
                try:
                    img = img_to_matrix(image)
                    img = flatten_image(img)
                    data.append(img)
                except:
                    QtGui.QMessageBox.information(self, APPNAME, "Error reading: " +  image)
                    continue
            data = np.array(data) 
            
            # Group objects by randomized principal components analysis
            pca = RandomizedPCA(n_components=2)
            X = pca.fit_transform(data)
            total_var = np.sum(pca.explained_variance_ratio_)
            
            # Create html output file
            outf = os.path.split(os.path.dirname(str(destDir)))[1] + ".htm"
            outfile = open(outf, "w")
            outfile.write("<!DOCTYPE HTML PUBLIC ""-//W3C//DTD HTML 3.2//EN"">")
            outfile.write("<html>\n")
            outfile.write("<head>\n")
            outfile.write("<title>" + APPNAME + "</title>\n")
            outfile.write("</head>\n")
            outfile.write("<body>\n\n")
            outfile.write("<h4>" + APPNAME + ' - ' + __version__ + "</h4>\n")
            outfile.write("<h4>" + self.trUtf8("Analysis of: ") + str(destDir) + "</h4>\n")
            outfile.write(self.trUtf8(u"Date: ") + time.strftime("%d/%m/%Y", time.localtime()) + "<br>\n")
            outfile.write(self.trUtf8(u"Time: ") + time.strftime("%H:%M:%S", time.localtime()) + "<br><br>\n\n")
            
            plt.clf()
            plt.scatter(X[:,0], X[:,1])
            for label, x, y in zip(images, X[:,0], X[:,1]):
                plt.annotate(str(label), xy = (x, y), xytext = (-10, 10), textcoords="offset points")
            plt.xlabel(self.trUtf8("PC 1 (") + "{:.1f}".format(pca.explained_variance_ratio_[0] * 100) + "%)")
            plt.ylabel(self.trUtf8("PC 2 (") + "{:.1f}".format(pca.explained_variance_ratio_[1] * 100)+ "%)")
            figurefile = os.path.split(os.path.dirname(str(destDir)))[1] + "_plot.png"
            plt.savefig(figurefile)
            outfile.write("<h4>" + self.trUtf8("Principal Components Analysis") + "</h4>\n")
            outfile.write("<h4>" + self.trUtf8("Total variance explained = ") + "{:.1f}".format(total_var * 100) + "&nbsp;%</h4>\n")
            outfile.write("<p><img src='" + os.path.basename(figurefile) + "' width=560 height=420></p>\n\n")
            
            outfile.write("</body>\n")
            outfile.write("</html>\n")
            outfile.close()
            
            self.statusBar().showMessage(self.trUtf8("Ready"))
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QMessageBox.information(self, APPNAME, "{:.1f}".format(total_var * 100) + self.trUtf8(" % total variance explained"))
            self.textBrowser = QtGui.QTextBrowser()
            self.setCentralWidget(self.textBrowser)
            self.textBrowser.setSource(QtCore.QUrl((outf)))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    locale = QtCore.QLocale.system().name()
    appTranslator = QtCore.QTranslator()
    if appTranslator.load("IMAGINE_" + locale, ":/"):
        app.installTranslator(appTranslator)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())