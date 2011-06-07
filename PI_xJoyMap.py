"""
PI_xJoyMap

Pretends to simplify modifying datarefs with your joystick and creating advanced joy commands
Needs a xjoymap.ini conf files in the plugin folder and an optional xjoymap.ini or acf_name.xjm in the aircraft folder.

It doesn't check the config parameters so bad parameters will hang the plugin and maybe x-plane (sorry for that)

Many thanks to Sandy Barbour for his X-Plane Python Interface, support, recommendations and fixes.

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
"""
from XPLMDefs import *
from XPLMUtilities import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMPlanes import *
from XPLMPlugin import *
from XPLMMenus import *
import ConfigParser
from os import path
"""
Enables debug messages to help finding problems with config files
levels:
    0    be quiet
    1    config read/clear
    2    loaded sections
    3    Create commands / Get Datarefs

"""
DEBUG=0

"""
Some constants
"""
CMD_PREFIX = 'xjoymap/'    #prefix for new commands
CONF_FILENAME = 'xjoymap.ini'
ACF_CONF_FILENAME = '.xjm'
X737_CHECK_FILE = '_x737pluginVersion.txt'
X737_INITIALIZED_MESSAGE = -2004318080
X737_UNLOADED_MESSAGE = -2004318065
VERSION="1.2.2"
# Execute commands before X-plane
INBEFORE=True
JOY_AXIS = 100 # joy axis to fetch
JOY_BUTTONS = 1520
 
class xjm:
    """
    General utilities
    """
    @classmethod
    def ConstantDataref(self, dataref, value, type = "int"):
        pass
        """
        Assigns a constant dataref
        """
        dr = EasyDref(dataref, type)
        dr.value = dr.cast(value)
        
    @classmethod
    def CheckParams(self, params, conf):
        """
        Check required params in a config section
        """
        for param in params:
            if (not param in conf):
                return False 
        return True
    @classmethod
    def CreateCommand(self, command, description = 'xjoymap command: fill the description field to change this description'):
        """
        returns the command with added prefix if necessary
        """
        command = command.strip()
        xjm.debug("Create command: " + command, 3)
        
        if ('/' not in command):
            command = CMD_PREFIX + 'main/' + command
        elif (command.count('/') < 2) :
            command = CMD_PREFIX + command
        return XPLMCreateCommand(command, description)

    @classmethod
    def debug(self, message, level = 1):
        """
        prints a debug message
        """
        if (DEBUG >= level): print message
        pass
    @classmethod
    def saveAssigments(self, file):
        """
        Saves joy assigments to a file
        """
        f = open(file, 'w')
        joyaxis = EasyDref('sim/joystick/joystick_axis_assignments[0:JOY_AXIS]')
        joybuttons = EasyDref('sim/joystick/joystick_button_assignments[0:JOY_BUTTONS]')
        assigments = {axis: joyaxis.value, buttons: joybuttons.value}
        cpickle.dump(assigments, f)
        f.close()
    @classmethod
    def loadAssigments(self, file):
        """
        Loads joy assigments from a file
        """
        f = open(file, 'r')
        joyaxis = EasyDref('sim/joystick/joystick_axis_assignments[0:JOY_AXIS]')
        joybuttons = EasyDref('sim/joystick/joystick_button_assignments[0:JOY_BUTTONS]')
        assigments = cpickle.load(f)
        joyaxis.value = assigments.axis
        joybuttons.value = assigments.buttons
        f.close()
        

class EasyDref:
    '''
    Easy Dataref access
    
    Copyright (C) 2011  Joan Perez i Cauhe
    '''
    def __init__(self, dataref, type = "int"):
        # Clear dataref
        dataref = dataref.strip()
        self.isarray, dref = False, False
        
        if ('"' in dataref):
            dref = dataref.split('"')[1]
            dataref = dataref[dataref.rfind('"')+1:]
        
        if ('(' in dataref):
            # Detect embedded type, and strip it from dataref
            type = dataref[dataref.find('(')+1:dataref.find(')')]
            dataref = dataref[:dataref.find('(')] + dataref[dataref.find(')')+1:]
        
        if ('[' in dataref):
            # We have an array
            self.isarray = True
            range = dataref[dataref.find('[')+1:dataref.find(']')].split(':')
            dataref = dataref[:dataref.find('[')]
            if (len(range) < 2):
                range.append(range[0])
            
            self.initArrayDref(range[0], range[1], type)
            
        elif (type == "int"):
            self.dr_get = XPLMGetDatai
            self.dr_set = XPLMSetDatai
            self.cast = int
        elif (type == "float"):
            self.dr_get = XPLMGetDataf
            self.dr_set = XPLMSetDataf
            self.cast = float  
        elif (type == "double"):
            self.dr_get = XPLMGetDatad
            self.dr_set = XPLMSetDatad
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        
        if dref: dataref = dref    
        self.DataRef = XPLMFindDataRef(dataref)
        if self.DataRef == False:
            print "Can't find " + dataref + " DataRef"
    
    def initArrayDref(self, first, last, type):
        self.index = int(first)
        self.count = int(last) - int(first) +1
        self.last = int(last)
        
        if (type == "int"):
            self.rget = XPLMGetDatavi
            self.rset = XPLMSetDatavi
            self.cast = int
        elif (type == "float"):
            self.rget = XPLMGetDatavf
            self.rset = XPLMSetDatavf
            self.cast = float  
        elif (type == "bit"):
            self.rget = XPLMGetDatab
            self.rset = XPLMSetDatab
            self.cast = float
        else:
            print "ERROR: invalid DataRef type", type
        pass

    def set(self, value):
        if (self.isarray):
            # set same value to all
            values = []
            for i in range(self.count): values.append(self.cast(value)) 
            self.rset(self.DataRef, values, self.index, self.count)
        else:
            self.dr_set(self.DataRef, self.cast(value))
            
    def get(self):
        if (self.isarray):
            list = []
            # return only the first value
            self.rget(self.DataRef, list, self.index, 1)
            return list[0]
        else:
            return self.dr_get(self.DataRef)
        
    def __getattr__(self, name):
        if name == 'value':
            return self.get()
        else:
            raise AttributeError
    
    def __setattr__(self, name, value):
        if name == 'value':
            self.set(value)
        else:
            self.__dict__[name] = value

 
class JoyAxisAssign:
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
    def __init__(self, plugin, axis, dataref, dr_range, dr_type = "int", release = 1, dr_round = 0):
        self.plugin = plugin
        self.axis = int(axis)
        self.dr_range = int(dr_range)
        self.dr_type = dr_type
        self.release = int(release)
        if (self.dr_range < 0): # Enable negative ranges
            self.negative = True
            self.dr_range = self.dr_range * -1
        else: self.negative = False
        self.dr_round = int(dr_round)
        if (self.dr_round != 0): self.dr_round = self.dr_round / 2
        self.old_joy_value = -1
        self.old_dr_value = -1
        
        self.dataref = EasyDref(dataref, dr_type) 

    def get_current_joy(self, axis_value):
        if (self.negative):
            current = axis_value * self.dr_range * 2 - self.dr_range
        else:
            current = axis_value * self.dr_range
        return self.dataref.cast(current)

    # called from the main flightloop
    def updateLoop(self, axis):

        current_joy_value = self.get_current_joy(axis[self.axis])
        current_dr_value = self.dataref.value
    
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
                    self.dataref.value = current_joy_value
                else: return 1
            else:
                # "No autopilot changes"
                self.dataref.value = current_joy_value
        
        # Save values
        self.old_joy_value = current_joy_value
        self.old_dr_value = self.dataref.value
        return 1

class JoyButtonAlias:
    """
    JoyButtonAlias
    Registers button assignments
    
    parent: parent class defining the shift status
    newCommand: New command to register
    mainCommand: Default command to execute
    shiftCommand: Alternate command executed on parent.shift == True
    mainDescription: New command description
    """
    def __init__(self, plugin, newCommand, mainCommand, shiftCommand = False, mainDescription = "", override = False):
        ## Sandy Barbour - Need to pass in PythonInterface address so that callbacks etc will work from withing a class
        self.plugin = plugin        
        self.mainCMD, self.shiftCMD = [], []
        if (override): self.override = 0
        else: self.override = 1
        
        """
        TODO: Define more shift commands
        """
        for cmd in mainCommand.split(','): 
            # Let define xJoyMap commands without prefix
            if ('/' in  cmd):
                self.mainCMD.append(XPLMFindCommand(cmd.strip()))
            else:
                self.mainCMD.append(XPLMFindCommand(CMD_PREFIX +  cmd.strip()))            
        
        if (shiftCommand):
            for cmd in shiftCommand.split(','): 
                # Let define xJoyMap commands without prefix
                if ('/' in  cmd):
                    self.shiftCMD.append(XPLMFindCommand(cmd.strip()))
                else:
                    self.shiftCMD.append(XPLMFindCommand(CMD_PREFIX +  cmd.strip())) 
        else:  self.shiftCMD = self.mainCMD
        
        self.newCMD = xjm.CreateCommand(newCommand, mainDescription)
        self.newCH = self.newCommandHandler
        
        #print "register:", id(self.plugin), self.newCMD, id(self.newCH)
        XPLMRegisterCommandHandler(self.plugin, self.newCMD, self.newCH, INBEFORE, 0)
    
    def newCommandHandler(self, inCommand, inPhase, inRefcon):
        if (inPhase == 0):
            for cmd in self.getCommand(self.plugin.shift): XPLMCommandBegin(cmd)
        elif (inPhase == 2):
            for cmd in self.getCommand(self.plugin.shift): XPLMCommandEnd(cmd)
        return self.override
    
    def getCommand(self, shift): #returns the command array for the appropriate shift status
        if (shift):
            return self.shiftCMD
        else:
            return self.mainCMD
    def destroy(self):
        #print "destroy", id(self.plugin), self.newCMD, id(self.newCH)
        XPLMUnregisterCommandHandler(self.plugin, self.newCMD, self.newCH, INBEFORE, 0);
        pass

class JoyButtonDataref:
    """
    JoyButtonDataref
    
    Assigns a button to a dataref
    
    command: New command
    dataref: Dataref to interact with
    values: values to toggle
    increment: increment steep
    
    """
    def __init__(self, plugin, command, dataref, type ='int', values = False, increment = False, repeat = False, loop = True ,description = ''):
        self.plugin = plugin
        self.values = []
        self.repeat = repeat
        
        self.dataref = EasyDref(dataref, type)
        
        if (increment != False):
            self.action = self.incremental
            self.increment = self.dataref.cast(increment)
            self.mode = 'incremental'      
            if(self.repeat):
                self.repeatCH = self.RepeatCallback
                XPLMRegisterFlightLoopCallback(self.plugin, self.repeatCH, 0, 0)
        else: 
            if loop:
                self.action = self.toggle_loop
            else:
                self.action = self.toggle  
            self.increment = 1
            if (values): 
                nvalues = []
                for value in values.split(','):
                    nvalues.append(self.dataref.cast(value.strip()))
                self.values = nvalues
                self.valuesi = 0
                self.valuesl = len(self.values) - 1
                self.mode = 'toggle'
        
        # register new commands
        self.command = xjm.CreateCommand(command, description)
        self.newCH = self.CommandHandler
        if (self.mode == 'incremental' or (self.mode == 'toggle' and self.valuesl > 0)):
            self.command_down = xjm.CreateCommand(command + '_rev' , description)
            self.newCH_down = self.CommandHandler_down
            XPLMRegisterCommandHandler(self.plugin, self.command_down, self.newCH_down, INBEFORE, 0)
        
        #print "register", id(self.plugin), self.command, id(self.newCH)
        XPLMRegisterCommandHandler(self.plugin, self.command, self.newCH, INBEFORE, 0)

    def CommandHandler(self, inCommand, inPhase, inRefcon):
        if (inPhase == 0):
            self.action(self.increment)
            if (self.repeat): 
                self.rincrement = self.increment
                XPLMSetFlightLoopCallbackInterval(self.plugin, self.repeatCH, 0.3, 1, 0)
        if (inPhase == 2 and self.repeat):
            XPLMSetFlightLoopCallbackInterval(self.plugin, self.repeatCH, 0, 0, 0)
        return 1
    
    def CommandHandler_down(self, inCommand, inPhase, inRefcon):
        if (inPhase == 0):
            self.action(self.increment * -1)
            if (self.repeat): 
                self.rincrement = self.increment * -1
                XPLMSetFlightLoopCallbackInterval(self.plugin, self.repeatCH, 0.3, 1, 0)
        if (inPhase == 2 and self.repeat):
            XPLMSetFlightLoopCallbackInterval(self.plugin, self.repeatCH, 0, 0, 0)
        return 1
    
    def incremental(self, increment):
        self.dataref.value += increment
        pass
    
    def RepeatCallback(self, elapsedMe, elapsedSim, counter, refcon):
        """
        Performs increment repetitions
        """
        self.action(self.rincrement)
        return 0.02
    
    def toggle_loop(self, increment):
        self.valuesi += increment
        if (self.valuesi > self.valuesl): self.valuesi = 0
        if (self.valuesi < 0): self.valuesi = self.valuesl
        self.dataref.value = self.values[self.valuesi]
    
    def toggle(self, increment):
        if (self.valuesl >= (self.valuesi + increment) >= 0):
            self.valuesi += increment
        self.dataref.value = self.values[self.valuesi]
    
    def destroy(self):
        #print "destroy", id(self.plugin), self.command, id(self.newCH)
        XPLMUnregisterCommandHandler(self.plugin, self.command, self.newCH, INBEFORE, 0)
        if (self.mode == 'incremental' or (self.mode == 'toggle' and self.valuesl > 0)):
            XPLMUnregisterCommandHandler(self.plugin, self.command_down, self.newCH_down, INBEFORE, 0)
        if (self.repeat):
            XPLMUnregisterFlightLoopCallback(self.plugin, self.repeatCH, 0)
        pass

class JoySwitch:
    def __init__(self, plugin, new_command, description, dataref, type='int', onval=1, offval=0):
        self.plugin = plugin
        self.dataref = EasyDref(dataref, type)
        self.onval = self.dataref.cast(onval)
        self.offval = self.dataref.cast(offval)
        self.command = new_command

        # register new command
        self.command = xjm.CreateCommand(self.command, description)
        self.newCH = self.CommandHandler
        #print "register", id(self.plugin), self.command, id(self.newCH)
        XPLMRegisterCommandHandler(self.plugin, self.command, self.newCH, INBEFORE, 0)

    def CommandHandler(self, inCommand, inPhase, inRefcon):
        if (inPhase == 0):  
            self.dataref.value = self.onval
        if (inPhase == 2):
            self.dataref.value = self.offval
        return 1

    def destroy(self):
        XPLMUnregisterCommandHandler(self.plugin, self.command, self.newCH, INBEFORE, 0)

class PythonInterface:
    """
    Main plugin
    """    
    def XPluginStart(self):
        self.Name = "X-plane Joy Map tool - " + VERSION
        self.Sig = "xJoyMap-v.joanpc.PI"
        self.Desc = "Provides advanced joy mapping features"
        self.axis, self.buttons, self.buttonsdr =  [], [], []
        self.shift = 0
        
        self.sys_path = ""
        self.sys_path = XPLMGetSystemPath(self.sys_path)
        
        self.shiftcommand = xjm.CreateCommand("shift", "Shift button")
        self.shiftCH = self.shiftHandler
        XPLMRegisterCommandHandler(self, self.shiftcommand, self.shiftCH, INBEFORE, 0)
        
        # Datarefs
        self.axis_values_dr = XPLMFindDataRef("sim/joystick/joystick_axis_values")

        # Main floop
        self.floop = self.floopCallback
        XPLMRegisterFlightLoopCallback(self, self.floop, 0, 0)
        
        # Main menu
        self.Cmenu = self.mmenuCallback
        self.mPluginItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), 'xJoyMap', 0, 1)
        self.mMain = XPLMCreateMenu(self, 'xJoyMap', XPLMFindPluginsMenu(), self.mPluginItem, self.Cmenu, 0)
        self.mReload = XPLMAppendMenuItem(self.mMain, 'Reload config', False, 1)
        
        return self.Name, self.Sig, self.Desc
    
    def mmenuCallback(self, menuRef, menuItem):
        # Start/Stop menuitem
        if menuItem == 0:
            self.clearConfig()
            self.config()

    def config(self, startup = False):
        # Defaults
        defaults = {'type':"int", 'release':1, 'negative': 0, 'shift': 0, 'round': 0, 'shifted_command': False, \
                    'values': False, 'increment' : False, 'description': '', 'override': False, 'repeat': False, 'loop': 'True'}
        
        config = ConfigParser.RawConfigParser()
        alias_commands=[]
                
        # Plane config
        # Sandy Barbour 21/10/2010 - This will only work when Xplane is up and running.
        # Calling it from XPluginStart will return garbage and could crash Xplane as the strings are full of rubbish
        # If Xplane doesn't crash then is is also possible that the Python scripts can cause strange behaviour
        
        # Load only the main config on startup
        if (startup):
            config.read(self.sys_path + 'Resources/plugins/PythonScripts/' + CONF_FILENAME)
        else:
            # Try to load the aircraft config or reset the main conf
            plane, plane_path = XPLMGetNthAircraftModel(0)
            if (not config.read(plane_path[:-4] + ACF_CONF_FILENAME)):
                if (not config.read(plane_path[:-len(plane)] + CONF_FILENAME)):
                    config.read(self.sys_path + 'Resources/plugins/PythonScripts/' + CONF_FILENAME)
                     
        for section in config.sections():            
            conf = dict(defaults)
            xjm.debug("[" + section + "]", 2)
            if (section == "Constants"):
                for item in config.items(section):
                    param = item[1].split(',')
                    if (len(param) < 2):
                        param[3] = 'int'
                    xjm.ConstantDataref(param[0].strip(), param[1].strip(), param[2].strip())
                break
            
            for item in config.items(section):
                conf[item[0]] = item[1]
        
            """
            Add new classes here
            TODO: This code will be rewritten maybe each class should check their parameters..
            it's kind of ugly all that stuff here :)
            """
            # Sandy Barbour - Need to pass in PythonInterface address so that callbacks etc will work from withing a class

            # JoyAxis Assignments
            if  (xjm.CheckParams(['axis', 'dataref', 'range'], conf)):
                self.axis.append(JoyAxisAssign(self, int(conf['axis']), \
                conf['dataref'], conf['range'], conf['type'], conf['release'], \
                conf['round']))
            # JoySwitch
            elif (xjm.CheckParams(['new_command', 'on_value', 'off_value', 'dataref'], conf)):
                self.buttons.append(JoySwitch(self, conf['new_command'], conf['description'], conf['dataref'], conf['type'], conf['on_value'], conf['off_value']))
            # JoyButtonDataref
            elif(xjm.CheckParams(['new_command', 'dataref'], conf)):
                self.buttonsdr.append(JoyButtonDataref(self, conf['new_command'], conf['dataref'], conf['type'],\
                conf['values'], conf['increment'], conf['repeat'], (not conf['loop'].lower() in ['no', 'false', 'disabled', '0', 'disable', 'off']) , section))
            # joyButtonAlias
            elif (xjm.CheckParams(['new_command', 'main_command'], conf)):
                alias_commands.append(conf) # store alias
        # Alias should be defined at the end
        for conf in alias_commands:
            self.buttons.append(JoyButtonAlias(self, conf['new_command'], conf['main_command'], \
            conf['shifted_command'], section, conf['override']))
            
        # Reenable flightloop if we have axis defined   
        if (len(self.axis)): XPLMSetFlightLoopCallbackInterval(self, self.floop, -1, 0, 0)
        xjm.debug("config end")
            
    def clearConfig(self):
        """
        Clears all the assignments and disables the flightloop
        """
        xjm.debug("clearConfig start")
        # Disable flightloop
        XPLMSetFlightLoopCallbackInterval(self, self.floop, 0, 0, 0)
        # Destroy commands
        for command in self.buttons: command.destroy()
        for command in self.buttonsdr: command.destroy()
        # and buttons
        self.buttons, self.buttonsdr, self.axis = [], [], []
        xjm.debug("clearConfig end")
        
    def shiftHandler(self, inCommand, inPhase, inRefcon):
        """
        Defines the shift status
        """
        if (inPhase == 0):
            self.shift = 1
        elif (inPhase == 2):
            self.shift = 0
        return 1

    def floopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        """
        Main flight loop: calls axis classes .updateloop
        """
        # Get all axis
        axis_values = []
        XPLMGetDatavf(self.axis_values_dr, axis_values , 0 ,JOY_AXIS)        
        for axis_assign in self.axis:
            axis_assign.updateLoop(axis_values)
        return -1

    def XPluginStop(self):
        self.clearConfig()
        XPLMUnregisterFlightLoopCallback(self, self.floop, 0)
        XPLMUnregisterCommandHandler(self, self.shiftcommand, self.shiftCH, INBEFORE, 0)
        XPLMDestroyMenu(self, self.mMain)
    
    def XPluginEnable(self):
        self.config(True)
        return 1
    
    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        """
        Detects aircraft changes and reloads the config
        """
        if (inFromWho == XPLM_PLUGIN_XPLANE):
            # On plane load
            if (inParam == XPLM_PLUGIN_XPLANE and inMessage == XPLM_MSG_PLANE_LOADED ): # On aircraft change
                plane, plane_path = XPLMGetNthAircraftModel(0)
                """
                Detect x737 load, clear config and wait for x737 plugin
                """
                if (path.lexists(plane_path[:-len(plane)] + X737_CHECK_FILE)): 
                    self.clearConfig()
                    return
                else:
                    self.clearConfig()
                    self.config()
                    pass
        # x737 Plug-in loaded, load config
        X737_ID = XPLMFindPluginBySignature('bs.x737.plugin')
        if (inFromWho == X737_ID):
            if (inMessage == X737_INITIALIZED_MESSAGE):
                xjm.debug("x737 plug-in initiated, reloading config")
                self.config()
            elif (inMessage == X737_UNLOADED_MESSAGE):
                xjm.debug("x737 plug-in unloaded, clearing config")
                self.clearConfig()
        else:
            xjm.debug("message from: " + str(inFromWho) + ' id: ' +  str(inMessage), 3)
        pass