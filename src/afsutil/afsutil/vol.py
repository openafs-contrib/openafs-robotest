
from __future__ import print_function

class Vnode(object):
    REG = 0
    INFO = 1
    SMALL = 2
    LARGE = 3
    LINK = 4

    def __init__(self):
        pass

    @classmethod
    def create(cls, vntype, partid, pvid, vid):
        print("Vnode.create")

class VnodeSpecial(Vnode):

    @classmethod
    def create(cls, vntype, partid, pvid, vid):
        print("VnodeSpecial.create")

class Volume(object):

    def __init__(self, partid, pvid, vid):
        self.part = partid
        self.pvid = pvid
        self.vid = vid
        self.special = {}

    @classmethod
    def create(cls, partid, pvid, vid):
        volume = cls(partid, pvid, vid)
        for vntype in (Vnode.INFO, Vnode.SMALL, Vnode.LARGE, Vnode.LINK):
            volume.special[vntype] = VnodeSpecial.create(vntype, vid, pvid)


