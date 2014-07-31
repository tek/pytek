import sure  # NOQA
from flexmock import flexmock  # NOQA

from tek import Configurations  # NOQA
from tek.test import Spec
from tek.util.decorator import lazy_property, lazy_class_property

import tests  # NOQA


class LazyPropSpecimen(object):

    def __init__(self):
        self.indicator = 1

    @lazy_property
    def culprit(self):
        self.indicator = 5
        return 2


class LazyClassPropSpecimen(object):
    indicator = 1

    @lazy_class_property
    def culprit(self):
        self.indicator = 5
        return 2

    def test(self):
        return setattr(self, 'foo', 66)


class Decorator_(Spec, ):

    def setup(self, *a, **kw):
        super(Decorator_, self).setup(*a, **kw)

    def lazy_property(self):
        specimen = LazyPropSpecimen()
        specimen.indicator.should.equal(1)
        specimen.culprit.should.equal(2)
        specimen.indicator.should.equal(5)

        def setter():
            specimen.culprit = 4
        setter.when.called_with().should.throw(AttributeError)
        del specimen.culprit

    def lazy_class_property(self):
        specimen = LazyClassPropSpecimen()
        specimen.indicator.should.equal(1)
        specimen.culprit.should.equal(2)
        specimen.indicator.should.equal(5)

__all__ = ['Decorator_']
