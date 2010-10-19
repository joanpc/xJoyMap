"""
PI_xJoyMap

Pre-lease

Pretends to simplify modifying datarefs with your joystick and creating advanced joy commands
Needs a axis.ini conf files in the plugin folder or an optional axis.ini in the aircraft folders.

It doesn't check the config parameters so bad parameters will hang the plugin and maybe x-plane

Please feel free to post your patches or bugs at http://github.com/joanpc/xJoyMap

Copyright (C) 2010  Joan Perez i Cauhe
---
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
---
"""
from XPLMUtilities import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMPlanes import *
from XPLMPlugin import *
import ConfigParser
from os import path


"""
Some constants
"""
CMD_PREFIX = 'sim/xjoymap/'	#prefix for the new commands
CONF_FILENAME = 'xjoymap.ini'
ACF_CONF_FILENAME = '.xjm'
X737_CHECK_FILE = '_x737pluginVersion.txt'
X737_INITIALIZED_MESSAGE = -2004318080
#X737_UNLOADED_MESSAGE = -2004318065

"""
JoyAxisAssign

Assigns a joystick axis to a dataref value.

axis: joy axis #
dataref: Dataref string
dr_range: range of the dataref ex: 3 = 0 to 3: -3 = 30 
dr_type: int or float
release: soft release range to retake control if the value is changed externally 
		 usually by the autopilot.
dr_round: Rounding done at the dataref, sometimes after setting a dataref value
		  the value is rounded by the sim. Without this setting the class will 
		  detect the rounding as an autopilot action. (ex: 100 for vertical_velocity)
		  
http://www.xsquawkbox.net/xpsdk/docs/DataRefs.html list of datarefs
"""
class JoyAxisAssign:
	def __init__(self, axis, dataref, dr_range, dr_type = int, release = 1, dr_round = 0):
		self.axis = int(axis)
		self.dr_value = XPLMFindDataRef(dataref)
		self.dr_range = int(dr_range)
		self.dr_type = dr_type
		self.release = int(release)
		if (self.dr_range < 0): # Enable negative ranges
			self.negative = True
			self.dr_range = self.dr_range * -1
		else: self.negative = False
		self.dr_round = int(dr_round)
		self.old_joy_value = -1
		self.old_dr_value = -1
		
		if (dr_type == "int"):
			self.get_dr = XPLMGetDatai
			self.set_dr = XPLMSetDatai
		elif (dr_type == "float"):
			self.get_dr = XPLMGetDataf
			self.set_dr = XPLMSetDataf	

	def XPluginStart(self):
		self.Name = "Joy Axis Assign Class"
		self.Sig = "JoyAxisAssignClass-v100.joanpc.PI"
		self.Desc = "Joy Axis Assign Class"
		return self.Name, self.Sig, self.Desc	

	def get_current_joy(self, axis_value):
		if (self.negative):
			current = axis_value * self.dr_range * 2 - self.dr_range
		else:
			current = axis_value * self.dr_range
		if (self.dr_type == "int"): return int(current)
		else: return current

	# called from the main flightloop
	def updateLoop(self, axis):

		current_joy_value = self.get_current_joy(axis[self.axis])
		current_dr_value = self.get_dr(self.dr_value)
	
		if (self.old_dr_value == -1):
			self.old_joy_value = current_joy_value
			self.old_dr_value = current_joy_value
		
		if (current_joy_value == self.old_joy_value):
			# No joy changes
			return 0
		elif (current_joy_value != current_dr_value):
			# new joy values
			if not (current_dr_value + self.dr_round >= self.old_dr_value >= current_dr_value - self.dr_round):
				# Something changed the values update if in release range
				if (current_joy_value +  self.release > current_dr_value > current_joy_value - self.release):
					#print "Values in range"
					self.set_dr(self.dr_value, current_joy_value)
				else: return 1
			else:
				# "No autopilot changes"
				self.set_dr(self.dr_value, current_joy_value)
		
		# Save values
		self.old_joy_value = current_joy_value
		self.old_dr_value = self.get_dr(self.dr_value)
		return 1
	
	def XPluginStop(self):
		pass
	def XPluginEnable(self):
		return 1
	def XPluginDisable(self):
		pass
	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

"""
JoyButtonAlias
Registers button assignments

parent: parent class defining the shift status
newCommand: New command to register
mainCommand: Default command to execute
shiftCommand: Alternate command executed on parent.shift == True
mainDescription: New command description
"""
class JoyButtonAlias:
	def XPluginStart(self):
		self.Name = "Joys overrides"
		self.Sig = "JoyButtonAssingsClass-v100.joan.PI"
		self.Desc = "Shifted and combo joy commands"
		return self.Name, self.Sig, self.Desc
	
	def __init__(self, parent, newCommand, mainCommand, shiftCommand = False, mainDescription = ""):
		
		self.mainCMD = []
		for cmd in mainCommand.split(','): self.mainCMD.append(XPLMFindCommand(cmd.strip()))
		if (shiftCommand):
			self.shiftCMD = []
			for cmd in shiftCommand.split(','): self.shiftCMD.append(XPLMFindCommand(cmd.strip()))
		else:  self.shiftCMD = self.mainCMD
		self.parent = parent
		
		self.newCMD = XPLMCreateCommand(CMD_PREFIX + newCommand, mainDescription)
		self.newCH = self.newCommandHandler
		XPLMRegisterCommandHandler(self, self.newCMD, self.newCH, 0, 0)
	
	def XPluginStop(self):
		pass
	def XPluginEnable(self):
		return 1
	def XPluginDisable(self):
		pass
	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
	def newCommandHandler(self, inCommand, inPhase, inRefcon):
		if (inPhase == 0):
			for cmd in self.getCommand(self.parent.shift): XPLMCommandBegin(cmd)
		elif (inPhase == 2):
			for cmd in self.getCommand(self.parent.shift): XPLMCommandEnd(cmd)
		return 0
	def getCommand(self, shift): #returns the command array for the appropriate shift status
		if (shift):
			return self.shiftCMD
		else:
			return self.mainCMD
	def destroy(self):
		XPLMUnregisterCommandHandler(self, self.newCMD, self.newCH, 0, 0)
		pass
"""
JoyButtonDataref

Assigns a button to a dataref

command: New command
dataref: Dataref to interact with
values: values to toggle
increment: increment steep

"""
class JoyButtonDataref:
	def __init__(self, command, dataref, type ='int', values = False, increment = False, description = ''):
		self.values = []
		if (increment != False): 
			self.action = self.incremental
			self.increment = int(increment)
			self.mode = 'incremental'
		else: 
			self.action = self.toggle
			self.increment = 1
			if (values): 
				nvalues = []
				for value in values.split(','):
					nvalues.append(int(value.strip()))
				self.values = nvalues
				self.valuesi = 0
				self.valuesl = len(self.values) - 1
				self.mode = 'toggle'
		if (type == 'int'):
			self.getdataref = XPLMGetDatai
			self.setdataref = XPLMSetDatai
		else:
			self.getdataref = XPLMGetDataf
			self.setdataref = XPLMSetDataf
		
		self.dataref = XPLMFindDataRef(dataref)
		# register new command
		self.command = XPLMCreateCommand(CMD_PREFIX + command, description)
		self.newCH = self.CommandHandler
		XPLMRegisterCommandHandler(self, self.command, self.newCH, 0, False)
		# If more than 2 toggle values or in incremental mode register a x_down command
		#if(len(self.values) > 2 or self.mode == 'incremental'):
		#self.command_down = XPLMCreateCommand(CMD_PREFIX + command + '_down', description)
		#self.newCH_down = self.CommandHandler_down
		#XPLMRegisterCommandHandler(self, self.command_down, self.newCH_down, 0, 0)
		pass

	def CommandHandler(self, inCommand, inPhase, inRefcon):
		if (inPhase == 0): self.action(self.increment)
		return 0
	def CommandHandler_down(self, inCommand, inPhase, inRefcon):
		if (inPhase == 0): self.action(self.increment * -1)
		return 0
	def incremental(self, increment):
		self.setdataref(self.dataref, self.getdataref(self.dataref) + increment)
		pass
	def toggle(self, increment):
		self.valuesi += increment
		if (self.valuesi > self.valuesl): self.valuesi = 0
		if (self.valuesi < 0): self.valuesi = self.valuesl
		self.setdataref(self.dataref, self.values[self.valuesi])
		pass	
	def destroy(self):
		# BUG: Unregistering commands sometimes disables reenabling them
		XPLMUnregisterCommandHandler(self, self.command , self.newCH, 0, 0)
		#if ((len(self.values) > 2 or self.mode == 'incremental')): 
		#XPLMUnregisterCommandHandler(self, self.command_down, self.newCH_down, 0, 0)
		pass

	def XPluginStop(self):
		pass
	def XPluginEnable(self):
		return 1
	def XPluginDisable(self):
		pass
	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
	def XPluginStart(self):
		self.Name = "JoyButtonDataref"
		self.Sig = "JoyButtonDatarefClass-v100.joan.PI"
		self.Desc = "Modifies datarefs with joy buttons"
		return self.Name, self.Sig, self.Desc

"""
Main plugin
"""
class PythonInterface:
	def XPluginStart(self):
		self.Name = "X-plane Joy Map tool"
		self.Sig = "xJoyMap-v100.joanpc.PI"
		self.Desc = "Provides advanced joy mapping features"
		self.axis, self.buttons, self.buttonsdr =  [], [], []
		self.shift = 0
		
		self.sys_path = ""
		self.sys_path = XPLMGetSystemPath(self.sys_path)
		
		self.shiftcommand = XPLMCreateCommand(CMD_PREFIX + "shift", "Shift button")
		self.shiftCH = self.shiftHandler
		XPLMRegisterCommandHandler(self, self.shiftcommand, self.shiftCH, 0, 0)
		
		# Datarefs
		self.axis_values_dr = XPLMFindDataRef("sim/joystick/joystick_axis_values")

		# Main floop
		self.floop = self.floopCallback
		XPLMRegisterFlightLoopCallback(self, self.floop, 0, 0)
		
		self.config()
		return self.Name, self.Sig, self.Desc

	def config(self):
		# Defaults
		defaults = {'type':"int", 'release':1, 'negative': 0, 'shift': 0, 'round': 0, 'shifted_command': False, \
					'values': False, 'increment' : False, 'description': ''}
		# Plane config
		plane, plane_path = XPLMGetNthAircraftModel(0)
		
		config = ConfigParser.RawConfigParser()
		alias_commands=[]
		
		# Check for config files
		if (not config.read(plane_path[:-4] + ACF_CONF_FILENAME)):
			if (not config.read(plane_path[:-len(plane)] + CONF_FILENAME)):
				config.read(self.sys_path + 'Resources/plugins/PythonScripts/' + CONF_FILENAME)

		for section in config.sections():
			conf = dict(defaults)
			for item in config.items(section):
				conf[item[0]] = item[1]
			"""
			Add new classes here
			TODO: This code will be rewritten maybe each class should check their parameters..
			"""	
			# JoyAxis Assignments
			if  ('axis' in conf and 'dataref' in conf and 'range' in conf):
				self.axis.append(JoyAxisAssign(int(conf['axis']), \
				conf['dataref'], conf['range'], conf['type'], conf['release'], \
				conf['round']))
			# JoyButtonDataref
			elif('new_command' in conf and 'dataref' in conf):
				self.buttonsdr.append(JoyButtonDataref(conf['new_command'], conf['dataref'], conf['type'],\
				conf['values'], int(conf['increment']), section))
			elif ('new_command' in conf and 'main_command' in conf):
				alias_commands.append(conf) # store alias
		# Alias should be defined at the end
		for conf in alias_commands:
			self.buttons.append(JoyButtonAlias(self, conf['new_command'], conf['main_command'], \
			conf['shifted_command'], section))
			
		# Reenable flightloop if we have axis defined	
		if (len(self.axis)): XPLMSetFlightLoopCallbackInterval(self.floop, -1, 0, 0)
			
	"""
	Clears all the assignments and disables de flightloop
	"""
	def clearConfig(self):
		# Disable flightloop
		XPLMSetFlightLoopCallbackInterval(self.floop, 0, 0, 0)
		# Destroy commands
		for command in self.buttons: command.destroy()
		for command in self.buttonsdr: command.destroy()
		# and buttons
		self.buttons, self.buttonsdr, self.axis = [], [], []
		
	"""
	Defines the shift status
	"""
	def shiftHandler(self, inCommand, inPhase, inRefcon):
		if (inPhase == 0):
			self.shift = 1
		elif (inPhase == 2):
			self.shift = 0
		return 0

	"""
	Main flight loop: calls axis classes .updateloop
	"""
	def floopCallback(self, elapsedMe, elapsedSim, counter, refcon):
		# Get all axis
		axis_values = []
		XPLMGetDatavf(self.axis_values_dr, axis_values , 0 ,100)		
		for axis_assign in self.axis:
			axis_assign.updateLoop(axis_values)
		return -1

	def XPluginStop(self):
		self.clearConfig()
		XPLMUnregisterFlightLoopCallback(self, self.floop, 0)
		XPLMRegisterCommandHandler(self, self.shiftcommand, self.shiftCH, 0, 0)
		pass
	def XPluginEnable(self):
		return 1
	def XPluginDisable(self):
		pass
	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		"""
		Detects aircraft changes and reloads the config
		"""
		if (inMessage == 102 and inParam == 0): # On aircraft change
			plane, path = XPLMGetNthAircraftModel(0)
			"""
			TODO: Detect x737 by X737_CHECK_FILE
			"""
			#if(path.lexists(path[ :-len(plane)] + X737_CHECK_FILE)):
			if (plane == '737.acf'): # if x737 clear config and wait for x737 plugin
				self.clearConfig()
				return 1
			# Reload Config
			self.clearConfig()	
			self.config()
		""" 
		TODO: that's an ugly fix to reload config if the x737 plugin is enabled
		Copy pasted from the x737 joy plugin
		"""
		X737_ID = XPLMFindPluginBySignature('bs.x737.plugin')
		if (inFromWho == X737_ID):
			if (inMessage == X737_INITIALIZED_MESSAGE):
				print "x737 initiated, reloading config"
				self.config()
		pass