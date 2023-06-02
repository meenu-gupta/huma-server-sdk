"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
Modified by Madoshakalaka@Github (dependency links added)
"""
# Always prefer setuptools over distutils
import os

from setuptools import setup, find_packages
from os import path

# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

__packagename__ = "py-phoenix-server"


def package_files(directory):
    paths = []
    for (filepath, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", filepath, filename))
    return paths


here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name=__packagename__,
    # Required
    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="v1.5.2",
    # Required
    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description="A Huma project",
    # Optional
    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,
    # Optional
    # Denotes that our long_description is in Markdown; valid values are
    # text/plain, text/x-rst, and text/markdown
    #
    # Optional if long_description is written in reStructuredText (rst) but
    # required for plain-text or Markdown; if unspecified, "applications should
    # attempt to render [the long_description] as text/x-rst; charset=UTF-8 and
    # fall back to text/plain if it is not valid rst" (see link below)
    #
    # This field corresponds to the "Description-Content-Type" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-content-type-optional
    long_description_content_type="text/markdown",
    # Optional (see note above)
    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url="https://github.com/huma-engineering/py-phoenix-server",
    # Optional
    # This should be your name or the name of the organization which owns the
    # project.
    author="Huma Engineering team",
    # Optional
    # This should be a valid email address corresponding to the author listed
    # above.
    author_email="dev-account@huma.com",
    # Optional
    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    # Optional
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    # Indicate who your project is intended for
    # Pick your license as you wish
    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    # These classifiers are *not* checked by 'pip install'. See instead
    # 'python_requires' below.
    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords="sample setuptools development",
    # Optional
    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=["contrib", "docs", "tests", "deploy"]),
    # Required
    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires=">=3.8.*,  <4",
    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "aenum==2.2.3",
        "aliyun-python-sdk-core==2.13.15",
        "aliyun-python-sdk-core-v3==2.13.32",
        "aliyun-python-sdk-kms==2.15.0",
        "aliyun-python-sdk-push==3.13.2",
        "amqp==2.6.1",
        "aniso8601==8.0.0",
        "apns2==0.7.1",
        "arrow==0.14.0",
        "azure-core==1.16.0",
        "azure-storage-blob==12.8.0",
        "Babel==2.9.1",
        "bcrypt==3.2.0",
        "billiard==3.6.4.0",
        "blinker==1.4",
        "boltons==20.1.0",
        "CacheControl==0.12.6",
        "cachetools==4.2.2",
        "celery==4.4.2",
        "celery-redbeat==1.0.0",
        "Cerberus==1.3.4",
        "cffi==1.14.6",
        "cfgv==3.3.0",
        "configparser==5.1.0",
        "cos-python-sdk-v5==1.9.0",
        "crcmod==1.7",
        "cryptography==3.3.2",
        "decorator==5.0.9",
        "dicttoxml==1.7.4",
        "dnspython==1.16.0",
        "exrex==0.10.5",
        "filelock==3.0.12",
        "fire==0.3.1",
        "firebase-admin==4.3.0",
        "flasgger==0.9.4",
        "Flask==2.0.0",
        "Flask-Limiter==1.2.1",
        "fluent-logger==0.9.6",
        "freezegun==0.3.15",
        "frozendict==1.2",
        "gobiko.apns==0.1.3",
        "google-api-core==1.31.0",
        "google-api-python-client==2.12.0",
        "google-auth==1.32.1",
        "google-auth-httplib2==0.1.0",
        "google-cloud-core==1.7.1",
        "google-cloud-firestore==2.1.3",
        "google-cloud-storage==1.29.0",
        "google-resumable-media==0.5.1",
        "googleapis-common-protos==1.53.0",
        "grpcio==1.38.1",
        "h2==2.6.2",
        "hpack==3.0.0",
        "httplib2==0.19.1",
        "hyper==0.7.0",
        "hyperframe==3.2.0",
        "ics==0.7",
        "identify==2.2.11",
        "isodate==0.6.0",
        "itsdangerous==2.0.1",
        "Jinja2==3.0.1",
        "jmespath==0.10.0",
        "jsonpatch==1.28",
        "jsonpath-ng==1.5.2",
        "jsonpointer==2.1",
        "jsonschema==3.2.0",
        "kombu==4.6.11",
        "limits==1.5.1",
        "MarkupSafe==2.0.1",
        "minio==5.0.8",
        "mistune==0.8.4",
        "mohawk==1.1.0",
        "mongoengine==0.20.0",
        "msgpack==0.6.2",
        "msrest==0.6.21",
        "nodeenv==1.6.0",
        "oauthlib==3.1.1",
        "onfido-python==1.2.0",
        "oss2==2.9.1",
        "pdfkit==0.6.1",
        "phonenumbers==8.12.1",
        "Pillow==9.0.1",
        "ply==3.11",
        "pre-commit==2.8.2",
        "prometheus-client==0.11.0",
        "prometheus-flask-exporter==0.18.1",
        "proto-plus==1.19.0",
        "protobuf==3.17.3",
        "pyasn1==0.4.8",
        "pyasn1-modules==0.2.8",
        "pycountry==20.7.3",
        "pycparser==2.20",
        "pycryptodome==3.10.1",
        "pydub==0.24.1",
        "pyfcm==1.4.7",
        "PyJWT==1.7.1",
        "pymongo==3.10.1",
        "pyrsistent==0.18.0",
        "python-dotenv==0.17.0",
        "python-i18n==0.3.7",
        "python-json-logger==0.1.9",
        "pytz==2021.1",
        "PyYAML==5.3.1",
        "qrcode==6.1",
        "requests==2.25.1",
        "requests-oauthlib==1.3.0",
        "rsa==4.7.2",
        "sentry-sdk==1.5.0",
        "six==1.16.0",
        "TatSu==5.6.1",
        "tenacity==8.0.0",
        "termcolor==1.1.0",
        "toml==0.10.2",
        "tomlkit==0.7.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        "twilio==6.52.0",
        "uritemplate==3.0.1",
        "validators==0.14.3",
        "vine==1.3.0",
        "virtualenv==20.4.7",
        "waitress==1.4.3",
        "Werkzeug==2.0.1",
        "yamllint==1.26.0",
        "confluent-kafka==1.7.0",
        "google==3.0.0",
    ],
    # Optional
    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={
        "dev": [
            "appdirs==1.4.4",
            "attrs==21.2.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "black==19.10b0",
            "cached-property==1.5.2",
            "cerberus==1.3.2",
            "certifi==2021.5.30",
            "chardet==4.0.0",
            "click==8.0.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "colorama==0.4.4; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "coverage==5.1",
            "distlib==0.3.2",
            "fakeredis==1.4.1",
            "idna==2.10; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "more-itertools==8.8.0; python_version >= '3.5'",
            "orderedmultidict==1.0.1",
            "packaging==20.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pathspec==0.8.1",
            "pep517==0.10.0",
            "pip-shims==0.5.3; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "pipenv-setup==3.1.1",
            "pipfile==0.0.2",
            "pipfile-requirements==0.3.0",
            "plette[validation]==0.2.3; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pluggy==0.13.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "py==1.10.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pyparsing==2.4.7; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pytest==5.4.1",
            "pytest-cov==2.8.1",
            "python-dateutil==2.8.1",
            "redis==3.4.1",
            "regex==2021.7.6",
            "requirementslib==1.5.16; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "six==1.16.0",
            "sortedcontainers==2.4.0",
            "typed-ast==1.4.3",
            "urllib3==1.26.6",
            "vistir==0.5.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "wcwidth==0.2.5",
            "wheel==0.36.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        ]
    },
    # Optional
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # Sometimes you’ll want to use packages that are properly arranged with
    # setuptools, but are not published to PyPI. In those cases, you can specify
    # a list of one or more dependency_links URLs where the package can
    # be downloaded, along with some additional hints, and setuptools
    # will find and install the package correctly.
    # see https://python-packaging.readthedocs.io/en/latest/dependencies.html#packages-not-on-pypi
    #
    dependency_links=[
        "git+https://github.com/huma-engineering/python-apns@4f003da2accb3960b48a8412223af8c52032e341#egg=gobiko-apns",
        "git+https://github.com/huma-engineering/python-apns#egg=gobiko.apns",
    ],
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    # package_data={"": package_files('extensions/deployment/router/module_config_body_schemas')},  # Optional
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[("my_data", ["data/data_file"])],  # Optional
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    # entry_points={"console_scripts": ["sample=sample:main"]},  # Optional
    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        "Bug Reports": "https://github.com/huma-engineering/py-phoenix-server/issues",
        "Source": "https://github.com/huma-engineering/py-phoenix-server/",
    },
    include_package_data=True,
)
