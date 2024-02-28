#!/usr/bin/env python3

# uhd_ubuntu_deb.py
# This script is used to generate UHD dsc, changes, and source archives for upload to Launchpad.
# After dsc generation, pbuilder is called to build the debs. This sets up an envionment similar to
# the Launchpad build process. To build the dsc you must have pbuilder, debootstrap, and devscripts
# installed and have run:
#
# pbuilder create --debootstrapopts --variant=buildd --distribution=<target distro>
#
# See here for more on pbuilder: https://wiki.ubuntu.com/PbuilderHowto

import argparse
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile

supported_ubuntu_releases = ["bionic", "focal", "jammy"]
#tar_command = "tar --exclude='.git*' --exclude='./debian' --exclude='*.swp' --exclude='fpga' --exclude='build' --exclude='./images/*.pyc' --exclude='./images/uhd-*' --exclude='tags' --exclude='.ci' --exclude='.clang*' -cJf {}/uhdpv_{}.orig.tar.xz ."
#tar_command = "tar --exclude='.git*' --exclude='build' --exclude='.buildkite' --exclude='.ci' --exclude='.clang*' -cJf {}/gnuradiopv_{}.orig.tar.xz ."
tar_command = "tar --exclude='.git*' --exclude='build' --exclude='.buildkite' --exclude='.ci' -cJf {}/gnuradiopv_{}.orig.tar.xz ."
debuild_command = "debuild -S -i -sa"
debuild_nosign = " -uc -us"
mk_build_command = "sudo mk-build-deps"
mk_build_arg = " -i --tool 'apt-get -f --yes'"
copy_command = "cp -r {}/gnuradiopv_{}.orig.tar.xz {}"


def main(args):
    if not pathlib.Path("docs").exists():
        print("Check path. This script must be run on gnuradio base path")
        sys.exit(1)
    if not args.release in supported_ubuntu_releases:
        print("Unsupported release selected. Supported releases are {}".format(
            supported_ubuntu_releases))
        sys.exit(1)

    # Determine GRC version number
    print("Determining gnuradio version number...")
    grc_version = ""
    orig_release = ""
    with open("cmake/debian-gnuradio-pv/changelog") as cl:
        first_line = cl.readline()
        grc_version = re.findall("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*", first_line)
        if len(grc_version) != 1:
            print("grc_version in changelog malformed. Check cmake/debian-gnuradio-pv/changelog")
            sys.exit(1)
        grc_version = grc_version[0]
        orig_release = re.findall("[A-Za-z_]*;", first_line)
        if len(orig_release) != 1:
            print(
                "orig_release in changelog malformed. Check cmake/debian-gnuradio-pv/changelog")
            sys.exit(1)
        orig_release = orig_release[0].replace(";", "")

    # Compress GRC source
    if pathlib.Path(args.buildpath).exists():
        shutil.rmtree(args.buildpath)
    os.mkdir(args.buildpath)
    if not args.tarfile:
        print("Compressing GRC Source...")
        result = subprocess.run(shlex.split(
            tar_command.format(args.buildpath, grc_version)))
        if result.returncode:
            print("Compressing source failed")
            sys.exit(result.returncode)
    else:
        print("Retrieving existing GRC Source...")
        result = subprocess.run(shlex.split(
            copy_command.format(args.tarfile, grc_version, args.buildpath)))
        if result.returncode:
            print("Retrieving source failed")
            sys.exit(result.returncode)

    # Extract GRC source to build folder
    print("Extractubg GRC source to build folder...")
    grc_deb_build_path = pathlib.Path(
        args.buildpath, "gnuradiopv-{}".format(grc_version))
    if grc_deb_build_path.exists():
        shutil.rmtree(grc_deb_build_path)
    with tarfile.open(args.buildpath + "/gnuradiopv_{}.orig.tar.xz".format(grc_version), "r:xz") as uhd_archive:
        uhd_archive.extractall(path=grc_deb_build_path)

    # Copy debian build files to build folder
    print("Copying debian build files to the build folder...")
    shutil.copytree("cmake/debian-gnuradio-pv", grc_deb_build_path / "debian")
    #shutil.copy2("host/utils/uhd-usrp.rules",
    #             grc_deb_build_path / "debian/uhd-host.udev")
    #with open(grc_deb_build_path / "debian/uhd-host.manpages", "w") as man_file:
    #    for file in grc_deb_build_path.glob("host/docs/*.1"):
    #        man_file.write(os.path.relpath(file, grc_deb_build_path) + "\n")
    #    man_file.write("\n")
    #for file in grc_deb_build_path.glob("debian/*.in"):
    #    os.remove(file)

    # Modify changelog for selected release
    print("Modifying changelog for the selected release...")
    with open(grc_deb_build_path / "debian/changelog", 'r+') as cl:
        cl_text = cl.read()
        cl_text = re.sub(orig_release, args.release, cl_text)
        cl_text = re.sub(
            "0ubuntu1", "0ubuntu1~{}1".format(args.release), cl_text)
        cl.seek(0)
        cl.write(cl_text)
        cl.truncate()

    # Generate dsc file
    result = ""
    # result1 = ""
    print("Running debuild / dsc generation")
    # result1 = subprocess.run(shlex.split(
    #         mk_build_command + mk_build_arg), cwd=grc_deb_build_path)
    # if result1.returncode:
    #     print("mk-build-deps failed")
    #     sys.exit(result1.returncode)
    if args.sign:
        result = subprocess.run(shlex.split(
            debuild_command), cwd=grc_deb_build_path)
    else:
        result = subprocess.run(shlex.split(
            debuild_command + debuild_nosign), cwd=grc_deb_build_path)
    if result.returncode:
        print("debuild / dsc generation failed")
        sys.exit(result.returncode)

    # Build debs using dsc
    if not args.nobuild:
        print("Building deb with dsc using pbuilder for {}".format(args.release))
        os.mkdir(args.buildpath + "/result")
        result = subprocess.run(shlex.split(
           "sudo pbuilder build --buildresult ./result gnuradiopv_{}-0ubuntu1~{}1.dsc".format(grc_version, args.release)), cwd=args.buildpath)
        if result.returncode:
           print("pbuilder failed")
           sys.exit(result.returncode)

    # Upload dsc to Launchpad
    if args.upload:
        if not args.sign:
            print("Uploading requires signing. Add --sign.")
            sys.exit(1)
        result = subprocess.run(shlex.split(
            "dput -f ppa:sfen/uhdpv gnuradiopv_{}-0ubuntu1~{}1_source.changes".format(grc_version, args.release)), cwd=args.buildpath)
        if result.returncode:
            print("PPA upload failed")
            sys.exit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tarfile", type=str,
                        help="Specify existing tar file")
    parser.add_argument("--sign", action='store_true',
                        help="Signs files with GPG key. Not required for test builds")
    parser.add_argument("--upload", action='store_true',
                        help="Uploads to launchpad. Requires--sign")
    parser.add_argument("--nobuild", action='store_true',
                        help="Disables building using pbuilder")
    parser.add_argument("--buildpath", type=str, required=True,
                        help="Output path for build files. "
                             "Will get nuked before creating packages.")
    parser.add_argument("release", type=str,
                        help="Ubuntu release version. This must match pbuilder create --distribution if building.")
    args = parser.parse_args()
    main(args)
