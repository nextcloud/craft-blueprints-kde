cmake_minimum_required(VERSION 3.21)
project(SbomStagingRegression LANGUAGES NONE)
# Only isolate Qt's surrounding project bookkeeping; run its real path, install,
# checksum, and external-reference generators below.
function(__qt_internal_cmake_include_guard)
endfunction()
function(_qt_internal_validate_all_args_are_parsed prefix)
    if(${prefix}_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "Unexpected arguments")
    endif()
endfunction()
include("${QT_HELPERS}/QtPublicSbomCommonGenerationHelpers.cmake")
include("${QT_HELPERS}/QtPublicSbomGenerationHelpers.cmake")
include("${QT_HELPERS}/QtPublicSbomExternalReferenceHelpers.cmake")
function(_qt_internal_get_current_project_sbom_dir out)
    set(${out} "${CMAKE_BINARY_DIR}" PARENT_SCOPE)
endfunction()
function(_qt_internal_get_staging_area_spdx_file_path out)
    set(${out} "${CMAKE_BINARY_DIR}/staging.spdx" PARENT_SCOPE)
endfunction()
function(_qt_internal_get_staging_area_cydx_file_path out)
    set(${out} "${CMAKE_BINARY_DIR}/staging.spdx" PARENT_SCOPE)
endfunction()
set(QT_GENERATE_SBOM ON)
set_property(GLOBAL PROPERTY _qt_sbom_project_spdx_id SPDXRef-qtbase)
set(prefix_args "")
if(EXPLICIT_PREFIX)
    list(APPEND prefix_args INSTALL_PREFIX "${TEST_PREFIX}")
    set(output_prefix "${TEST_PREFIX}")
else()
    set(output_prefix "\${CMAKE_INSTALL_PREFIX}")
endif()
_qt_internal_sbom_generate_add_file(FILENAME bin/Qt6Core.dll FILETYPE BINARY
    SPDXID SPDXRef-Core PARENT_PACKAGE_SPDXID SPDXRef-qtbase ${prefix_args})
_qt_internal_sbom_generate_add_external_reference(
    EXTERNAL_DOCUMENT_FILE_PATH sbom/dependency.spdx
    EXTERNAL_DOCUMENT_SPDX_ID DocumentRef-dependency)
file(WRITE "${CMAKE_BINARY_DIR}/assemble.cmake"
    "file(WRITE \"${CMAKE_BINARY_DIR}/staging.spdx\" \"\")\n"
    "include(\"${CMAKE_BINARY_DIR}/SPDXRef-Core.cmake\")\n"
    "include(\"${CMAKE_BINARY_DIR}/DocumentRef-dependency.cmake\")\n"
    "file(APPEND \"${CMAKE_BINARY_DIR}/staging.spdx\" \"\${QT_SBOM_EXTERNAL_DOC_REFS}\")\n")
file(WRITE "${CMAKE_BINARY_DIR}/verification.cmake" "")
_qt_internal_sbom_setup_sbom_install_code(
    SBOM_FORMAT "${TEST_FORMAT}" REPO_PROJECT_NAME_LOWERCASE qtbase
    SBOM_INSTALL_OUTPUT_PATH "${output_prefix}/sbom/qtbase.spdx"
    SBOM_INSTALL_OUTPUT_PATH_WITHOUT_EXT "${output_prefix}/sbom/qtbase"
    SBOM_INSTALL_OUTPUT_DIR "${output_prefix}/sbom"
    ASSEMBLE_SBOM_INCLUDE_PATH "${CMAKE_BINARY_DIR}/assemble.cmake"
    PROCESS_VERIFICATION_CODES "${CMAKE_BINARY_DIR}/verification.cmake")
# Include definitions needed by Qt's generated external-document script.
file(WRITE "${CMAKE_BINARY_DIR}/run.cmake"
    "set(WIN32 ${TEST_WINDOWS})\n"
    "set(CMAKE_INSTALL_PREFIX \"${TEST_PREFIX}\")\n"
    "function(__qt_internal_cmake_include_guard)\nendfunction()\n"
    "function(_qt_internal_validate_all_args_are_parsed)\nendfunction()\n"
    "include(\"${QT_HELPERS}/QtPublicSbomExternalReferenceHelpers.cmake\")\n"
    "include(\"${CMAKE_BINARY_DIR}/cmake_install.cmake\")\n")
