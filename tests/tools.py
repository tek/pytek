from tek.tools import sizeof_fmt
from tek.test import Spec, sure


class Tools_(Spec):

    def sizeof_fmt(self):
        sizeof_fmt(1450000, prec=3, bi=False).should.equal('1.450 MB')
        sizeof_fmt(1450000, bi=True).should.equal('1.4 MB')
