# SPDX-FileCopyrightText: 2026 Nextcloud GmbH and Nextcloud contributors
# SPDX-License-Identifier: BSD-2-Clause

import os
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from Blueprints.CraftPackageObject import BlueprintException, CraftPackageObject
from CraftTestBase import CraftTestBase
from options import UserOptions
from Utils import CraftHash


class BrotliBlueprintTest(CraftTestBase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self.kdeRoot.cleanup)
        self.package = CraftPackageObject.get("libs/brotli")
        self.recipe = self.package.subinfo
        self.recipe.options.dynamic = UserOptions.get(self.package)

    def test_default_build_preserves_current_release(self):
        self.assertEqual(self.recipe.buildTarget, "1.2.1")
        self.assertEqual(self.package.instance.imageDirPattern(), "image-RelWithDebInfo-1.2.1")

    def test_supported_version_overrides(self):
        for version in ("1.0.9", "1.1.0", "1.1.1", "1.2.0", "1.2.1"):
            with self.subTest(version=version):
                UserOptions.setOptions([f"libs/brotli.version={version}"])
                self.assertEqual(self.recipe.buildTarget, version)
                self.assertEqual(self.recipe.targetSourcePath(), f"brotli-{version}")
                self.assertEqual(self.recipe.targetDigest()[1], CraftHash.HashAlgorithm.SHA256)

    def test_unknown_version_is_rejected(self):
        UserOptions.setOptions(["libs/brotli.version=not-a-version"])
        with self.assertRaises(BlueprintException):
            _ = self.recipe.buildTarget

    def test_release_archive_integrity(self):
        UserOptions.setOptions(["libs/brotli.version=1.1.1"])
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "brotli.tar.gz"
            cached_archive = os.getenv("BROTLI_TEST_ARCHIVE")
            if cached_archive:
                archive.write_bytes(Path(cached_archive).read_bytes())
            else:
                with urllib.request.urlopen(self.recipe.target(), timeout=60) as response:
                    archive.write_bytes(response.read())

            digests, algorithm = self.recipe.targetDigest()
            self.assertTrue(CraftHash.checkFilesDigests(directory, [archive.name], digests, algorithm))
            with tarfile.open(archive) as source:
                version_header = source.extractfile(f"{self.recipe.targetSourcePath()}/c/common/version.h").read().decode()
            for component, value in (("MAJOR", 1), ("MINOR", 1), ("PATCH", 1)):
                self.assertIn(f"#define BROTLI_VERSION_{component} {value}", version_header)

            with archive.open("ab") as output:
                output.write(b"corrupt")
            self.assertFalse(CraftHash.checkFilesDigests(directory, [archive.name], digests, algorithm))
