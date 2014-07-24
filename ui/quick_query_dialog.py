# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickOSM
                                 A QGIS plugin
 OSM's Overpass API frontend
                             -------------------
        begin                : 2014-06-11
        copyright            : (C) 2014 by 3Liz
        email                : info at 3liz dot com
        contributor          : Etienne Trimaille
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from QuickOSMWidget import *
from qgis.gui import QgsMessageBar
from qgis.core import *
from quick_query import Ui_ui_quick_query      
from QuickOSM.Controller.Process import Process
from QuickOSM.CoreQuickOSM.ExceptionQuickOSM import *

#shoud not be here, use controller
from QuickOSM.CoreQuickOSM.QueryFactory import QueryFactory

import os
from qgis.utils import iface


class QuickQueryWidget(QuickOSMWidget, Ui_ui_quick_query):
    def __init__(self, parent=None):
        '''
        QuickQueryWidget constructor
        '''
        QuickOSMWidget.__init__(self)
        self.setupUi(self)
        
        #Setup UI
        self.lineEdit_filePrefix.setDisabled(True)
        self.groupBox.setCollapsed(True)
        self.fillLayerCombobox()
        self.allowButtons()
               
        #connect
        self.pushButton_runQuery.clicked.connect(self.runQuery)
        self.pushButton_showQuery.clicked.connect(self.showQuery)
        self.pushButton_browse_output_file.clicked.connect(self.setOutDirPath)
        self.lineEdit_key.textEdited.connect(self.allowButtons)
        self.lineEdit_browseDir.textEdited.connect(self.disablePrefixFile)
        self.radioButton_extentLayer.toggled.connect(self.allowNominatimOrExtent)
        self.radioButton_extentMapCanvas.toggled.connect(self.allowNominatimOrExtent)
        self.radioButton_place.toggled.connect(self.allowNominatimOrExtent)
        self.pushButton_refreshLayers.clicked.connect(self.fillLayerCombobox)

    def allowButtons(self):
        if self.lineEdit_key.text():
            self.pushButton_runQuery.setDisabled(False)
            self.pushButton_showQuery.setDisabled(False)
        else:
            self.pushButton_runQuery.setDisabled(True)
            self.pushButton_showQuery.setDisabled(True)
 
    def allowNominatimOrExtent(self):
        '''
        Disable or enable radiobuttons if nominatim or extent
        '''
        if self.radioButton_extentMapCanvas.isChecked() or self.radioButton_extentLayer.isChecked():
            self.lineEdit_nominatim.setDisabled(True)
        else:
            self.lineEdit_nominatim.setDisabled(False)
        
        if self.radioButton_extentLayer.isChecked():
            self.comboBox_extentLayer.setDisabled(False)
            #self.pushButton_refreshLayers.setDisabled(False)
        else:
            self.comboBox_extentLayer.setDisabled(True)
            self.pushButton_refreshLayers.setDisabled(True)

    def runQuery(self):
        '''
        Process for running the query
        '''
        #Block the button and save the initial text
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.pushButton_browse_output_file.setDisabled(True)
        self.pushButton_showQuery.setDisabled(True)
        self.startProcess()
        QApplication.processEvents()
        
        #Get all values
        key = unicode(self.lineEdit_key.text())
        value = unicode(self.lineEdit_value.text())
        nominatim = unicode(self.lineEdit_nominatim.text())
        timeout = self.spinBox_timeout.value()
        outputDir = self.lineEdit_browseDir.text()
        prefixFile = self.lineEdit_filePrefix.text()
        
        #Which geometry at the end ?
        outputGeomTypes = self.getOutputGeomTypes()
        
        #Which osm's objects ?
        osmObjects = []
        if self.checkBox_node.isChecked():
            osmObjects.append('node')
        if self.checkBox_way.isChecked():
            osmObjects.append('way')
        if self.checkBox_relation.isChecked():
            osmObjects.append('relation')
        
        try:
            #Test values
            if not osmObjects:
                raise OsmObjectsException
            
            if not outputGeomTypes:
                raise OutPutGeomTypesException
            
            #If bbox, we must set None to nominatim, we can't have both
            bbox = None
            if self.radioButton_extentLayer.isChecked() or self.radioButton_extentMapCanvas.isChecked():
                nominatim = None
                bbox = self.getBBox()
            
            if nominatim == '':
                nominatim = None
            
            if outputDir and not os.path.isdir(outputDir):
                raise DirectoryOutPutException

            numLayers = Process.ProcessQuickQuery(dialog = self, key=key, value=value, nominatim=nominatim, bbox=bbox, osmObjects=osmObjects, timeout=timeout, outputDir=outputDir, prefixFile=prefixFile,outputGeomTypes=outputGeomTypes)
            if numLayers:
                self.label_progress.setText(QApplication.translate("QuickOSM",u"Successful query !"))
                iface.messageBar().pushMessage(QApplication.translate("QuickOSM",u"Successful query !"), level=QgsMessageBar.INFO , duration=5)
            else:
                self.label_progress.setText(QApplication.translate("QuickOSM",u"No result"))
                iface.messageBar().pushMessage(QApplication.translate("QuickOSM", u"Successful query, but no result."), level=QgsMessageBar.WARNING , duration=7)
        
        except GeoAlgorithmExecutionException,e:
            self.displayGeoAlgorithmException(e)
        except Exception,e:
            self.displayException(e)
        
        finally:
            #Resetting the button
            self.pushButton_browse_output_file.setDisabled(False)
            self.pushButton_showQuery.setDisabled(False)
            QApplication.restoreOverrideCursor()
            self.endProcess()
            QApplication.processEvents()
            
    def showQuery(self):
        '''
        Show the query in the main window
        '''
        #We have to find the widget in the stackedwidget of the main window
        queryWidget = None
        indexQuickQueryWidget = None
        for i in xrange(iface.QuickOSM_mainWindowDialog.stackedWidget.count()):
            if iface.QuickOSM_mainWindowDialog.stackedWidget.widget(i).__class__.__name__ == "QueryWidget":
                queryWidget = iface.QuickOSM_mainWindowDialog.stackedWidget.widget(i)
                indexQuickQueryWidget = i
                break
        
        #Get all values
        key = unicode(self.lineEdit_key.text())
        value = unicode(self.lineEdit_value.text())
        nominatim = unicode(self.lineEdit_nominatim.text())
        timeout = self.spinBox_timeout.value()
        outputDir = self.lineEdit_browseDir.text()
        prefixFile = self.lineEdit_filePrefix.text()
        
        #If bbox, we must set None to nominatim, we can't have both
        bbox = None
        if self.radioButton_extentLayer.isChecked() or self.radioButton_extentMapCanvas.isChecked():
            nominatim = None
            bbox = True
        
        if nominatim == '':
            nominatim = None
        
        #Which osm's objects ?
        osmObjects = []
        if self.checkBox_node.isChecked():
            osmObjects.append('node')
        if self.checkBox_way.isChecked():
            osmObjects.append('way')
        if self.checkBox_relation.isChecked():
            osmObjects.append('relation')
            
        #Which geometry at the end ?
        queryWidget.checkBox_points.setChecked(self.checkBox_points.isChecked())
        queryWidget.checkBox_lines.setChecked(self.checkBox_lines.isChecked())
        queryWidget.checkBox_multilinestrings.setChecked(self.checkBox_multilinestrings.isChecked())
        queryWidget.checkBox_multipolygons.setChecked(self.checkBox_multipolygons.isChecked())
        
        queryWidget.radioButton_extentLayer.setChecked(self.radioButton_extentLayer.isChecked())
        queryWidget.radioButton_extentMapCanvas.setChecked(self.radioButton_extentMapCanvas.isChecked())
        
        #Transfer the combobox from QuickQuery to Query
        if self.comboBox_extentLayer.count():
            queryWidget.radioButton_extentLayer.setCheckable(True)
        queryWidget.comboBox_extentLayer.setModel(self.comboBox_extentLayer.model())
        
        #Transfer the output
        queryWidget.lineEdit_browseDir.setText(outputDir)
        if prefixFile:
            queryWidget.lineEdit_filePrefix.setText(prefixFile)
            queryWidget.lineEdit_filePrefix.setEnabled(True)

        #Make the query
        queryFactory = QueryFactory(timeout=timeout,key=key,value=value,bbox=bbox,nominatim=nominatim,osmObjects=osmObjects)
        query = queryFactory.make()
        queryWidget.textEdit_query.setPlainText(query)
        iface.QuickOSM_mainWindowDialog.listWidget.setCurrentRow(indexQuickQueryWidget)
        iface.QuickOSM_mainWindowDialog.exec_()

class QuickQueryDockWidget(QDockWidget):
    def __init__(self, parent=None):
        QDockWidget.__init__(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.widget = QuickQueryWidget()
        self.setWidget(self.widget)
        self.setWindowTitle(QApplication.translate("ui_quick_query", "QuickOSM - Quick query"))