
#
# Unit Tests
#
class VolumeKeywordTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.v = _VolumeKeywords()

    def test_create(self):
        name = 'unittest.xyzzy'
        path = "/afs/.robotest/test/%s" % name
        self.v.create_volume(name, path=path, ro=True)
        self.v.remove_volume(name, path=path)

    def test_should_exist(self):
        self.v.volume_should_exist('root.cell')

    def test_should_not_exist(self):
        self.v.volume_should_not_exist('does.not.exist')

    def test_location(self):
        name_or_id = 'root.cell'
        server = socket.gethostname()
        part = 'a'
        self.v.volume_location_matches(name_or_id, server, part, vtype='rw')

    def test_unlocked(self):
        self.v.volume_should_be_unlocked('root.cell')

# usage: PYTHONPATH=libraries python -m OpenAFSLibrary.keywords.volume
if __name__ == '__main__':
    unittest.main()

