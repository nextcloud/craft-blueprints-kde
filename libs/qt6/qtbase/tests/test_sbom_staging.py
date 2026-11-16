"""Exercise the blueprint patch against an unmodified Qt 6.11.2 source tree."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
CMAKE = os.environ.get("CMAKE", "cmake")


def run(*args, **kwargs):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    if result.returncode:
        raise AssertionError(result.stdout)
    return result.stdout


class StagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        source = Path(os.environ["QTBASE_SOURCE_DIR"])
        shutil.copytree(source / "cmake", cls.root / "cmake")
        run("git", "apply", "--check", str(HERE.parent / "qtbase-sbom-windows-staging.diff"), cwd=cls.root)
        run("git", "apply", str(HERE.parent / "qtbase-sbom-windows-staging.diff"), cwd=cls.root)
        cls.project = cls.root / "project"
        cls.project.mkdir()
        shutil.copyfile(HERE / "staging-fixture.cmake", cls.project / "CMakeLists.txt")

    def exercise(self, windows, prefix, stage, explicit=False, sbom_format="SPDX_V2"):
        with tempfile.TemporaryDirectory(dir=self.root) as tmp:
            case = Path(tmp)
            build = case / "build"
            if prefix == "DIRECT":
                prefix = str(case / "direct")
            # Windows drive paths are relative on POSIX, allowing portable simulation.
            destdir = str(case / "stage with spaces") if stage else ""
            relative_prefix = prefix[2:] if windows and stage and prefix[1:2] == ":" else prefix
            installed = Path(destdir + relative_prefix)
            if not installed.is_absolute():
                installed = case / installed
            (installed / "bin").mkdir(parents=True)
            (installed / "sbom").mkdir()
            payload = b"synthetic Qt DLL used only for checksum regression\n"
            dependency = b"DocumentNamespace: https://example.test/dependency\n"
            (installed / "bin/Qt6Core.dll").write_bytes(payload)
            (installed / "sbom/dependency.spdx").write_bytes(dependency)
            env = dict(os.environ, DESTDIR="")
            run(CMAKE, "-S", str(self.project), "-B", str(build),
                "-DQT_HELPERS=" + str(self.root / "cmake"),
                "-DTEST_WINDOWS=" + ("ON" if windows else "OFF"),
                "-DTEST_PREFIX=" + prefix,
                "-DEXPLICIT_PREFIX=" + ("ON" if explicit else "OFF"),
                "-DTEST_FORMAT=" + sbom_format, env=env)
            env["DESTDIR"] = destdir
            run(CMAKE, "-P", str(build / "run.cmake"), cwd=case, env=env)
            result = (installed / "sbom/qtbase.spdx").read_text()
            self.assertIn("FileChecksum: SHA1: " + hashlib.sha1(payload).hexdigest(), result)
            self.assertIn("SHA1: " + hashlib.sha1(dependency).hexdigest(), result)
            self.assertEqual(len(list(case.rglob("qtbase.spdx"))), 1)

    def test_backslash_paths_and_install_time_values(self):
        script = self.root / "path-cases.cmake"
        script.write_text(r'''cmake_minimum_required(VERSION 3.21)
function(__qt_internal_cmake_include_guard)
endfunction()
include("${HELPERS}/QtPublicSbomCommonGenerationHelpers.cmake")
# Generate before either prefix or DESTDIR is known.
_qt_internal_sbom_get_staged_path_code(code result "\${prefix}/sbom")
set(WIN32 TRUE)
set(prefix [[C:\Nextcloud\stable-35.0\windows-msvc2022_64-cl]])
set(ENV{DESTDIR} [[c:\_\4694666a\image-RelWithDebInfo-6.11.2]])
cmake_language(EVAL CODE "${code}")
set(expected "c:/_/4694666a/image-RelWithDebInfo-6.11.2/Nextcloud/stable-35.0/windows-msvc2022_64-cl/sbom")
if(NOT result STREQUAL expected)
    message(FATAL_ERROR "Staged path: ${result}")
endif()
set(ENV{DESTDIR} "")
cmake_language(EVAL CODE "${code}")
if(NOT result STREQUAL "C:/Nextcloud/stable-35.0/windows-msvc2022_64-cl/sbom")
    message(FATAL_ERROR "Direct path: ${result}")
endif()
''')
        run(CMAKE, "-DHELPERS=" + str(self.root / "cmake"), "-P", str(script))

    def test_windows_staged_default_prefix(self):
        self.exercise(True, "C:/Nextcloud/stable-35.0/windows-msvc2022_64-cl", True)

    def test_windows_staged_explicit_prefix_with_spaces(self):
        self.exercise(True, "D:/Nextcloud SDK/windows", True, explicit=True)

    @unittest.skipIf(os.name == "nt", "Portable drive-path simulation runs on POSIX")
    def test_windows_direct_install_keeps_drive(self):
        self.exercise(True, "C:/Nextcloud/direct", False)

    def test_macos_staged_prefix(self):
        self.exercise(False, "/opt/Nextcloud/macos", True)

    def test_unix_direct_install(self):
        self.exercise(False, "DIRECT", False)

    def test_cyclonedx_output_staged(self):
        self.exercise(True, "C:/Nextcloud/cyclonedx", True, sbom_format="CYDX_V1_6")


if __name__ == "__main__":
    unittest.main()
