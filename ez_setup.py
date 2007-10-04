#!/usr/bin/env python
"""Bootstrap setuptools installation

If you want to use setuptools in your package's setup.py, just include this
file in the same directory with it, and add this to the top of your setup.py::

    from ez_setup import use_setuptools
    use_setuptools()

If you want to require a specific version of setuptools, set a download
mirror, or use an alternate download directory, you can do so by supplying
the appropriate options to ``use_setuptools()``.

This file can also be run as a script to install or upgrade setuptools.
"""
import subprocess, sys
DEFAULT_VERSION = "0.6c7"
DEFAULT_URL     = "http://pypi.python.org/packages/%s/s/setuptools/" % sys.version[:3]

md5_data = {
    'setuptools-0.6c7-py2.3.egg': '209fdf9adc3a615e5115b725658e13e2',
    'setuptools-0.6c7-py2.4.egg': '5a8f954807d46a0fb67cf1f26c55a82e',
    'setuptools-0.6c7-py2.5.egg': '45d2ad28f9750e7434111fde831e8372',
}

import sys, os

def _validate_md5(egg_name, data):
    if egg_name in md5_data:
        from md5 import md5
        digest = md5(data).hexdigest()
        if digest != md5_data[egg_name]:
            print >>sys.stderr, (
                "md5 validation of %s failed!  (Possible download problem?)"
                % egg_name
            )
            sys.exit(2)
    return data

def setuptools_is_loaded():
    return 'pkg_resources' in sys.modules or 'setuptools' in sys.modules

def get_setuptools_version():
    sub = subprocess.Popen([sys.executable, "-c", "import setuptools;print setuptools.__version__"], stdout=subprocess.PIPE)
    return sub.stdout.read().strip()

def setuptools_is_new_enough(required_version):
    """Return True if setuptools is already installed and has a version
    number >= required_version."""
    verstr = get_setuptools_version()
    try:
        import pkg_resources
    except ImportError:
        # Well then I guess it is definitely not new enough.
        return False
    try:
        ver = pkg_resources.parse_version(verstr)
        newenough = ver and ver >= pkg_resources.parse_version(required_version)
    finally:
        del sys.modules['pkg_resources']
    return newenough

def use_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    min_version=None, download_delay=15
):
    """Automatically find/download setuptools and make it available on sys.path

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end with
    a '/').  `to_dir` is the directory where setuptools will be downloaded, if
    it is not already available.  If `download_delay` is specified, it should
    be the number of seconds that will be paused before initiating a download,
    should one be required.  If an older version of setuptools is installed,
    this routine will print a message to ``sys.stderr`` and raise SystemExit in
    an attempt to abort the calling script.
    """
    if min_version is None:
        min_version = version
    if setuptools_is_loaded():
        # setuptools is installed, but can't be upgraded, so just version
        # check (using pkg_resources) and exit if it's not a good enough
        # version.
        if not setuptools_is_new_enough(min_version):
            print >>sys.stderr, (
            "The required version of setuptools (>=%s) is not installed, and\n"
            "can't be installed while this script is running. Please install\n"
            "a more recent version first.\n\n(Currently using %r)"
            ) % (min_version, get_setuptools_version())
            sys.exit(2)
    else:
        if not setuptools_is_new_enough(min_version):
            egg = download_setuptools(version, download_base, to_dir, download_delay)
            sys.path.insert(0, egg)
            import setuptools; setuptools.bootstrap_install_from = egg

def download_setuptools(
    version=DEFAULT_VERSION, download_base=DEFAULT_URL, to_dir=os.curdir,
    delay = 15
):
    """Download setuptools from a specified location and return its filename

    `version` should be a valid setuptools version number that is available
    as an egg for download under the `download_base` URL (which should end
    with a '/'). `to_dir` is the directory where the egg will be downloaded.
    `delay` is the number of seconds to pause before an actual download attempt.
    """
    import urllib2, shutil
    egg_name = "setuptools-%s-py%s.egg" % (version,sys.version[:3])
    url = download_base + egg_name
    saveto = os.path.join(to_dir, egg_name)
    src = dst = None
    if not os.path.exists(saveto):  # Avoid repeated downloads
        try:
            from distutils import log
            if delay:
                log.warn("""
---------------------------------------------------------------------------
This script requires setuptools version %s to run (even to display
help).  I will attempt to download it for you (from
%s), but
you may need to enable firewall access for this script first.
I will start the download in %d seconds.

(Note: if this machine does not have network access, please obtain the file

   %s

and place it in this directory before rerunning this script.)
---------------------------------------------------------------------------""",
                    version, download_base, delay, url
                ); from time import sleep; sleep(delay)
            log.warn("Downloading %s", url)
            src = urllib2.urlopen(url)
            # Read/write all in one block, so we don't create a corrupt file
            # if the download is interrupted.
            data = _validate_md5(egg_name, src.read())
            dst = open(saveto,"wb"); dst.write(data)
        finally:
            if src: src.close()
            if dst: dst.close()
    return os.path.realpath(saveto)

def main(argv, version=DEFAULT_VERSION):
    """Install or upgrade setuptools and EasyInstall"""

    if setuptools_is_loaded():
        # setuptools is installed, but can't be upgraded, so just version
        # check (using pkg_resources) and exit if it's not a good enough
        # version.
        if not setuptools_is_new_enough(version):
            print >>sys.stderr, (
            "The required version of setuptools (>=%s) is not installed, and\n"
            "can't be installed while this script is running. Please install\n"
            "a more recent version first.\n\n(Currently using %r)"
            ) % (version, get_setuptools_version())
            sys.exit(2)
    else:
        if setuptools_is_new_enough(version):
            if argv:
                from setuptools.command.easy_install import main
                main(argv)
            else:
                print "Setuptools version",version,"or greater has been installed."
                print '(Run "ez_setup.py -U setuptools" to reinstall or upgrade.)'
        else:
            egg = None
            try:
                egg = download_setuptools(version, delay=0)
                sys.path.insert(0,egg)
                from setuptools.command.easy_install import main
                return main(list(argv)+[egg])   # we're done here
            finally:
                if egg and os.path.exists(egg):
                    os.unlink(egg)

def update_md5(filenames):
    """Update our built-in md5 registry"""

    import re
    from md5 import md5

    for name in filenames:
        base = os.path.basename(name)
        f = open(name,'rb')
        md5_data[base] = md5(f.read()).hexdigest()
        f.close()

    data = ["    %r: %r,\n" % it for it in md5_data.items()]
    data.sort()
    repl = "".join(data)

    import inspect
    srcfile = inspect.getsourcefile(sys.modules[__name__])
    f = open(srcfile, 'rb'); src = f.read(); f.close()

    match = re.search("\nmd5_data = {\n([^}]+)}", src)
    if not match:
        print >>sys.stderr, "Internal error!"
        sys.exit(2)

    src = src[:match.start(1)] + repl + src[match.end(1):]
    f = open(srcfile,'w')
    f.write(src)
    f.close()


if __name__=='__main__':
    if '--md5update' in sys.argv:
        sys.argv.remove('--md5update')
        update_md5(sys.argv[1:])
    else:
        main(sys.argv[1:])
