# =================================================================================================
# Export a TCMS product, test case or test plan to file.
# -------------------------------------------------------------------------------------------------
# Usage:
#   issai_export.sh [options] {case|case-id|plan|plan-id|product|product-id} entity_ref output_path
#     Options: --include-attachments (default: not set, i.e. False)
#              --include-descendants (default: not set, i.e. False)
#              --include-executions (default: not set, i.e. False)
#              --include-history (default: not set, i.e. False)
#              --include-runs (default: not set, i.e. False)
#              --product-build <build-name> (default: not set,
#                                            i.e. all builds of specified versions)
#              --product-version <version-value> (default: not set, i.e. all versions)
# -------------------------------------------------------------------------------------------------
# The output path must be an empty directory.
# The entity will be exported to file <entity-type>_<tcms-entity-id>.toml in the output path,
# e.g. testcase_24.toml.
#
# Option --include-attachments will also export attachments from TCMS.
# Attachment files are placed under subdirectory attachments in the output path, then under a
# subdirectory named like the entity type (case, plan or run) and finally under a
# subdirectory named like the entity ID
#
# Option --include-descendants will include descendant test plans in the export.
# Applies to entity type test plan only.
#
# Option --include-executions will include test executions in the export.
# Applies to entity type test case only.
#
# Option --include-history will include change history of test cases and executions in the export.
#
# Option --include-runs will include test runs and executions in the export.
# Applies to entity type test plan only.
#
# Option --product-build will limit exported test runs and executions to the specified build.
#
# Option --product-version will limit exported test plans and cases to the specified version.
# -------------------------------------------------------------------------------------------------
# Copyright (c) 2024 Frank Sommer
# =================================================================================================

export PYTHONPATH=..:$PYTHONPATH
python3 cli/issai_export.py $*
