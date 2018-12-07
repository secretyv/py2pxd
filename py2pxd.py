#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
py2pxd
Extract cython pxd information from python .py files
"""

import ast
import optparse
import os
import sys
try:
    import hashlib
    HashlibMD5 = hashlib.md5
except ImportError:
    import md5
    HashlibMD5 = md5.new
import logging

import py2pxd_ as PX

LOGGER = logging.getLogger("INRS.IEHSS.Python.cython")

def xeqOneFile(fin, fout):
    """
    Treat one python file. Manages backup and update.
    """
    fbck = '.'.join([fout, 'bak'])        # Backup
    ftmp = '.'.join([fout, 'new'])        # New file

    # ---  Build parse tree
    src = ''.join(open(fin, 'rt').readlines())
    tree = ast.parse(src)

    # ---  Transfer parse tree
    #LOGGER.setLevel(logging.DEBUG)
    m0 = PX.PXModule()
    m0.visit(tree)

    # ---  Read structure from file
    m1 = PX.PXModule()
    try:
        with open(fout, 'rt') as fi:
            m1.read(fi)
    except IOError:
        pass

    # ---  Merge structures
    m0.merge(m1)
    #return

    # ---  Write to new file
    with open(ftmp, 'wt') as fo:
        m0.write(fo)

    # ---  Manage backup and update
    if os.path.isfile(ftmp):
        if os.path.isfile(fout):
            lh = len(PX.HEADER)
            tmp_fic = file(ftmp, 'rb')
            out_fic = file(fout, 'rb')
            tmp_md5 = HashlibMD5(tmp_fic.read()[lh:])
            out_md5 = HashlibMD5(out_fic.read()[lh:])
            tmp_fic.close()
            out_fic.close()
            if tmp_md5.digest() != out_md5.digest():
                if os.path.isfile(fbck): os.remove(fbck)
                os.renames(fout, fbck)
                os.renames(ftmp, fout)
                LOGGER.info(' --> Updating %s', fout)
            else:
                os.remove(ftmp)
        else:
            os.renames(ftmp, fout)
            LOGGER.info(' --> Creating %s', fout)


def main(opt_args=None):
    LOGGER.info('%s %s', PX.__package__, PX.__version__)

    # ---  Define options
    usage  = '%s [options]' % __package__
    parser = optparse.OptionParser(usage)
    parser.add_option("-v", "--verbose", dest="vrb", default=False, action="store_true",
                      help="increase verbosity")
    parser.add_option("-i", "--fi", "--input", dest="inp", default=None,
                      help="input file to cythonize", metavar="input_path")
    parser.add_option("-o", "--fo", "--output", dest="out", default=None,
                      help="pxd output file. Defaults to input_path.pxd", metavar="output_path")

    # ---  Parse options
    if not opt_args: opt_args = sys.argv[1:]
    options, _ = parser.parse_args(opt_args)
    if options.vrb:
        LOGGER.setLevel(logging.DEBUG)
    if not options.inp:
        parser.print_help()
        return
    if not options.out:
        options.out = os.path.splitext(options.inp)[0] + '.pxd'
        #parser.print_help()
        #return

    # --- Execute
    LOGGER.info('%s --> %s', options.inp, options.out)
    xeqOneFile(options.inp, options.out)


if __name__ == "__main__":
    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
    LOGGER.setLevel(logging.INFO)

    main()
