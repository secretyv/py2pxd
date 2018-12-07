#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import logging

from .pxreader   import PXReader
from .pxvariable import PXVariable

LOGGER = logging.getLogger("INRS.IEHSS.Python.cython.class")

class PXEnum(ast.NodeVisitor, PXReader):
    def __init__(self):
        super(PXEnum, self).__init__()
        self.node = None
        self.name = None
        self.type = None
        self.attrs = []

    def __eq__(self, other):
        return self.name == other.name

    def merge(self, other):
        assert self == other
        LOGGER.debug('PXEnum.merge: %s', self.name)

        for k in self.attrs:
            try:
                io = other.attrs.index(k)
                k.merge(other.attrs[io])
            except IndexError:
                pass

    #--------------------
    #   Python source code parser (ast visitors)
    #--------------------
    def visit_ClassDef(self, node):
        print(ValueError('Nested enum are not supported'))

    def visit_Tuple(self, node):
        LOGGER.debug('PXEnum.visit_Tuple')
        for item in node.elts:
            a = PXVariable()
            a.doVisit(item.s)
            self.attrs.append(a)

    def visit_Call(self, node):
        LOGGER.debug('PXEnum.visit_Call')
        self.generic_visit(node)

    def doVisit(self, node):
        LOGGER.debug('PXEnum.doVisit')
        assert isinstance(node, ast.Assign)
        assert isinstance(node.value, ast.Call)
        self.node = node
        self.name = self.node.targets[0].id
        LOGGER.debug('PXEnum.doVisit: enum %s', self.name)
        self.generic_visit(node)

    #--------------------
    #   Reader for pxd files
    #--------------------
    def read_items(self, attr):
        items = attr.split(',')
        for item in items:
            item = item.strip()
            if not item: continue
            try:
                a = PXVariable()
                a.read_arg(item)
                self.attrs.append(a)
                LOGGER.debug('PXEnum.read_items: add item %s=%s', a, a.val)
            except Exception:
                pass

    def read_decl(self, decl):
        assert decl[-1] == ':'
        decl = decl[:-1]
        decl = decl.split('enum ')[1]
        decl = decl.strip()
        try:
            t, n = decl.split(' ')
        except Exception:
            t, n = '', decl
        self.type = t.strip()
        self.name = n.strip()

    def read(self, decl, fi):
        self.read_decl(decl)
        LOGGER.debug('PXEnum.read: %s', self.name)
        for l in PXReader.read_line(fi):
            if l == 'pass':
                pass
            elif l == '':
                return
            else:
                self.read_items(l)

    #--------------------
    #   Writer for pxd file
    #--------------------
    def write(self, fo, indent=0):
        fmt = '{indent}cdef enum {name}:\n'
        s = fmt.format(indent=' '*indent, name=self.name)
        fo.write(s)
        indent += 4
        if self.attrs:
            for a in self.attrs:
                attr = ''
                if a.name: attr += '%s'  % a.name
                if a.val not in [PXVariable.Status.Undefined, PXVariable.Status.Invalid]:
                    attr += ' = %s' % a.val
                fmt = '{indent}{attr}\n'
                s = fmt.format(indent=' '*indent, attr=attr)
                fo.write(s)
        else:
            s = '{indent}pass\n'.format(indent=' '*indent)
            fo.write(s)


if __name__ == "__main__":
    def main():
        c = PXEnum()

    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
    LOGGER.setLevel(logging.DEBUG)

    main()
