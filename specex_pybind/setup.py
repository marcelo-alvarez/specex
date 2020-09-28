#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, division, print_function
#
# Standard imports
#
import glob
import os
import sys
import shutil
#
# setuptools' sdist command ignores MANIFEST.in
#
from distutils.command.sdist import sdist as DistutilsSdist
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.egg_info import egg_info
from distutils.command.clean import clean
from distutils.errors import CompileError
#
# DESI support code.
#
# If this code is being run within the readthedocs environment, then we
# need special steps.
#
# Longer story:  desimodel and desitarget are fiberassign build requirements
# but these are not pip installable from a requirements file, due to the way
# that pip handles recursive requirements files and the fact that desiutil is
# required for obtaining even basic package info (egg_info).  Since this is
# such a specialized case, we just check if this is running on readthedocs
# and manually pip install things right here.
#
'''
try:
    import desiutil
except ImportError:
    if os.getenv('READTHEDOCS') == 'True':
        import subprocess as sp
        dutil = \
            'git+https://github.com/desihub/desiutil.git@master#egg=desiutil'
        dmodel = \
            'git+https://github.com/desihub/desimodel.git@master#egg=desimodel'
        dtarget = \
            'git+https://github.com/desihub/desitarget.git@master#egg=desitarget'
        sp.check_call(['pip', 'install', dutil])
        sp.check_call(['pip', 'install', dmodel])
        sp.check_call(['pip', 'install', dtarget])
    else:
        raise
'''

class dummy_cmdclass():
    pass

#from desiutil.setup import DesiTest, DesiVersion, get_version
#
# Begin setup
#
setup_keywords = dict()
#
# THESE SETTINGS NEED TO BE CHANGED FOR EVERY PRODUCT.
#
setup_keywords['name'] = 'specex'
setup_keywords['description'] = 'DESI PSF Fit'
setup_keywords['author'] = 'DESI Collaboration'
setup_keywords['author_email'] = 'desi-data@desi.lbl.gov'
setup_keywords['license'] = 'BSD'
setup_keywords['url'] = 'https://github.com/desihub/specex'
#
# END OF SETTINGS THAT NEED TO BE CHANGED.
#
# pkg_version = get_version(setup_keywords['name']) 
pkg_version = 'dummy-version-string' # need to fix so get_version returns 
setup_keywords['version'] = pkg_version
cpp_version_file = os.path.join("src", "_version.h")
with open(cpp_version_file, "w") as f:
    f.write('// Generated by setup.py -- DO NOT EDIT THIS\n')
    f.write('const static std::string package_version("{}");\n\n'
            .format(pkg_version))
#
# Use README.rst as long_description.
#
setup_keywords['long_description'] = ''
if os.path.exists('README.rst'):
    with open('README.rst') as readme:
        setup_keywords['long_description'] = readme.read()
#
# Set other keywords for the setup function.  These are automated, & should
# be left alone unless you are an expert.
#
# Treat everything in bin/ except *.rst as a script to be installed.
#
if os.path.isdir('bin'):
    setup_keywords['scripts'] = [fname for fname in
                                 glob.glob(os.path.join('bin', '*'))
                                 if not os.path.basename(fname)
                                 .endswith('.rst')]
setup_keywords['provides'] = [setup_keywords['name']]
setup_keywords['requires'] = ['Python (>3.4.0)']
# setup_keywords['install_requires'] = ['Python (>2.7.0)']
setup_keywords['zip_safe'] = False
setup_keywords['use_2to3'] = False
setup_keywords['packages'] = find_packages('py')
setup_keywords['package_dir'] = {'': 'py'}
#setup_keywords['cmdclass'] = {'version': DesiVersion, 'test': DesiTest,
#                              'sdist': DistutilsSdist}
setup_keywords['cmdclass'] = {'version' : dummy_cmdclass}
test_suite_name = \
    '{name}.test.{name}_test_suite.{name}_test_suite'.format(**setup_keywords)
setup_keywords['test_suite'] = test_suite_name

# Autogenerate command-line scripts.
#
# setup_keywords['entry_points'] =
# {'console_scripts':['desiInstall = desiutil.install.main:main']}
#
# Add internal data directories.
#
# setup_keywords['package_data'] = {'specex': ['data/*',]}

# Add a custom clean command that removes in-tree files like the
# compiled extension.

class RealClean(clean):
    def run(self):
        super().run()
        clean_files = [
            "./build",
            "./dist",
            "py/specex/_internal*",
            "py/specex/__pycache__",
            "py/specex/test/__pycache__",
            "./*.egg-info",
            "py/*.egg-info"
        ]
        for cf in clean_files:
            # Make paths absolute and relative to this path
            apaths = glob.glob(os.path.abspath(cf))
            for path in apaths:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
        return


# These classes allow us to build a compiled extension that uses pybind11.
# For more details, see:
#
#  https://github.com/pybind/python_example
#

# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689


def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    devnull = None
    oldstderr = None
    try:
        with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
            f.write('int main (int argc, char **argv) { return 0; }')
            try:
                devnull = open('/dev/null', 'w')
                oldstderr = os.dup(sys.stderr.fileno())
                os.dup2(devnull.fileno(), sys.stderr.fileno())
                compiler.compile([f.name], extra_postargs=[flagname])
            except CompileError:
                return False
            return True
    finally:
        if oldstderr is not None:
            os.dup2(oldstderr, sys.stderr.fileno())
        if devnull is not None:
            devnull.close()


def cpp_flag(compiler):
    """Return the -std=c++[11/14] compiler flag.

    The c++14 is prefered over c++11 (when it is available).
    """
    if has_flag(compiler, '-std=c++14'):
        return '-std=c++14'
    elif has_flag(compiler, '-std=c++11'):
        return '-std=c++11'
    else:
        raise RuntimeError('Unsupported compiler -- at least C++11 support '
                           'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }

    if sys.platform.lower() == 'darwin':
        c_opts['unix'] += ['-stdlib=libc++', '-mmacosx-version-min=10.7']

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        linkopts = []
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' %
                        self.distribution.get_version())
            opts.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
            if has_flag(self.compiler, '-fopenmp'):
                opts.append('-fopenmp')
                linkopts.append('-fopenmp')
            if sys.platform.lower() == 'darwin':
                linkopts.append('-stdlib=libc++')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' %
                        self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args.extend(opts)
            ext.extra_link_args.extend(linkopts)
        build_ext.build_extensions(self)

spec_incdir =  "/global/common/software/desi/cori/desiconda/20200801-1.4.0-spec//aux/include"

spec_libdir = "/global/common/software/desi/cori/desiconda/20200801-1.4.0-spec//aux/lib"

#spec_incdir = "./"
#spec_libdir = "./"
#spec_libs   = ""
#g++  -O3 -fPIC -pthread -fPIC -DPIC -fopenmp -I/global/common/software/desi/cori/desiconda/20200801-1.4.0-spec//aux/include -I/global/common/software/desi/cori/desiconda/20200801-1.4.0-spec//aux/include  -I/global/common/software/desi/cori/desiconda/20200801-1.4.0-spec//aux/include -I. -Wuninitialized -Wunused-value -Wunused-variable -I. -fPIC -o specex_desi_main.o -c specex_desi_main.cc
ext_modules = [
    Extension(
        'specex._internal',
        [
            'src/mymath.cpp',
            'src/myargs.cpp',
            'src/ext.cpp',
            'src/specex_desi_main.cc',
            'src/_pyspecex.cpp'
            #'src/',
            #'src/',
            #'src/',
            #'src/',
        ],
        include_dirs=[
            'src',
            spec_incdir
        ],
        library_dirs=[
            spec_libdir
        ],
        libraries=[
            "harp",
            "boost_regex-mt",
            "boost_program_options-mt",
            "boost_serialization-mt"
        ],
        extra_compile_args=[
            '-w'
        ],
        language='c++'
    ),
]

setup_keywords['ext_modules'] = ext_modules
#setup_keywords['cmdclass']['build_ext'] = BuildExt
setup_keywords['cmdclass']['clean'] = RealClean

#
# Run setup command.
#
setup(**setup_keywords)
