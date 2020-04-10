[ITK-SNAP Shared Memory](https://github.com/baishi/itksnap_shm)
=========================================================

The ITK-SNAP program has an not well documented SYSV IPC shared memory interface to synchronize cursor position, zoom level etc across different running instances.

Sometimes it is desirable to manipulate the inter process communication. The itksnap_shm library is for easy access to this interface.

Installation
------------
The library is designed to work cross platform. However, at current stage, it has only been tested on Linux.

To setup 
```
pip install -e .
```

Brief Tutorial
--------------
First initialize the SNAPManager to attach to the shared memory segment

```
>>> import time
>>> import itksnap_shm
>>> snap = itksnap_shm.SNAPManager()
```

To read the shared memory and parse it into more user friendly data structure
```
>>> msg = snap.read()
```
Now msg will be a structure of IPCMessage

The accessible attributes are:
version, sender_pid, message_pid (these attributes are internal protocol data which doesn't affect ITKSNAP operations)
cursor, a 3-element array of double for physical coordinate of cursor location (in NIfTI World Coordinate)
The first element is always Top-Left pane, and the second is the Top-Right pane. The last element is the Bottom-Right (coronal) pane.
zoom_levels, same as curosr, a e-element array. The unit is pixel per mm.
viewPositionRelative, an array of 3 pair of coordinates. For each of the pane, the pan of image relative to the view port. In NIfTi World Coorindate)
camera, a CameraState structure for VTK 3D model camera
VersionEnum, alway set to 0x1005 for current version.

```
>>> msg.cursor[0]
-6.776136864512334
>>> msg.cursor[0], msg.curosr[1], msg.curosr[2]
(-6.776136864512334, -29.0, -10.0)
>>> msg.zoom_levels[0], msg.zoom_levels[1], msg.zoom_levels[2]
(20.0, 20.0, 20.0)
```

The CameraState structure has following attributes:
position, the camera position as 3-vector double array, the unit is NIfTi World Coordinate
focial_point, the focal point of the camera. The representation and unit is same as above.
view_up, to be documented
clipping_range, a pair of coordinate to define how far to clip the 3d model
view_angle, a double value for the angle in degrees
prallel_scale, to be documented
parallel_projection, a long int for parallel_projection

Example to set values
---------------------
Set zoom level of z axis to be 40 pixel per mm.
```
>>> snap.change_zoom(msg.zoom_levels[0], msg.zoom_levels[1], 40.)
```
Move current cursor of ITKSNAP to location X -8, Y -29, Z -11
```
>>> snap.move_mouse(-8, -29., -11)
```
Remember to sleep for at least 0.3 second if not running in a loop for ITKSNAP to have a chance to read the update values.
ITKSNAP will check if the process with id sender_pid is still alive. If the process is already terminated, it will ignore the message.
```
>>> time.sleep(0.3)
```
Licensing
-----------------------------
This source code is distributed under the term of [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html).
