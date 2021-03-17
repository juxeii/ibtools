from setuptools import setup, find_packages

VERSION = '0.4'
DESCRIPTION = 'Little helper tools for IB API'
LONG_DESCRIPTION = 'Little helper tools for IB API'

setup(
    name="ibtools",
    version=VERSION,
    author="Juergen Reiss",
    author_email="juxeiier@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['ib_insync', 'IPython'],
    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)"
    ]
)
