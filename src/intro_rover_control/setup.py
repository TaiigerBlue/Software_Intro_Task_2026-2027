from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'intro_rover_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Chris',
    maintainer_email='ChrisTigerr@gmail.com',
    description='Manual and dance joint control for the Space Concordia intro rover',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'manual_control = intro_rover_control.manual_control:main',
            'dance = intro_rover_control.dance:main',
            'joint_state_to_gz = intro_rover_control.joint_state_to_gz:main',
        ],
    },
)
