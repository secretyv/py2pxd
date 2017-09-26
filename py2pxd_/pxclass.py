#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import logging

from pxreader   import PXReader
from pxvariable import PXVariable
from pxfunction import PXFunction

LOGGER = logging.getLogger("INRS.IEHSS.Python.cython.class")

class PXClass(ast.NodeVisitor, PXReader):
    def __init__(self):
        super(PXClass, self).__init__()
        self.node = None
        self.name = None
        self.type = None
        self.bases = []
        self.meths = []
        self.attrs = {}

    def __eq__(self, other):
        return self.name == other.name

    def merge(self, other):
        assert self == other
        LOGGER.debug('PXClass.merge: %s', self.name)
        self.bases = self.bases + [i for i in other.bases if i not in self.bases]

        for k in other.attrs:
            self.attrs.setdefault(k, other.attrs[k])
        for k in self.attrs:
            try:
                self.attrs[k].merge(other.attrs[k])
            except KeyError:
                pass

        self.meths = self.meths + [i for i in other.meths if i not in self.meths]
        for meth in self.meths:
            try:
                idx = other.meths.index(meth)
                meth.merge(other.meths[idx])
            except ValueError:
                pass

    #--------------------
    #   Python source code parser (ast visitors)
    #--------------------
    def getOneBaseName(self, node):
        if isinstance(node, ast.Attribute):
            return '.'.join((self.getOneBaseName(node.value), node.attr))
        elif isinstance(node, ast.Name):
            return node.id

    def visit_ClassDef(self, node):
        print ValueError('Nested classes are not yet supported')

    def visit_FunctionDef(self, node):
        isSpecialName = False
        if len(node.name) > 4 and node.name[:2] == '__' and node.name[-2:] == '__':
            isSpecialName = True

        v = PXFunction(self)
        v.doVisit(node)
        if not isSpecialName: self.meths.append(v)
        self.attrs.update(v.attrs)

    def visit_Assign(self, node):
        """Class attributes"""
        try:
            v = ast.literal_eval(node.value)
            t = type(v)
        except Exception as e:
            LOGGER.debug('Exception: %s', str(e))
            t = type(None)
        for tgt in node.targets:
            if tgt.id not in ['__slots__']:
                a = PXVariable()
                a.doVisit(tgt.id, type_name=t)
                self.attrs[a.name] = a

    def doVisit(self, node):
        self.node = node
        self.name = self.node.name
        self.bases = [self.getOneBaseName(n) for n in node.bases]
        self.generic_visit(node)

    def resolveHierarchy(self, knownClasses):
        """
        """
        # ---  Look for childrens
        childs = []
        for c in knownClasses:
            if self.name in c.bases: childs.append(c)
        # ---  Resolve first childrens
        for c in childs:
            c.resolveHierarchy(knownClasses)
        # ---  Remove attributes allready defined in parent
        for c in knownClasses:
            if c.name in self.bases:
                LOGGER.debug('PXClass.resolveHierarchy: %s is child of %s', self.name, c.name)
                for a in c.attrs:
                    if a in self.attrs:
                        del self.attrs[a]

    #--------------------
    #   Reader for pxd files
    #--------------------
    def read_attr(self, attr):
        try:
            attr = attr.split('cdef ')[1].strip()
            attr = attr.split('public ')[1].strip()
        except Exception:
            pass
        a = PXVariable()
        a.read_arg(attr)
        self.attrs[a.name] = a

    def read_decl(self, decl):
        assert decl[-1] == ':'
        decl = decl[:-1]
        decl = decl.split('class ')[1]
        decl = decl.strip()
        try:
            d, h = decl.split('(', 1)
            h = h[:-1]
            self.bases = [h_.strip() for h_ in h.split(',')]
        except Exception:
            d = decl
        try:
            t, n = d.split(' ')
        except Exception:
            t, n = '', d
        self.type = t.strip()
        self.name = n.strip()

    def read(self, decl, fi):
        self.read_decl(decl)
        LOGGER.debug('PXClass.read: %s', self.name)
        lcls = {}
        for l in PXReader.read_line(fi):
            if l == 'pass':
                pass
            elif l[0:5] == 'cdef ':
                self.read_attr(l)
            elif l[0:6] == 'cpdef ':
                f = PXFunction(self)
                f.read(l, lcls)
                LOGGER.debug('    append method %s', f.name)
                self.meths.append(f)
                lcls = {}
            elif l[0:14] == '@cython.locals':
                lcls = PXReader.read_locals(l)
            elif l == '':
                return

    #--------------------
    #   Writer for pxd file
    #--------------------
    def write(self, fo, indent=0):
        bases = ''
        if self.bases:
            bases = '(%s)' % ', '.join(self.bases)
        fmt = '{indent}cdef class {name}{bases}:\n'
        s = fmt.format(indent=' '*indent, name=self.name, bases=bases)
        fo.write(s)
        indent += 4
        if self.attrs or self.meths:
            fmt = '{indent}cdef public {type:12s} {name}\n'
            for k in sorted(self.attrs.keys()):
                s = fmt.format(indent=' '*indent, type=self.attrs[k].type, name=self.attrs[k].name)
                fo.write(s)
            if self.attrs and self.meths:
                s = '{indent}#\n'.format(indent=' '*indent)
                fo.write(s)
            for m in self.meths:
                m.write(fo, indent=indent)
        else:
            s = '{indent}pass\n'.format(indent=' '*indent)
            fo.write(s)


if __name__ == "__main__":
    def main():
        c = PXClass()

    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
    LOGGER.setLevel(logging.DEBUG)

    main()
