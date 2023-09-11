from conan import ConanFile
from conan.tools.cmake import CMake
from conan.tools import files
from conan.tools.files import patches
from functools import cached_property
import json

class Folly(ConanFile):
    name = 'folly'
    version = '2023.09.04.00'

    license = 'ISC'
    author = 'John Freeman <jfreeman08@gmail.com>'
    url = 'https://github.com/thejohnfreeman/conan-folly'
    description = 'An open-source C++ library developed and used at Facebook.'

    settings = 'os', 'compiler', 'build_type', 'arch'
    options = {
        'tests': [True, False],
    }

    default_options = {
        'tests': False,
    }

    requires = [
        'boost/1.82.0',
        'bzip2/1.0.8',
        'double-conversion/3.3.0',
        'fmt/10.0.0',
        'gflags/2.2.2',
        'glog/0.6.0',
        'libevent/2.1.12',
        'libsodium/cci.20220430',
        'liburing/2.3',
        'lz4/1.9.3',
        'openssl/1.1.1p',
        'snappy/1.1.10',
        # For LZMA.
        'xz_utils/5.4.2',
        'zlib/1.2.13',
        'zstd/1.5.5',
    ]

    def requirements(self):
        if self.settings.os == 'Linux':
            self.requires('libiberty/9.1.0')
            self.requires('libunwind/1.7.2')

    def export_sources(self):
        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            self.copy(patch['patch_file'])

    def source(self):
        files.get(self, **self.conan_data['sources'][self.version])
        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            patches.patch(self, **patch)

    # TODO: Is this necessary?
    def configure(self):
        if self.settings.compiler == 'apple-clang':
            self.options['boost'].visibility = 'global'

    def generate(self):
        cmake_include_path = ''
        cmake_library_path = ''
        # TODO: List comprehension?
        for dep in self.deps_cpp_info.deps:
            if dep in ('boost', 'libevent', 'gflags'):
                continue
            cmake_include_path += ';' + ';'.join(self.deps_cpp_info[dep].include_paths)
            cmake_library_path += ';' + ';'.join(self.deps_cpp_info[dep].lib_paths)
        presets = {
            'version': 1,
            'configurePresets': [{
                'name': 'default',
                # TODO: How are we supposed to know this?
                'generator': 'Ninja',
                'cacheVariables': {
                    'CMAKE_BUILD_TYPE': str(self.settings.build_type),
                    'CMAKE_INCLUDE_PATH': cmake_include_path,
                    'CMAKE_LIBRARY_PATH': cmake_library_path,
                    'BOOST_ROOT': self.deps_cpp_info['boost'].rootpath,
                    'LIBGFLAGS_INCLUDE_DIR': self.deps_cpp_info['gflags'].include_paths[0],
                    # TODO: Fix this path somehow...
                    'LIBGFLAGS_LIBRARY_RELEASE': f"{self.deps_cpp_info['gflags'].lib_paths[0]}/lib{self.deps_cpp_info['gflags'].libs[0]}.a",
                    'LibEvent_INCLUDE_PATHS': self.deps_cpp_info['libevent'].include_paths[0],
                    'LibEvent_LIB_PATHS': self.deps_cpp_info['libevent'].lib_paths[0],
                }
            }]
        }
        with open(f'{self.build_folder}/CMakePresets.json', 'w') as file:
            file.write(json.dumps(presets, indent=2))

    @cached_property
    def cmake(self):
        try:
            cmake = CMake(self)
        except Exception as cause:
            import traceback
            traceback.print_exception(cause)
            raise cause
        cmake.verbose = True
        cmake.configure()
        return cmake

    def build(self):
        cmake = self.cmake
        cmake.build()

    def package(self):
        cmake = self.cmake
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ['folly']
