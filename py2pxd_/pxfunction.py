#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import sys
import logging

from .pxvariable import PXVariable, default_types

LOGGER = logging.getLogger("INRS.IEHSS.Python.cython.function")

class PXFunction(ast.NodeVisitor):
    def __init__(self, class_=None):
        super(PXFunction, self).__init__()
        self.clss = class_
        self.node = None
        self.name = ''
        self.type = ''
        self.args  = []
        self.attrs = {}
        self.locls = {}

    def __eq__(self, other):
        return self.name == other.name

    def merge(self, other):
        assert self == other
        LOGGER.debug('PXFunction.merge: %s', self.name)
        LOGGER.debug('    merge type:  %s and %s', self.type, other.type)
        if self.type != other.type:
            if   self.type in ['']:
                if other.type not in ['']: self.type = other.type
            elif self.type in ['None']:
                if other.type not in ['', 'None']: self.type = other.type
            elif self.type in ['object']:
                if other.type not in ['', 'None', 'object']: self.type = other.type
            else:
                self.type = '__conflict__type__: "%s" "%s"' % (self.type, other.type)
        LOGGER.debug('    merged to %s', self.type)

        #self.args = self.args + [i for i in other.args if i not in self.args]
        for arg in self.args:
            try:
                idx = other.args.index(arg)
                arg.merge(other.args[idx])
            except ValueError:
                LOGGER.info('PXFunction.merge: argument added: %s', arg)
        for arg in other.args:
            try:
                idx = self.args.index(arg)
            except ValueError:
                LOGGER.info('PXFunction.merge: argument removed: %s', arg)

        for k in other.locls:
            self.locls.setdefault(k, other.locls[k])
        for k in self.locls.keys():
            try:
                self.locls[k].merge(other.locls[k])
            except KeyError:
                pass

    #--------------------
    #   Python source code parser (ast visitors)
    #--------------------
    def generic_visit(self, node):
        LOGGER.debug('PXFunction.generic_visit: %s', type(node).__name__)
        ast.NodeVisitor.generic_visit(self, node)

    def doVisit(self, node):
        self.node = node
        self.name = self.node.name
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        LOGGER.info('PXFunction.visit_FunctionDef')
        if self.name:
            print ValueError('Nested functions are not yet supported: %s.%s:%i', self.name, node.name, node.lineno)
        else:
            self.name = node.name
            ast.NodeVisitor.generic_visit(self, node)

    def visit_arguments(self, node):
        LOGGER.debug('PXFunction.visit_arguments')
        # ---  Prepend les valeurs avec des None
        args = node.args
        vals = [None]*len(args)
        vals.extend(node.defaults)
        vals = vals[-len(args):]
        # ---  Itère sur les (args, vals)
        for a, v in zip(args, vals):
            arg = PXVariable()
            arg.doVisit(a.id, value=v)
            if arg.name == 'self' and self.clss:
                arg.type = self.clss.name
            self.args.append(arg)

    def __visit_Attribute(self, node, type_name=None):
        LOGGER.debug('PXFunction.__visit_Attribute')
        try:
            val = node.value.id
        except Exception:
            val = ''
        if val == 'self':
            att = node.attr
            a = PXVariable()
            a.doVisit(att, type_name=type_name)
            self.attrs[a.name] = a

    def __visit_Local(self, node, type_name=None):
        LOGGER.debug('PXFunction.__visit_Local %s as %s', node.id, type_name)
        a = PXVariable()
        a.doVisit(node.id, type_name=type_name)
        # ---  Check if an args
        if a in self.args:
            idx = self.args.index(a)
            self.args[idx].merge(a)
        # ---  Add to locals
        else:
            self.locls[a.name] = a

    def visit_For(self, node):
        LOGGER.debug('PXFunction.visit_For')
        try:
            v = ast.literal_eval(node.iter)
            t = type(v)
        except Exception as e:
            LOGGER.debug('Exception: %s', str(e))
            t = type(None)
        tgt = node.target
        if isinstance(tgt, (ast.Tuple, ast.List)):
            t = type(None)      # we don't know the type of the items
            for e in tgt.elts:
                if isinstance(e, ast.Name):
                    self.__visit_Local(e, t)
        elif isinstance(tgt, ast.Name):
            self.__visit_Local(tgt, t)
        # ---  Continue with the body
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Assign(self, node):
        LOGGER.debug('PXFunction.visit_Assign')
        try:
            v = ast.literal_eval(node.value)
            t = type(v)
        except Exception as e:
            LOGGER.debug('Exception: %s', str(e))
            t = type(None)
        LOGGER.debug('  type is %s', t)

        for tgt in node.targets:
            if isinstance(tgt, ast.Attribute):
                self.__visit_Attribute(tgt, t)
            elif isinstance(tgt, (ast.Tuple, ast.List)):
                t = type(None)      # we don't know the type of the items
                for e in tgt.elts:
                    if isinstance(e, ast.Name):
                        self.__visit_Local(e, t)
            elif isinstance(tgt, ast.Name):
                self.__visit_Local(tgt, t)

    def visit_Return(self, node):
        LOGGER.debug('PXFunction.visit_Return')
        val = node.value
        try:
            if   sys.version_info[0] <  3 and isinstance(val, ast.Name):
                v = ast.literal_eval(val.id)
                t = type(v)
            elif sys.version_info[0] >= 3 and isinstance(val, ast.NameConstant):
                t = type(val.value)
            elif isinstance(val, ast.Num):
                t = type(val.n)
            else:
                t = type(None)
        except Exception as e:
            LOGGER.debug('Exception: %s', str(e))
            t = type(None)
        try:
            self.type = default_types[t]
        except Exception:
            self.type = str(t)

    #--------------------
    #   Reader for pxd files
    #--------------------
    def read_args(self, args):
        self.args = []
        args = args.strip()
        if args:
            for arg in args.split(','):
                a = PXVariable()
                a.read_arg(arg)
                self.args.append(a)

    def read_decl(self, decl):
        try:
            t, n = decl.split(' ')
        except Exception:
            t, n = '', decl
        self.type = t.strip()
        self.name = n.strip()

    def read(self, decl, lcls=None):
        assert decl[0:6] == 'cpdef '
        LOGGER.debug('PXFunction.read: %s', decl)
        n, d = decl[6:].split('(', 1)
        n = n.strip()
        d = d.strip()[:-1]
        self.read_decl(n)
        self.read_args(d)
        self.locls = lcls if lcls else {}
        LOGGER.debug('    end read function: %s %s(...)', self.type, self.name)


    #--------------------
    #   Writer for pxd file
    #--------------------
    def write(self, fo, indent=0):
        lcls = []
        for k in sorted(self.locls.keys()):
            l = self.locls[k]
            lcl = '%s = %s' % (l.name, l.type)
            lcls.append(lcl)
        if lcls:
            fmt = '{indent}@cython.locals ({lcls})\n'
            s = fmt.format(indent=' '*indent, lcls='%s' % ', '.join(lcls))
            fo.write(s)

        args = []
        for a in self.args:
            arg = ''
            if a.type: arg += '%s ' % a.type
            if a.name: arg += '%s'  % a.name
            if a.val is not PXVariable.ValUndefined:
                if isinstance(a.val, (str, unicode)) and a.val[0:12] == '__conflict__':
                    arg += a.val
                else:
                    arg += '=*'
            args.append(arg)
        fmt = '{indent}cpdef {type:12s} {name:16s}({args})\n'
        s = fmt.format(indent=' '*indent, type=self.type, name=self.name, args='%s' % ', '.join(args))
        fo.write(s)


if __name__ == "__main__":
    def main(opt_args=None):
        src = """
def test(i):
    a, b = 0, 0
    for c, d in zip(range(10), range(10)):
       print c
    return True
"""
        tree = ast.parse(src)

        f = PXFunction()
        f.visit(tree)

        f.write(sys.stdout)

    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
    LOGGER.setLevel(logging.DEBUG)

    main()
