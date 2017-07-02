s3sfe
=====

.. image:: https://img.shields.io/pypi/v/s3sfe.svg?maxAge=2592000
   :target: https://pypi.python.org/pypi/s3sfe
   :alt: pypi version

.. image:: https://img.shields.io/github/forks/jantman/s3sfe.svg
   :alt: GitHub Forks
   :target: https://github.com/jantman/s3sfe/network

.. image:: https://img.shields.io/github/issues/jantman/s3sfe.svg
   :alt: GitHub Open Issues
   :target: https://github.com/jantman/s3sfe/issues

.. image:: https://secure.travis-ci.org/jantman/s3sfe.png?branch=master
   :target: http://travis-ci.org/jantman/s3sfe
   :alt: travis-ci for master branch

.. image:: https://codecov.io/github/jantman/s3sfe/coverage.svg?branch=master
   :target: https://codecov.io/github/jantman/s3sfe?branch=master
   :alt: coverage report for master branch

.. image:: https://readthedocs.org/projects/s3sfe/badge/?version=latest
   :target: https://readthedocs.org/projects/s3sfe/?badge=latest
   :alt: sphinx documentation for latest release

.. image:: http://www.repostatus.org/badges/latest/wip.svg
   :alt: Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.
   :target: http://www.repostatus.org/#wip

s3sfe (S3 Sync Filelist Encrypted) Sync a list of files to S3, using server-side encryption with customer-provided keys.

Introduction
------------

This is a quick script I wrote for my own purposes. It's not terribly well tested,
and it serves a small niche use case. If you're looking to securely sync your
backups to S3 or another offsite storage, I'd highly encourage you to look into the
other options.

My use case is relatively simple:

* I want to sync just some files from my backups to S3; a specific whitelist of
  files and directories.
* I don't want to keep history, I just want the latest versions somewhere offsite.
* I want to use `S3 Server-Side Encryption with Customer-Provided Encryption Keys (SSE-C) <http://docs.aws.amazon.com/AmazonS3/latest/dev/ServerSideEncryptionCustomerKeys.html>`_; I'm fine keeping the key on my computer, because if someone can get it, they can get the original files too. I'm not worried about Amazon snooping on my data. I'm not concerned with anyone being able to access the filenames or metadata. All I'm really concerned about is that if a malicious party gets access to my AWS account, they don't also implicitly get the file contents.

This tool takes a list of files or directories on the local filesystem and syncs them to S3, using server-side encryption. It uses the files' md5sums to only upload files that differ from what's already in S3.

Requirements
------------

* Python 2.7 or 3.3+ (currently tested with 2.7, 3.3+ and developed with 3.6)
* Python `VirtualEnv <http://www.virtualenv.org/>`_ and ``pip`` (recommended installation method; your OS/distribution should have packages for these)

Installation
------------

It's recommended that you install into a virtual environment (virtualenv /
venv). See the `virtualenv usage documentation <http://www.virtualenv.org/en/latest/>`_
for information on how to create a venv.

.. code-block:: bash

    pip install s3sfe

Configuration
-------------

s3sfe takes all of its configuration via command-line options. It does, however,
expect a few elements of configuration to be present on the system:

* Your AWS Credentials must be available to the program in one of the `methods supported by boto3 <http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials>`_, typically either environment variables or one of the supported credentials files (``~/.aws/credentials`` or ``~/.aws/config``) or boto configuration files (``~/.boto`` or ``/etc/boto.cfg``).
* Your encryption key for `S3 Server-Side Encryption with Customer-Provided Encryption Keys (SSE-C) <http://docs.aws.amazon.com/AmazonS3/latest/dev/ServerSideEncryptionCustomerKeys.html>`_ must be stored in a file readable by this program. This must be a 256-bit AES256 key, stored in binary format.

Usage
-----

To backup: ``s3sfe --help``

To restore: ``s3sfe-restore --help``

Bugs and Feature Requests
-------------------------

Bug reports and feature requests are happily accepted via the `GitHub Issue Tracker <https://github.com/jantman/s3sfe/issues>`_. Pull requests are
welcome. Issues that don't have an accompanying pull request will be worked on
as my time and priority allows.

Development
===========

To install for development:

1. Fork the `s3sfe <https://github.com/jantman/s3sfe>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv s3sfe
    $ cd s3sfe && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/s3sfe.git@BRANCHNAME#egg=s3sfe
    $ cd src/s3sfe

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

Testing
-------

Testing is done via `pytest <http://pytest.org/latest/>`_, driven by `tox <http://tox.testrun.org/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

Release Checklist
-----------------

1. Open an issue for the release; cut a branch off master for that issue.
2. Confirm that there are CHANGES.rst entries for all major changes.
3. Ensure that Travis tests passing in all environments.
4. Ensure that test coverage is no less than the last release (ideally, 100%).
5. Increment the version number in s3sfe/version.py and add version and release date to CHANGES.rst, then push to GitHub.
6. Confirm that README.rst renders correctly on GitHub.
7. Upload package to testpypi:

   * Make sure your ~/.pypirc file is correct (a repo called ``test`` for https://testpypi.python.org/pypi)
   * ``rm -Rf dist``
   * ``python setup.py register -r https://testpypi.python.org/pypi``
   * ``python setup.py sdist bdist_wheel``
   * ``twine upload -r test dist/*``
   * Check that the README renders at https://testpypi.python.org/pypi/s3sfe

8. Create a pull request for the release to be merged into master. Upon successful Travis build, merge it.
9. Tag the release in Git, push tag to GitHub:

   * tag the release. for now the message is quite simple: ``git tag -s -a X.Y.Z -m 'X.Y.Z released YYYY-MM-DD'``
   * push the tag to GitHub: ``git push origin X.Y.Z``

11. Upload package to live pypi:

    * ``twine upload dist/*``

10. make sure any GH issues fixed in the release were closed.
