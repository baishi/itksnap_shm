from __future__ import print_function
import os, sys, re, random, math
import time
import mmap
import ctypes
import struct
import atexit

import ctypes
#import posix_ipc
#import sysv_ipc

rtld = ctypes.cdll.LoadLibrary('librt.so')
class Vector3d(ctypes.Structure):
    _fields_ = [
        ('value', ctypes.c_double * 3)
    ]
class CameraState(ctypes.Structure):
    _fields_ = [
        ('position', ctypes.c_double * 3),
        ('focal_point', ctypes.c_double * 3),
        ('view_up', ctypes.c_double * 3),
        ('clipping_range', ctypes.c_double * 2),
        ('view_angle', ctypes.c_double),
        ('parallel_scale', ctypes.c_double),
        ('parallel_projection', ctypes.c_int32),
    ]

class IPCMessage(ctypes.Structure):
    """This is the IPC shared memory message for ITK-SNAP version 0x1005
    The message body is encapsuled with a 10 byte header
    version int16: currently fixed as 0x1005
    sender_pid int32: the process id of the sender
    message_id int32: the message id of the sender
    ITK-SNAP will check shared memory with 30ms interval, if the combination of
    sender_pid and message_id in the shared memory does not change, no handling
    will be invoked.
    Otherwise, ITK-SNAP will check if the process of `sender_pid` is still alive.
    If the process terminates before shared memory is read, the message will be
    ignored.
    If the module is ready in a one off application. Please make sure to sleep at
    least 30ms for the command to be processed.
    cursor double[3]: an array of current cursor position in NIFTI Coordinate
    zoom_levels double[3]: the zoom levels in each direction
    viewPositionRelative float[2][3]: an array pair of float indicating the pan
        offset of x, y in each pane
    camera CameraState struct for vtk view
    versionEnum int32: a fixed nnumber of 0x1005

    """

    _fields_ = [
        ('version', ctypes.c_short), # This is the protocol version number
                                     # fixed as 0x1005
        ('sender_pid', ctypes.c_long),
        ('message_id', ctypes.c_long),
        ('cursor', ctypes.c_double * 3), # Vector3d
        ('zoom_levels', ctypes.c_double * 3),
        ('viewPositionRelative', ctypes.c_float * 2 * 3),
        ('camera', CameraState), # CameraState
        ('VersionEnum', ctypes.c_uint), # default 0x1005
    ]

def shmget(shm_key):
    #if isinstance(shm_key, basestring):
    #    key = ctypes.create_string_buffer(shm_key)
    #elif isinstance(shm_key, unicode):
    #    key = ctypes.create_unicode_buffer(shm_key)
    #else:
    #    raise TypeError('`key` must be `bytes` or `unicode`')

    _shmget = rtld.shmget
    result = _shmget(ctypes.c_int32(shm_key), ctypes.c_int32(0), ctypes.c_int32(0))
    if result == -1:
        raise RuntimeError('IPC endpoint %s not available' % (shm_key))
        #raise RuntimeError(os.strerror(ctypes.get_errno()))
    return result

def shmat(shm_id):
    _shmat = rtld.shmat
    _shmat.restype = ctypes.c_void_p
    _shmat.argtypes = (ctypes.c_int32, ctypes.c_void_p, ctypes.c_int32)
    none = None
    none_ptr = ctypes.cast(none, ctypes.POINTER(ctypes.c_voidp))

    result = _shmat(shm_id, none, 0)
    #result = ctypes.cast(result, ctypes.c_voidp)
    if result == -1:
        raise RuntimeError('IPC id %s open fail' % (shm_id))
    return result

def shmdt(shmaddr):
    _shmdt = rtld.shmdt
    _shmdt.argtypes = (ctypes.c_void_p,)
    result = _shmdt(shmaddr)
    return result

def ftok(key, version):
    #if isinstance(key, basestring):
    #    key = ctypes.create_string_buffer(key)
    #elif isinstance(key, unicode):
    #    key = ctypes.create_unicode_buffer(key)
    #else:
    #    raise TypeError('`key` must be `bytes` or `unicode`')
    key = ctypes.create_string_buffer(key.encode('utf-8'))

    result = rtld.ftok(key, ctypes.c_int(version))
    if result == -1:
        raise RuntimeError(os.strerror(ctypes.get_errno()))
    return result

class SNAPManager(object):
    def __init__(self, pref_path=None):
        pid = os.getpid()
        self.pid = pid
        last_pid = None
        last_message_id = None
        #shm_key = ftok('/home/baishi/.itksnap.org/ITK-SNAP/UserPreferences.xml', 0x1005)
        if pref_path is None:
            home = os.path.expanduser('~')
            pref_path = os.path.join(home, '.itksnap.org', 'ITK-SNAP', 'UserPreferences.xml')

        shm_key = ftok(pref_path, 0x1005)
        shm_fd = shmget(shm_key)
        mem_addr = shmat(shm_fd)
        self.mem_addr = mem_addr
        @atexit.register
        def detach():
            shmdt(mem_addr)

    def loop(self):
        msg = IPCMessage()
        mem_addr = self.mem_addr
        while True:
            ctypes.memmove(ctypes.byref(msg), mem_addr, ctypes.sizeof(msg))
            if msg.sender_pid == last_pid and msg.message_id == last_message_id:
                time.sleep(0.02)
                continue
            else:
                last_message_id = msg.message_id
                last_pid = msg.sender_pid
            #msg.sender_pid = pid
            #msg.message_id = msg.message_id + 1

            #handle = random.choice([0, 1, 2])
            #hnd = msg.cursor[handle]
            #msg.cursor[handle] = hnd + (random.random() - 0.5) * 0.1
            #ctypes.memmove(mem_addr, ctypes.byref(msg), ctypes.sizeof(msg))
            print ('Message version', msg.version, 'sender_pid', msg.sender_pid, 'message_id', msg.message_id)
            print ('vector', msg.cursor[0], msg.cursor[1], msg.cursor[2])
            print ('zoom level', msg.zoom_levels[0], msg.zoom_levels[1], msg.zoom_levels[2])
            #print ('2f', msg.viewPositionRelative[0][0], msg.viewPositionRelative[1][0], msg.viewPositionRelative[2])
            print ('2f', msg.viewPositionRelative[2][0], msg.viewPositionRelative[2][1])
            print ('camera', msg.camera.position[0], msg.camera.position[1], msg.camera.position[2])
            time.sleep(0.1)

    def read(self):
        mem_addr = self.mem_addr
        msg = IPCMessage()
        ctypes.memmove(ctypes.byref(msg), mem_addr, ctypes.sizeof(msg))
        return msg

    def dump(self, msg):
        print ('Message dump: version %s, from sender %s with id %s' % (msg.version, msg.sender_pid, msg.message_id) )
        print ('Cursor position %.3f %.3f %.3f' % (msg.cursor[0], msg.cursor[1], msg.cursor[2]))
        print ('Zoom level A: %.3f S: %.3f C: %.3f' % (msg.zoom_levels[0], msg.zoom_levels[1], msg.zoom_levels[2]))
        #print ('2f', msg.viewPositionRelative[0][0], msg.viewPositionRelative[1][0], msg.viewPositionRelative[2])
        print ('Panel offset A: %.2f,%.2f S: %.2f,%.2f C: %.2f,%.2f' % (
            msg.viewPositionRelative[0][0], msg.viewPositionRelative[0][1],
            msg.viewPositionRelative[1][0], msg.viewPositionRelative[1][1],
            msg.viewPositionRelative[2][0], msg.viewPositionRelative[2][1]
        ))
        print ('VTK Camera X: %s, Y: %s, Z: %s' % (
            msg.camera.position[0], msg.camera.position[1], msg.camera.position[2]
        ))

    def move_mouse(self, x, y, z):
        msg = IPCMessage()
        mem_addr = self.mem_addr
        ctypes.memmove(ctypes.byref(msg), mem_addr, ctypes.sizeof(msg))
        msg.sender_pid = self.pid
        msg.message_id = msg.message_id + 1
        msg.cursor[0] = x
        msg.cursor[1] = y
        msg.cursor[2] = z
        ctypes.memmove(mem_addr, ctypes.byref(msg), ctypes.sizeof(msg))

    def change_zoom(self, x, y, z):
        msg = IPCMessage()
        mem_addr = self.mem_addr
        ctypes.memmove(ctypes.byref(msg), mem_addr, ctypes.sizeof(msg))
        msg.sender_pid = self.pid
        msg.message_id = msg.message_id + 1
        msg.zoom_levels[0] = x
        msg.zoom_levels[1] = y
        msg.zoom_levels[2] = z
        ctypes.memmove(mem_addr, ctypes.byref(msg), ctypes.sizeof(msg))

if __name__ == '__main__':
    snap = SNAPManager()
    msg = snap.read()
    print (msg.cursor[0])
    snap.dump(msg)
    snap.move_mouse(float(-8) + random.random() * 10, float(-29), float(-10))
    snap.change_zoom(20, 20, 20)
    time.sleep(0.3)
