from setuptools import setup, find_packages

VERSION = '0.6'
DESCRIPTION = 'Little helper tools for IB API'
LONG_DESCRIPTION = 'Little helper tools for IB API'

setup(
    name="ibtools",
    version=VERSION,
    author="Juergen Reiss",
    author_email="juxeiier@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/juxeii/ibtools',
    license='BSD',
    python_requires='>=3.6',
    packages=find_packages(),
    install_requires=['rx', 'ib_insync', 'IPython'],
    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        'Topic :: Office/Business :: Financial :: Investment',
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        'License :: OSI Approved :: BSD License'
    ]
)
