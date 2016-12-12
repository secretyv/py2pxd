#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import logging

logger = logging.getLogger("INRS.IEHSS.Python.cython.variable")

default_types = {
    type(None)   : 'object',
    type(True)   : 'bint',
    type(0)      : 'long',
    type(0.0)    : 'double',
    type(list()) : 'list',
    type(dict()) : 'dict',
    type(tuple()): 'tuple',
    type(set())  : 'set',
    type(u' ')   : 'unicode',
    type(' ')    : 'unicode',
    #
    type(ast.List()) : 'list',
    type(ast.Dict()) : 'dict',
    type(ast.Tuple()): 'tuple',
    type(ast.Set())  : 'set',
    type(ast.Str())  : 'unicode',
}

class PXVariable(object):
    class ValUndefined:
        pass

    def __init__(self):
        self.name = ''
        self.type = default_types[ type(None) ]
        self.val  = PXVariable.ValUndefined

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return '%s %s' % (self.type, self.name)
        
    def merge(self, other):
        assert self == other
        cnflct = False
        logger.debug('PXVariable.merge: %s' % (self.name))
        logger.debug('    merge type:  %s and %s' % (self.type, other.type))
        if self.type != other.type:
            if   self.type in ['']:
                if other.type not in ['']: self.type = other.type
            elif self.type in ['None']:
                if other.type not in ['', 'None']: self.type = other.type
            elif self.type in ['object']:
                if other.type not in ['', 'None', 'object']: self.type = other.type
            elif other.type in ['', 'None', 'object']:
                pass
            elif self.type in ['long'] and other.type in ['size_t']:
                logger.debug('    promoting %s to %s' % (self.type, other.type))
                self.type = other.type
            else:
                self.type = '__conflict__type__: "%s" "%s"' % (self.type, other.type)
                cnflct = True
        logger.debug('    merged to %s' % (self.type))
        if cnflct: logger.warn('PXVariable.merge: %s: %s' % (self.name, self.type))

        cnflct = False
        logger.debug('    merge val:  %s and %s' % (self.val, other.val))
        if self.val  != other.val:  
            if   self.val in ['']:
                if other.val not in ['', PXVariable.ValUndefined]: self.val = other.val
            elif self.val in ['None']:
                if other.val not in ['', 'None', PXVariable.ValUndefined]: self.val = other.val
            elif self.val in ['object']:
                if other.val not in ['', 'None', 'object']: self.val = other.val
            elif other.val in ['', 'None', 'object', '*', PXVariable.ValUndefined]:
                pass
            else:
                self.val = '__conflict__val__: "%s" "%s"' % (self.val, other.val)
                cnflct = True
        logger.debug('    merged to %s' % str(self.val))
        if cnflct: logger.warn('PXVariable.merge: %s: %s' % (self.name, self.type))

    #--------------------
    #   Python source code parser (ast visitors)
    #--------------------
    def doVisit(self, name, type_name = None, value = ValUndefined):
        logger.debug('PXVariable.doVisit: %s with type %s and value %s' % (name, type_name, value))
        v, t = PXVariable.ValUndefined, None
        try:
            v = ast.literal_eval(value)
            t = v
        except Exception as e:
            if isinstance(value, ast.Attribute):
                v = PXVariable.ValUndefined
                t = None    # will become 'object'
            elif value != PXVariable.ValUndefined:
                v = PXVariable.ValUndefined
                t = None    # will become 'object'
            else:
                v = PXVariable.ValUndefined
                t = type_name

        if isinstance(t, type):
            self.type = default_types[t]
        elif isinstance(t, (str, unicode)):
            try:
                self.type = default_types[t]
            except KeyError:
                self.type = t
        else:
            try:
                self.type = default_types[type(t)]
            except KeyError:
                self.type = str(t)

        self.val  = v
        self.name = name
        logger.debug('    %s as %s' % (self.name, self.val))

    #--------------------
    #   Reader for pxd files
    #--------------------
    def read_arg(self, arg):
        """
        An argument is 'type name = value'
        """
        arg = arg.strip()
        try:
            arg, v = arg.split('=')
        except:
            v = ''
        try:
            t, n = arg.split(' ')
        except:
            t, n = self.type, arg
        self.name = n.strip()
        self.type = t.strip()
        self.val  = v.strip() if v else PXVariable.ValUndefined

    def read_var(self, var):
        """
        A variable is 'name = type'
        """
        try:
            n, t = var.split('=')
        except:
            n, t = var, ''
        self.name = n.strip()
        self.type = t.strip()
        self.val  = PXVariable.ValUndefined
        

if __name__ == "__main__":
    def main(opt_args = None):
        v = PXVariable()

    streamHandler = logging.StreamHandler()
    logger.addHandler(streamHandler)
    logger.setLevel(logging.DEBUG)

    main()
