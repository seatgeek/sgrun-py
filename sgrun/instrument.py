"""
Code for instrumenting our python applications.
"""
import atexit
import sys


class Instrumenter(object):

    def instrument(self):  # type: () -> None
        print("starting application!")
        atexit.register(lambda: print("ending application!"))


def instrument_application():  # type: () -> None
    Instrumenter().instrument()
