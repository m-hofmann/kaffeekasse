from distutils.core import setup

setup(
        name='kaffeekasse',
        version='0.1',
        packages=['kaffeekasse', 'kaffeekasse.pn532', 'kaffeekasse.utils'],
        url='github.com/m-hofmann/kaffeekasse',
        license='MIT License',
        author='Martin Hofmann',
        author_email='kaffeekasse@hofmann.me.uk',
        description='Coffee fund management tool written in Python. Uses NFC authentication.'
)
