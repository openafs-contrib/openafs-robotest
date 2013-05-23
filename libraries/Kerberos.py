import os as os
import re as re

try:
    from robot.api import logger
except ImportError:
    logger = None

class Kerberos:

    def init(self):
        pass

    def read_des_kvno(self, keytab, cell, realm):
        """ Get the kvno of the afs DES key from the keytab file.

            Returns the largest kvno if there is more than one.
        """
        self._log("Read KVNO: keytab='%s', cell='%s', realm='%s'" %
            (keytab, cell, realm), 'INFO')
        kvnos = [None]
        re_princ = re.compile("afs(/%s)?@%s" % (cell, realm))
        re_des = re.compile("(des-)|(DES )") # single des
        re_line = re.compile("\s*(\d+)\s+(\S+)\s+\((\S+)\)")
        command = "sudo klist -k -e %s" % (keytab)
        self._log("Running: %s " % (command), 'INFO')
        klist = os.popen(command)
        for line in klist.readlines():
            self._log(line.rstrip(), 'INFO')
            match = re_line.match(line)
            if match:
                kvno = int(match.group(1))
                princ = match.group(2)
                enctype = match.group(3)
                self._log("kvno=%d, princ='%s', enctype='%s'" % (kvno, princ, enctype), 'INFO')
                if re_princ.match(princ) and re_des.match(enctype):
                    kvnos.append(kvno)
        rc = klist.close()
        if not rc is None:
            raise AssertionError("klist failed: exit code=%d" % (rc))
        kvno = sorted(kvnos, reverse=True)[0]
        if kvno is None:
            raise AssertionError("Failed to find a kvno of afs key in file '%s'." % (keytab))
        self._log("kvno: %d" % (kvno), 'INFO')
        return kvno


    def _log(self, msg, level):
        if logger:
            logger.write(msg, level)
        else:
            print '*%s* %s' % (level, msg)

if __name__ == "__main__":
    logger = None
    k = Kerberos()
    k.read_kvno('keytabs/afs.keytab', 'robotest', 'LOCALCELL')

