#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger("INRS.IEHSS.Python.cython.reader")

from pxvariable import PXVariable

class PXReader(object):
    def __init__(self):
        pass

    @staticmethod 
    def read_line(fi):
        """
        Load a complete statement that can be spread over multiple lines
        """
        indt = 0
        ls = []
        while True:
            l = fi.readline()
            if not l: break  # eof
            # ---  Clean
            l = l.strip()
            if l and l[0] != '#':      # Keep comment only line
                l = l.split('#')[0]
                l = l.strip()
            # ---  Count ()
            np = 0
            for c in l:
                if c == '(': np+=1
                if c == ')': np-=1
            # ---  Append to list
            ls.append(l)
            # ---  If () are balanced
            if np == 0:
                l = ' '.join(ls)
                ls = []
                while '  ' in l: l = l.replace('  ', ' ')
                logger.debug('PXReader.read_line: %s' % l)
                yield l

    @staticmethod 
    def read_locals(l):
        """
        Extract the local variables form a @cython.local statement.
        Locals are returned as a dict {variable_name: type_name}
        """
        l = l.split('@cython.locals', 1)[-1]
        l = l.strip()[1:-1]
        lcls = {}
        for lcl in l.split(','):
            var = PXVariable()
            var.read_var(lcl)
            lcls[var.name] = var
        return lcls
                