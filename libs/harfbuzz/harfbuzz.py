import info
from CraftCore import CraftCore
from Package.MesonPackageBase import MesonPackageBase
from Utils import CraftHash


class subinfo(info.infoclass):
    def setTargets(self):
        self.targets["11.2.0"] = "https://github.com/harfbuzz/harfbuzz/archive/11.2.0.tar.gz"
        self.targetInstSrc["11.2.0"] = "harfbuzz-11.2.0"
        if CraftCore.compiler.isAndroid:
            self.patchToApply["11.2.0"] = [("no-so-version.patch", 1)]
        self.patchLevel["11.2.0"] = 2
        self.targets["15.2.0"] = "https://github.com/harfbuzz/harfbuzz/releases/download/15.2.0/harfbuzz-15.2.0.tar.xz"
        self.targetInstSrc["15.2.0"] = "harfbuzz-15.2.0"
        self.targetDigests["11.2.0"] = (["16c0204704f3ebeed057aba100fe7db18d71035505cb10e595ea33d346457fc8"], CraftHash.HashAlgorithm.SHA256)
        self.targetDigests["15.2.0"] = (["e2ec49090744383cdbe7df808c1cedaafba06a97be8dc4211fe546ba585f12cb"], CraftHash.HashAlgorithm.SHA256)
        self.description = "Text shaping library"
        self.defaultTarget = "15.2.0"

    def setDependencies(self):
        self.runtimeDependencies["virtual/base"] = None
        self.buildDependencies["python-modules/meson"] = None
        self.runtimeDependencies["libs/icu"] = None
        self.runtimeDependencies["libs/freetype"] = None
        if not CraftCore.compiler.isAndroid:
            self.runtimeDependencies["libs/cairo"] = None


class Package(MesonPackageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subinfo.options.configure.args += [
            "-Ddocs=disabled",
            "-Dbenchmark=disabled",
            f"-Dtests={self.subinfo.options.dynamic.buildTests.asEnabledDisabled}",
            "-Dglib=disabled",
            "-Dgobject=disabled",
            "-Dfreetype=enabled",
            f"-Dicu={self.subinfo.options.isActive('libs/icu').asEnabledDisabled}",
            f"-Dcairo={CraftCore.compiler.isAndroid.inverted.asEnabledDisabled}",
        ]
