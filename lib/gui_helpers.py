import os
import datetime

from PyQt4 import QtGui, QtCore, Qt
from PyQt4.QtCore import pyqtSignal

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np

from andor_helpers import *

layout_params = {
	'main': [1000, 800],
	'image': [700,500],
	'figure': [6, 6]
}

# Config form for user input for setting up acquisition parameters
class ConfigForm(QtGui.QWidget):
	# Initialize
	def __init__(self, Parent=None):
		super(ConfigForm, self).__init__(Parent)
		# Populate form widgets
		self.populate()
		# Set default values for config form entries
		self.setDefaultValues()

	# These default parameters are set in the default_config dict in andor_helpers.py
	def setDefaultValues(self):
		self.exposureEdit.setText(default_config['exposure'])

		self.xOffsetEdit.setText(default_config['xOffset'])
		self.yOffsetEdit.setText(default_config['yOffset'])

		self.dxEdit.setText(default_config['dx'])
		self.dyEdit.setText(default_config['dy'])

		self.binningControl.setChecked(default_config['binning'])

		self.emGainEdit.setText(default_config['emGain'])
		self.emEnableControl.setChecked(default_config['emEnable'])
		self.emGainToggle()

		# Default save path is built off of the default_config save path
		# plus the current date
		now = datetime.datetime.now()
		savedir = now.strftime(default_config['savePath'] + '%Y%m%d\\')
		self.savePathEdit.setText(savedir)

		# Check directory
		# If directory doesn't exist, make it
		# If directory does exist, automatically set the file number to be 1 greater than
		# the last file in the directory
		self.checkDir()

		# Try to initialize the combo boxes to the right value
		try:
			self.adChannelControl.setCurrentIndex(default_config['adChannel'])
			self.controlHSSOptions()

			self.hssControl.setCurrentIndex(default_config['hss'])
			self.preAmpGainControl.setCurrentIndex(default_config['preAmpGain'])

			self.vssControl.setCurrentIndex(default_config['vss'])
		# Hit exception if communication with camera isn't setup yet
		except Exception as e:
			pass

	# Check save directory and file number
	# using path defined in the save path field
	def checkDir(self):
		fileNumber = 0
		savedir = str(self.savePathEdit.text())

		# Check if the directory exists
		if os.path.isdir(savedir):
			filelist = os.listdir(savedir)
			for file in filelist:
				# Extract the file number
				# Files are saved as KRBCAM_FILENAME_BASE + filenumber + kinetics index + .csv
				# where kinetics index is a, b, etc. to number the images in the kinetics series
				# e.g., a possible file number is iXon_img10a.csv
				ind1 = len(KRBCAM_FILENAME_BASE)
				ind2 = file.find('.csv') - 1 # minus 1 to get rid of kinetics index
				
				# Compare file number, if it's bigger than set fileNumber to 1 greater than that
				try:
					substr = file[ind1:ind2]
					num = int(substr)
					if num >= fileNumber:
						fileNumber = num + 1
				except:
					pass
		# If not, make the directory
		else:
			os.makedirs(savedir)
		# Update the file number field of the config form
		self.fileNumberEdit.setText(str(fileNumber))

	# Setup Combo Boxes
	# The items are dependent on the camera capabilities
	def setupComboBoxes(self, config):
		# Get the camera info
		self.hss = config['hss']
		self.hssPA = config['hssPreAmp']
		self.pa = config['preAmpGain']
		self.nADC = config['adChannels']

		# Populate AD Channels
		for i in range(self.nADC):
			self.adChannelControl.addItem(str(i))

		# Populate horizontal shift speeds
		self.controlHSSOptions()

		# Populate vertical shift speeds
		for val in config['vss']:
			self.vssControl.addItem("{:.2} usec".format(val))

	# Setup horizontal shift speed options
	# The items are dependent on the camera capabilities
	def controlHSSOptions(self):
		# Clear combo box
		self.hssControl.clear()

		# Need to know whether we are in EM mode
		if self.emEnableControl.isChecked():
			typ = 0
		else:
			typ = 1

		# Need AD channel
		adc = int(self.adChannelControl.currentIndex())

		# Populate the box
		for val in self.hss[adc][typ]:
			self.hssControl.addItem("{:.1f} MHz".format(val))

		# Populate the pre amp options
		self.controlPAOptions()

	# Setup pre amplifier options
	# The items are dependent on the camera capabilities
	def controlPAOptions(self):
		# Clear the combo box
		self.preAmpGainControl.clear()

		# Need to know whether we are in EM mode
		if self.emEnableControl.isChecked():
			typ = 0
		else:
			typ = 1

		# Get current AD channel and current HSS
		adc = int(self.adChannelControl.currentIndex())
		hss = int(self.hssControl.currentIndex())

		# Populate box, only counting pre amp controls that are available
		# for this HSS
		for i in range(len(self.pa)):
			if self.hssPA[adc][typ][hss][i]:
				self.preAmpGainControl.addItem(str(self.pa[i]))

	# Returns the form data
	# If any field has an invalid format, the default values are reset
	def getFormData(self):
		self.checkDir()
		try:
			form = {}
			form['expTime'] = float(self.exposureEdit.text())
			form['xOffset'] = int(self.xOffsetEdit.text())
			form['yOffset'] = int(self.yOffsetEdit.text())
			form['dx'] = int(self.dxEdit.text())
			form['dy'] = int(self.dyEdit.text())
			form['binning'] = bool(self.binningControl.isChecked())
			form['emEnable'] = bool(self.emEnableControl.isChecked())
			form['emGain'] = int(self.emGainEdit.text())
			form['fileNumber'] = int(self.fileNumberEdit.text())
			form['savePath'] = str(self.savePathEdit.text())
			form['vss'] = self.vssControl.currentIndex()
			form['adChannel'] = self.adChannelControl.currentIndex()
			form['hss'] = self.hssControl.currentIndex()
			form['preAmpGain'] = self.preAmpGainControl.currentIndex()
			return form
		except:
			self.throwErrorMessage("Invalid form data!", "Try again.")
			self.setDefaultValues()
			return self.getFormData()

	# Takes form as an input dict (should have same keys as gConfig in the main GUI)
	# and populates the form fields with these
	def setFormData(self, form):
		self.exposureEdit.setText(str(form['expTime']))
		self.xOffsetEdit.setText(str(form['xOffset']))
		self.yOffsetEdit.setText(str(form['yOffset']))
		self.dxEdit.setText(str(form['dx']))
		self.dyEdit.setText(str(form['dy']))
		self.binningControl.setChecked(bool(form['binning']))
		self.emEnableControl.setChecked(bool(form['emEnable']))
		self.emGainEdit.setText(str(form['emGain']))
		self.fileNumberEdit.setText(str(form['fileNumber']))
		self.savePathEdit.setText(form['savePath'])

	# If the EM enable box is checked, then enable the EM gain field
	# Otherwise, disable the EM gain field
	def emGainToggle(self):
		try:
			if self.emEnableControl.isChecked():
				self.emGainEdit.setDisabled(False)
				self.emGainEdit.setText("1")
			else:
				self.emGainEdit.setText("0")
				self.emGainEdit.setDisabled(True)
				self.emGainEdit.setStyleSheet("color: rgb(0,0,0);")
		except:
			self.emGainEdit.setText("0")
			self.emGainEdit.setDisabled(True)
			self.emGainEdit.setStyleSheet("color: rgb(0,0,0);")

	# Populate the form with widgets
	def populate(self):
		self.acquireStatic = QtGui.QLabel("Acquire Mode", self)
		self.acquireEdit = QtGui.QLineEdit(self)
		self.acquireEdit.setText("Fast Kinetics")
		self.acquireEdit.setDisabled(True)
		self.acquireEdit.setStyleSheet("color: rgb(0,0,0);")

		self.triggerStatic = QtGui.QLabel("Trigger Mode", self)
		self.triggerEdit = QtGui.QLineEdit(self)

		if KRBCAM_TRIGGER_MODE == 0:
			self.triggerEdit.setText("Internal")
		else:
			self.triggerEdit.setText("External")
		self.triggerEdit.setDisabled(True)
		self.triggerEdit.setStyleSheet("color: rgb(0,0,0);")

		self.exposureStatic = QtGui.QLabel("Exposure (ms)", self)
		self.exposureEdit = QtGui.QLineEdit(self)

		self.emGainStatic = QtGui.QLabel("EM Gain", self)
		self.emGainEdit = QtGui.QLineEdit(self)

		self.emEnableStatic = QtGui.QLabel("EM Enable?", self)
		self.emEnableControl = QtGui.QCheckBox(self)
		self.emEnableControl.stateChanged.connect(self.emGainToggle)
		self.emEnableControl.stateChanged.connect(self.controlHSSOptions)

		self.adChannelStatic = QtGui.QLabel("AD Channel", self)
		self.adChannelControl = QtGui.QComboBox(self)
		self.adChannelControl.currentIndexChanged.connect(self.controlHSSOptions)

		self.hssStatic = QtGui.QLabel("HS Speed", self)
		self.hssControl = QtGui.QComboBox(self)
		self.hssControl.currentIndexChanged.connect(self.controlPAOptions)

		self.preAmpGainStatic = QtGui.QLabel("Pre-Amp Gain", self)
		self.preAmpGainControl = QtGui.QComboBox(self)

		self.xOffsetStatic = QtGui.QLabel("X Offset (px)", self)
		self.xOffsetEdit = QtGui.QLineEdit(self)
		
		self.yOffsetStatic = QtGui.QLabel("Y Offset (px)", self)
		self.yOffsetEdit = QtGui.QLineEdit(self)
		
		self.dxStatic = QtGui.QLabel("Width dx (px)", self)
		self.dxEdit = QtGui.QLineEdit(self)
		
		self.dyStatic = QtGui.QLabel("Height dy (px)", self)
		self.dyEdit = QtGui.QLineEdit(self)

		self.binningStatic = QtGui.QLabel("Bin 2x2?", self)
		self.binningControl = QtGui.QCheckBox(self)

		self.vssStatic = QtGui.QLabel("FKVS Speed", self)
		self.vssControl = QtGui.QComboBox(self)

		self.savePathStatic = QtGui.QLabel("Save to:", self)
		self.savePathEdit = QtGui.QLineEdit(self)

		self.fileNumberStatic = QtGui.QLabel("File number:", self)
		self.fileNumberEdit = QtGui.QLineEdit(self)
		
		self.layout = QtGui.QGridLayout()

		row = 1
		self.layout.addWidget(self.acquireStatic, row, 0)
		self.layout.addWidget(self.acquireEdit, row, 1)
		row += 1

		self.layout.addWidget(self.triggerStatic, row, 0)
		self.layout.addWidget(self.triggerEdit, row, 1)
		row += 1

		self.layout.addWidget(self.exposureStatic, row, 0)
		self.layout.addWidget(self.exposureEdit, row, 1)
		row += 1

		self.layout.addWidget(self.emEnableStatic, row, 0)
		self.layout.addWidget(self.emEnableControl, row, 1)
		row += 1

		self.layout.addWidget(self.emGainStatic, row, 0)
		self.layout.addWidget(self.emGainEdit, row, 1)
		row += 1

		self.layout.addWidget(self.adChannelStatic, row, 0)
		self.layout.addWidget(self.adChannelControl, row, 1)
		row += 1

		self.layout.addWidget(self.hssStatic, row, 0)
		self.layout.addWidget(self.hssControl, row, 1)
		row += 1

		self.layout.addWidget(self.preAmpGainStatic, row, 0)
		self.layout.addWidget(self.preAmpGainControl, row, 1)
		row += 1

		self.layout.addWidget(QtGui.QLabel(""), row, 0)
		row += 1

		self.layout.addWidget(self.xOffsetStatic, row, 0)
		self.layout.addWidget(self.xOffsetEdit, row, 1)
		row += 1

		self.layout.addWidget(self.yOffsetStatic, row, 0)
		self.layout.addWidget(self.yOffsetEdit, row, 1)
		row += 1

		self.layout.addWidget(self.dxStatic, row, 0)
		self.layout.addWidget(self.dxEdit, row, 1)
		row += 1

		self.layout.addWidget(self.dyStatic, row, 0)
		self.layout.addWidget(self.dyEdit, row, 1)
		row += 1

		self.layout.addWidget(self.binningStatic, row, 0)
		self.layout.addWidget(self.binningControl, row, 1)
		row += 1

		self.layout.addWidget(self.vssStatic, row, 0)
		self.layout.addWidget(self.vssControl, row, 1)
		row += 1

		self.layout.addWidget(QtGui.QLabel(""), row, 0)
		row += 1

		self.layout.addWidget(self.savePathStatic, row, 0)
		self.layout.addWidget(self.savePathEdit, row, 1)
		row += 1

		self.layout.addWidget(self.fileNumberStatic, row, 0)
		self.layout.addWidget(self.fileNumberEdit, row, 1)

		self.setLayout(self.layout)

	# Convenient function for throwing error messages
	def throwErrorMessage(self, header, msg):
		messageBox = QtGui.QMessageBox()
		messageBox.setText(header)
		messageBox.setInformativeText(msg)
		messageBox.exec_()


# Acquire button, abort button, status log
class AcquireAbortStatus(QtGui.QWidget):

	def __init__(self, Parent=None):
		super(AcquireAbortStatus, self).__init__(Parent)
		self.populate()
		self.setDefaultValues()

	# Set default values
	def setDefaultValues(self):
		self.acquireControl.setDisabled(False)
		self.abortControl.setDisabled(True)
		self.statusEdit.setText("Python GUI initialized.\n")

	# Enable abort, disable acquire
	def acquire(self):
		self.acquireControl.setDisabled(True)
		self.abortControl.setDisabled(False)

	# Enable acquire, disable abort
	def abort(self):
		self.abortControl.setDisabled(True)
		self.acquireControl.setDisabled(False)

	# Populate the GUI
	def populate(self):
		self.layout = QtGui.QVBoxLayout()

		self.acquireControl = QtGui.QPushButton("Update parameters and acquire")
		self.abortControl = QtGui.QPushButton("Stop acquiring")

		self.statusStatic = QtGui.QLabel("Status log:")
		self.statusEdit = QtGui.QTextEdit()
		self.statusEdit.setReadOnly(True)
		self.statusEdit.setStyleSheet("color: rgb(0,0,0);")

		self.layout.addWidget(self.acquireControl)
		self.layout.addWidget(self.abortControl)
		self.layout.addWidget(self.statusStatic)
		self.layout.addWidget(self.statusEdit)

		self.setLayout(self.layout)

# Form for inputting and monitoring cooling status and parameters
class CoolerControl(QtGui.QWidget):

	def __init__(self, Parent=None):
		super(CoolerControl, self).__init__(Parent)
		self.populate()
		self.setDefaultValues()

	# Set default values
	def setDefaultValues(self):
		self.coolerOffControl.setChecked(True)
		self.coolerOff()
		self.coolerStatusEdit.setText("Off")
		self.ccdTempRangeEdit.setText("No camera")
		self.ccdCurrentTempEdit.setText("Cooler off")
		self.ccdSetTempEdit.setText(str(KRBCAM_DEFAULT_TEMP))

	# Given the camInfo dict from the main GUI,
	# display the allowed temp range for the camera
	def setTempRange(self, info):
		mintemp = max(info['temperatureRange'][0], KRBCAM_MIN_TEMP)
		maxtemp = min(info['temperatureRange'][1], KRBCAM_MAX_TEMP)

		msg = "{} to {}".format(mintemp, maxtemp)
		self.ccdTempRangeEdit.setText(msg)

	# Disable On button, enable Off button
	def coolerOn(self):
		self.coolerOnControl.setDisabled(True)
		self.coolerOffControl.setDisabled(False)

	# Disable Off button, enable On button
	def coolerOff(self):
		self.coolerOnControl.setDisabled(False)
		self.coolerOffControl.setDisabled(True)

	# Populate the GUI
	def populate(self):
		self.buttonGroup = QtGui.QButtonGroup(self)

		self.coolerOnControl = QtGui.QRadioButton("On", self)
		self.coolerOffControl = QtGui.QRadioButton("Off", self)

		self.coolerOnControl.clicked.connect(self.coolerOn)
		self.coolerOffControl.clicked.connect(self.coolerOff)

		self.buttonGroup.addButton(self.coolerOnControl)
		self.buttonGroup.addButton(self.coolerOffControl)

		self.buttonGroupLabel = QtGui.QLabel("Cooler control:", self)

		self.coolerStatusStatic = QtGui.QLabel("Cooler Status:", self)
		self.coolerStatusEdit = QtGui.QLineEdit(self)
		self.coolerStatusEdit.setDisabled(True)
		self.coolerStatusEdit.setStyleSheet("color: rgb(0,0,0);")

		self.ccdTempRangeStatic = QtGui.QLabel("Temp. Range (C):", self)
		self.ccdTempRangeEdit = QtGui.QLineEdit(self)
		self.ccdTempRangeEdit.setDisabled(True)
		self.ccdTempRangeEdit.setStyleSheet("color: rgb(0,0,0);")

		self.ccdSetTempStatic = QtGui.QLabel("Set Temp. (C):", self)
		self.ccdSetTempEdit = QtGui.QLineEdit(self)

		self.ccdCurrentTempStatic = QtGui.QLabel("CCD Temp. (C):", self)
		self.ccdCurrentTempEdit = QtGui.QLineEdit(self)
		self.ccdCurrentTempEdit.setDisabled(True)
		self.ccdCurrentTempEdit.setStyleSheet("color: rgb(0,0,0);")

		self.layout = QtGui.QGridLayout()

		self.layout.addWidget(self.buttonGroupLabel, 0, 0)
		self.layout.addWidget(self.coolerOnControl, 1, 0)
		self.layout.addWidget(self.coolerOffControl, 1, 1)
		self.layout.addWidget(self.coolerStatusStatic, 2, 0)
		self.layout.addWidget(self.coolerStatusEdit, 2, 1)
		self.layout.addWidget(self.ccdTempRangeStatic, 3, 0)
		self.layout.addWidget(self.ccdTempRangeEdit, 3, 1)
		self.layout.addWidget(self.ccdSetTempStatic, 4, 0)
		self.layout.addWidget(self.ccdSetTempEdit, 4, 1)
		self.layout.addWidget(self.ccdCurrentTempStatic, 5, 0)
		self.layout.addWidget(self.ccdCurrentTempEdit, 5, 1)

		self.setLayout(self.layout)

# Window for displaying images after they are acquired
class ImageWindow(QtGui.QWidget):
	def __init__(self, Parent=None):
		super(ImageWindow, self).__init__(Parent)
		self.setFixedSize(layout_params['image'][0],layout_params['image'][1])
		self.populate()

		# Default od and count limits
		self.odLimits = [[0,3], [0,3]]
		self.countLimits = [[500,2000], [500,2000]]

		# Set default values
		self.setDefaultValues()

	def setDefaultValues(self):
		self.kSelectButton.setChecked(True)
		self.minEdit.setText(str(self.odLimits[0][0]))
		self.maxEdit.setText(str(self.odLimits[0][1]))

	# Populate GUI
	# self.displayData is a listener for any state change of the buttons
	def populate(self):
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)

		self.buttonGroup = QtGui.QButtonGroup(self)
		self.kSelectButton = QtGui.QRadioButton("K", self)
		self.rbSelectButton = QtGui.QRadioButton("Rb", self)
		self.buttonGroup.addButton(self.kSelectButton)
		self.buttonGroup.addButton(self.rbSelectButton)
		self.buttonGroup.buttonClicked.connect(self.displayData)

		self.frameSelect = QtGui.QComboBox(self)
		self.frameSelect.addItem("OD")
		self.frameSelect.addItem("Shadow")
		self.frameSelect.addItem("Light")
		self.frameSelect.addItem("Dark")
		self.frameSelect.currentIndexChanged.connect(self.displayData)

		self.minLabel = QtGui.QLabel("Min", self)
		self.minEdit = QtGui.QLineEdit(self)
		self.maxLabel = QtGui.QLabel("Max", self)
		self.maxEdit = QtGui.QLineEdit(self)

		self.maxEdit.returnPressed.connect(self.validateLimits)
		self.minEdit.returnPressed.connect(self.validateLimits)

		self.layout = QtGui.QGridLayout()
		self.layout.addWidget(self.toolbar,0,0,1,6)
		self.layout.addWidget(self.canvas,1,0,4,6)
		self.layout.addWidget(self.kSelectButton,5,0)
		self.layout.addWidget(self.rbSelectButton,5,1)
		self.layout.addWidget(self.frameSelect,5,2,1,2)
		self.layout.addWidget(self.minLabel,6,0)
		self.layout.addWidget(self.minEdit,6,1)
		self.layout.addWidget(self.maxLabel,6,2)
		self.layout.addWidget(self.maxEdit,6,3)

		self.setLayout(self.layout)

	# Display the data!
	def displayData(self):
		# Take the button states and determine what image the user wants to see
		(fk, od) = self.getConfig()

		# Then try to plot the image
		try:

			# Get the correct colorbar limits
			if od == 0:
				lims = self.odLimits[fk]
			else:
				lims = self.countLimits[fk]

			# Update the text boxes
			self.minEdit.setText(str(lims[0]))
			self.maxEdit.setText(str(lims[1]))

			# Plot the image
			self.plot(self.data[fk][od], lims[0], lims[1])
			
		# AttributeError will occur if no data collected, since
		# then self.data is undefined
		except Exception as e:
			print e

	def setData(self, data):
		self.data = self.processData(data)

	# Validate the entered values in the min and max boxes
	def validateLimits(self):
		# Try to cast to int
		try:
			max_entry = int(float(self.maxEdit.text()))
			min_entry = int(float(self.minEdit.text()))

			# Update our od limits or count limits
			(fk, od) = self.getConfig()
			if od == 0:
				self.odLimits[fk] = [min(min_entry, max_entry), max(min_entry, max_entry)]
			else:
				self.countLimits[fk] = [min(min_entry, max_entry), max(min_entry, max_entry)]

			# Update the image shown on the screen
			self.displayData()
		except:
			msgBox = QtGui.QMessageBox()
			msgBox.setText("Invalid entry for image display limits.")
			msgBox.setInformativeText("Please check entry (must be integer).")
			msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
			msgBox.exec_()

		
	# Determine which image to display
	def getConfig(self):
		if self.kSelectButton.isChecked():
			fk = 0
		else:
			fk = 1
		od = self.frameSelect.currentIndex()
		if od == -1:
			od = 0
		return (fk, od)

	# Separate images, get OD image
	def processData(self, data):
		out = []

		# Separate kinetic series, od series
		for i in range(KRBCAM_FK_SERIES_LENGTH):
			arr = data[i]
			od_series = []
			
			num_images = KRBCAM_OD_SERIES_LENGTH
			(length, x) = np.shape(arr)
			length = length / num_images

			# Separate OD series			
			for j in range(num_images):
				od_series.append(arr[j*length:(j+1)*length])

			# Calculate OD of the image assuming no saturation
			shadow = od_series[0] - od_series[2]
			background = od_series[1] - od_series[2]
			with np.errstate(divide='ignore', invalid='ignore'):
				od = np.log(background / shadow)

				# Clip off infs and NaNs
				od[od == np.inf] = KRBCAM_OD_MAX
				od[od == -np.inf] = 0
				od = np.where(np.isnan(od), 0, od)

			od_series = [od] + od_series
			out.append(od_series)

		# Return re-arranged data
		# Data is a 2-index array
		# First index runs over kinetic series
		# Second index runs over OD series
		return out

	# Plot the data
	def plot(self, data, vmin, vmax):
		# Clear plot
		self.figure.clear()

		# Plot the data
		ax = self.figure.add_subplot(111)
		im = ax.imshow(data, vmin=vmin, vmax=vmax)

		# Add a horizontal colorbar
		self.figure.colorbar(im, orientation='horizontal')

		# Need to do the following to get the z data to show up in the toolbar
		numrows, numcols = np.shape(data)
		def format_coord(x, y):
		    col = int(x + 0.5)
		    row = int(y + 0.5)
		    if col >= 0 and col < numcols and row >= 0 and row < numrows:
		        z = data[row, col]
		        return '({:},{:}), z={:.2f}'.format(int(x),int(y),z)
		    else:
		        return 'x=%1.4f, y=%1.4f' % (x, y)
		ax.format_coord = format_coord

		# Update the plot
		self.canvas.draw()