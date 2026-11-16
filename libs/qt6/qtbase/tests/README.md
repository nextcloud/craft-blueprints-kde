# Qt SBOM staging regression tests

These tests apply the blueprint patch to a temporary copy of an **unmodified Qt
6.11.2** source tree. They configure a compiler-free CMake fixture and run Qt's
actual generated SBOM install/checksum scripts against synthetic files. They do
not compile Qt or a client.

On a POSIX host with Python 3, Git and CMake 3.21 or newer:

```sh
QTBASE_SOURCE_DIR=/path/to/qtbase-everywhere-src-6.11.2 \
  python3 libs/qt6/qtbase/tests/test_sbom_staging.py
```

Set `CMAKE` to an executable path if CMake is not on `PATH`. The tests simulate
Windows drive paths (including the reported backslash staging path), cover
explicit and install-time prefixes, verify real file and dependency-document
SHA-1 checksums, exercise both SBOM output formats' shared installation code,
and check direct installs and macOS-style staging. This does not replace a
native Windows Craft build.

The fix is registered for Qt 6.11.2, patch level 3. Existing configured Qt build
trees must be patched and reconfigured to regenerate their SBOM install scripts;
retrying the previous generated scripts alone will retain the invalid paths.
Qt SBOM generation remains enabled through its existing default.
