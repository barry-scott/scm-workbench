#!/usr/bin/env python
import sys
import os
import time

def if_opt( opt, yes, no ):
    if opt:
        return yes
    else:
        return no

def createRpmSpecFile( opt, spec_filename ):
    all_requires = set()
    all_build_requires = set()

    all_sources = []

    kit_xml_preferences_basename = ''

    python = '/usr/bin/python3'
    all_requires.add( 'python3' )
    all_requires.add( 'python3-qt6' )
    all_requires.add( 'subversion' )
    all_requires.add( 'python3-pysvn' )
    all_requires.add( 'git-core >= 2.7' )
    all_requires.add( 'python3-hglib' )
    all_requires.add( 'python3-GitPython' )
    all_requires.add( 'python3-qscintilla-qt6' )
    all_requires.add( 'python3-xml-preferences' )

    all_build_requires.add( 'python3' )
    all_build_requires.add( 'gettext' )
    all_build_requires.add( 'make' )

    if opt.opt_kit_xml_preferences is None:
        all_requires.add( 'python3-xml-preferences' )

    else:
        kit_xml_preferences_basename = os.path.basename( opt.opt_kit_xml_preferences )
        all_sources.append( opt.opt_kit_xml_preferences )

    fmt_spec_file = ''.join( (
                        spec_file_head,
                        spec_file_prep,
                        if_opt( kit_xml_preferences_basename != '', spec_file_prep_xml_preferences, '' ),
                        spec_file_tail) )

    fmt_spec_file = fmt_spec_file.replace( '%', '%%' )
    fmt_spec_file = fmt_spec_file.replace( './.', '%' )
    spec_vars = {'VERSION':             opt.version
                ,'RELEASE':             opt.opt_release
                ,'DATE':                time.strftime( '%a %b %d %Y' )
                ,'PYTHON':              python
                ,'SOURCES':             '\n'.join( 'Source%d: %s' % (index, os.path.basename( src )) for index, src in enumerate( all_sources, 1 ) )
                ,'REQUIRES':            '\n'.join( 'Requires: %s' % (req,) for req in sorted( all_requires ) )
                ,'BUILD_REQUIRES':      '\n'.join( 'BuildRequires: %s' % (req,) for req in sorted( all_build_requires ) )
                ,'KIT_XML_PREFERENCES': kit_xml_preferences_basename
                }
    spec_file = fmt_spec_file % spec_vars

    with open( spec_filename, 'w' ) as f:
        f.write( spec_file )

    return 0

# use ./. in place of %

spec_file_head = '''
%global debug_package %{nil} 

Name:           scm-workbench
Version:        ./.(VERSION)s
Release:        ./.(RELEASE)s%{?dist}
Summary:        SCM Workbench

License:        ASL 2.0
URL:            https://github.com/barry-scott/scm-workbench
Source0:        https://github.com/barry-scott/scm-workbench/%{name}-%{version}.tar.gz
./.(SOURCES)s

BuildArch:      noarch

./.(REQUIRES)s

./.(BUILD_REQUIRES)s

%global __python %{__python3}

%description
SCM Workbench is a GUI to easily work with Git, 
Mercurial (hg) and Subversion (svn) repositories.
'''

spec_file_prep = '''
%prep
# unpack Source0
%setup
'''

spec_file_prep_xml_preferences = '''
gunzip -c "%_sourcedir/./.(KIT_XML_PREFERENCES)s" | tar xf - -C Imports
# make build_bemacs code happy
ln -s $PWD/Imports/xml-preferences-*/Source/xml_preferences Builder
# make Scm code happy
ln -s $PWD/Imports/xml-preferences-*/Source/xml_preferences Source/Common
'''

spec_file_tail = '''
%build
echo Info: build PWD $( pwd )
true

%install
echo Info: Install PWD $( pwd )

export BUILDER_TOP_DIR=$( pwd )
export PYTHON=/usr/bin/python3

cd ${BUILDER_TOP_DIR}/Builder
./build-install-tree.sh \
    %{buildroot} \
    %{_bindir} \
    %{_datarootdir}/scm-workbench/lib \
    %{_mandir}/man1 \
    %{_datarootdir}/doc/scm-workbench \
    %{_datarootdir}/applications

%files
%defattr(0644, root, root, 0755)
%attr(755, root, root) %{_bindir}/scm-workbench
%attr(755, root, root) %{_bindir}/scm-workbench-git-callback
# include all files in the _datarootdir (includes man1 and desktop)
%{_datarootdir}

%changelog
* ./.(DATE)s Barry Scott <barry@barrys-emacs.org> - ./.(VERSION)s-./.(RELEASE)s
- Specfile create by package_workbench.py
'''
