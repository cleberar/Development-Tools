#!/usr/bin/python -t
# -*- mode: Python; indent-tabs-mode: nil; -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# Updated changelog for the creation of the SVN log
#

import errno, os, sys
import commands
import re
import time
import xml.etree.ElementTree as et
from optparse import OptionParser

class BumpSpecError(Exception):
    pass

class SpecFile:
    def __init__(self, filename, verbose=False):
            self.verbose = verbose
            self.filename = filename
            f = open(filename,"r")
            self.lines = f.readlines()
            f.close()

    def bumpRelease(self):
            bump_patterns = [(re.compile(r"^Release\s*:\s*(\d+.*)", re.I), self.increase), 
                             (re.compile(r"^%define\s+rel\s+(\d+.*)"), self.increase), 
                             (re.compile(r"^%define\s+release\s+(\d+.*)", re.I), self.increase), 
                             (re.compile(r"^Release\s*:\s+%release_func\s+(\d+.*)"), self.increase),
                             (re.compile(r"^%define\s+baserelease\s+(\d+.*)"), self.increase),
                            ]
            skip_pattern = re.compile(r"\$Revision:")
            for i in range(len(self.lines)):
                    if skip_pattern.search(self.lines[i]):
                            continue
                    for bumpit, bumpit_func in bump_patterns:
                            (self.lines[i], n) = bumpit.subn(bumpit_func, self.lines[i], 1)
                            if n:  # bumped
                                    return

            # Here, no line matched at all.
            # Happens with macro-overloaded spec files e.g.
            # Bump ^Release: ... line least-insignificant.
            for i in range(len(self.lines)):
                    if self.lines[i].startswith('Release:'):
                            old = self.lines[i][len('Release:'):].rstrip()
                            new = self.increaseFallback(old)
                            if self.verbose:
                                    self.debugdiff(old, new)
                            self.lines[i] = self.lines[i].replace(old, new)
                            return

            if self.verbose:
                    print >> sys.stderr, 'ERROR: No release value matched:', self.filename
                    sys.exit(1)

    def addChangelogEntry(self, evr, entry, email, svn):
            if len(evr):
                    evrstring = ' - %s' % evr
            else:
                    evrstring = ''
            changematch = re.compile(r"^%changelog")
            date = time.strftime("%a %b %d %Y",   time.localtime(time.time()))
            newchangelogentry = "%changelog\n* "+date+" "+email+evrstring

            svnlog = False

            for i in range(len(self.lines)):
                    if(changematch.match(self.lines[i])):
                            self.lines[i] = newchangelogentry
                            if svn:
                                lastchange = self.lines[i + 1]
                                svnlog = self.changeSVN(svn, lastchange)

                            if (svnlog) :
                                self.lines[i] += svnlog+"\n\n"
                            else :
                                self.lines[i] += "\n" + entry+"\n\n"
                            break

    # update ChangeLog  SVN logs
    def changeSVN(self, svn ,lastchange):

        listlastchange = lastchange.replace("*", "").strip().split(" ");

        now = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        last = time.strftime("%Y-%m-%d", time.strptime(str(int(listlastchange[2]) + 1) + " " + listlastchange[1] + " " + listlastchange[3] , "%d %b %Y"))

        svnlog = 'svn log -r "{%s}:{%s}" --xml %s' % (now, last, svn)
        # obtemos o log do SVN
        try:
            svnXML = commands.getoutput(svnlog)
            root = et.fromstring(svnXML)
        except :
            return ""

        changelog = ""
        listRevision = []
        for child in root:

            revision = child.attrib['revision'].strip()
            msg = child.find('msg').text

            if (listRevision.count(revision) > 0):
                continue

            listRevision.append(revision)
            if not msg :
                continue
            else :

                msg = msg.strip()
                ticket = re.search('[#[0-9]*]', msg)

                if re.search(r"\New Package", msg) or re.search(r"\New Release", msg) or re.search(r"\New SPEC", msg) :
                    continue

                elif ticket :

                    lines = msg.split("\n")
                    countline = len(lines)
                    for i in range(countline):
                        line = lines[i]
                        if line :
                            currentTicket = re.search('[#[0-9]*]', line)
                            line = line.replace(currentTicket.group(), "")
                            line = line.strip()

                            currentTicket = currentTicket.group().replace("[", "").replace("]", "")
                            changelog += '\n- %s (%s)' % (line, currentTicket)

        return changelog

    def increaseMain(self, release):
            return '{0}'.format(float(release) + 0.1)

    def increaseFallback(self, release):
            """bump at the very-right or add .1 as a last resort"""

            relre = re.compile(r'(?P<prefix>.+\.)(?P<post>\d+$)')
            relmatch = relre.search(release)
            if relmatch:
                    prefix = relmatch.group('prefix')
                    post = relmatch.group('post')
                    new = prefix+self.increaseMain(post)
            else:
                    new = release.rstrip()+'.1'
            return new


    def increase(self, match):
            old = match.group(1)  # only the release value
            try:
                        new = self.increaseMain(old)

            except BumpSpecError:
                    new = self.increaseFallback(old)

            if self.verbose:
                    self.debugdiff(old, new)

            # group 0 is the full line that defines the release
            return match.group(0).replace(old, new)


    def writeFile(self, filename):
            f = open(filename, "w")
            f.writelines(self.lines)
            f.close()


    def debugdiff(self, old, new):
            print '-%s' % old
            print '+%s\n' % new


if __name__ == "__main__":
    usage = "Usage: %s <options> <specfile(s)>" % sys.argv[0]
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--comment", default='- rebuilt',help="changelog comment (default:- rebuilt)")
    parser.add_option("-u", "--userstring", default=None,help="user name+email string")
    parser.add_option("-v", "--verbose", default=False, action='store_true',help="more output")
    parser.add_option("-s", "--svn", default='', help="create changlog by SVN log")

    (opts, args) = parser.parse_args()

    userstring = os.getenv('RPM_PACKAGER')
    if not userstring and not opts.userstring:
            userstring = os.getenv('MAILTO')
            if not userstring:
                    print 'ERROR: Set $RPM_PACKAGER environment variable or use option -u!'
                    sys.exit(errno.EINVAL)
    if opts.userstring:
            userstring = opts.userstring

    for aspec in args:
            s = SpecFile(aspec, opts.verbose)
            s.bumpRelease()
            s.writeFile(aspec)

            # Get EVR for changelog entry.
            (epoch,ver,rel) = os.popen("LC_ALL=C rpm --specfile -q --qf '%%{epoch} %%{version} %%{release}\n' --define 'dist %%{nil}' %s | head -1" % aspec).read().strip().split(' ')
            if epoch != '(none)':
                    evr = str(epoch)+':'
            else:
                    evr = ''
            evr += ver+'-'+rel

            s.addChangelogEntry(evr, opts.comment, userstring, opts.svn)
            s.writeFile(aspec)

sys.exit(0)
