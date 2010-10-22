xJoyMap 1.0rc1:

xJoyMap wants to be a simple way to modify datarefs with your joystick and/or creating
advanced combined commands

Implements the following modes:

axis2dataref:     maps a joystick axis to a dataref
button2dataref    incrementa:l increment / decrement a dataref pressing a joy button
button2dataref    toggle: toggle between predefined values on button press
buttonAlias:      creates Alias, combo and "shifted" commands

It should be useful to:

* Users who want to change the behavior their joystick between aircraft
  changes without visiting the joy config pane (see the x737 config example)

* Hardware Cockpit builders who want to assign dozens of buttons 
  and switches without having to write their own plug-ins.

* Airplane builders with custom plugins who doesn't want 
  to write all the button to dataref communication.

Please share your config files with the community!!

Please feel free to post your patches, bugs and contributions
at http://github.com/joanpc/xJoyMap

=============
Installation
=============

You need the awesome PYTHON INTERFACE PLUGIN by Sandy Barbour
http://www.xpluginsdk.org/python_interface.htm

Copy PI_xJoyMap.py and xJoyMap.ini to your 
Resources/plugins/PythonScripts directory.

Edit xJoyMap.ini to fit your needs. It contains some examples
and comments to help you.

If you want specific commands for an aircraft
copy xJoyMap.ini to the aircraft folder and modify it.
You can also use aircraftname.xjm in your aircraft folder.

===================
Configuration/Help
===================

Check the config files in the examples folder for more info.

=============
Future plans
=============

Constant dataref:     Define constant values for datarefs on plane load (useful to set the fov for example)
Incremental repeat:   Repeat increment while the button is pressed
Switch mode:          Useful for hardware switches (pressed_value, unpressed_value)
More shift commands:  To be able to map the saitek x52 mode switch  

*Maybe*
shift axis:           Define axis assignments for each shift state
override yoke   

======
Thanks
======

Many thanks to Sandy Barbour for the awesome X-Plane Phyton Interface and, his support, recommendations and fixes. 
And all the x-plane.org community.


Enjoy
Joan

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
