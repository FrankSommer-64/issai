# =================================================================================================
# Import file containing a product, test case, test plan or result to TCMS.
# -------------------------------------------------------------------------------------------------
# Usage:
#   issai_import.sh [options] input_file
#     Options: --apply-current-user {always | missing | never} (default: never)
#              --create-master-data (default: not set, i.e. False)
#              --dry-run (default: not set, i.e. False)
#              --include-attachments (default: not set, i.e. False)
# -------------------------------------------------------------------------------------------------
# The file to import must contain the entity data in TOML format.
#
# Option --apply-current-user always will use the current user as owner for
# all objects created in TCMS.
# Option --apply-current-user missing will use the current user as owner for objects created in
# TCMS, if the owner specified in import file doesn't exist in TCMS.
# Option --apply-current-user never will result in import failure, if a user
# specified in import file doesn't exist in TCMS.
#
# Option --create-master-data will automatically create master data like builds
# or categories, if they don't exist in TCMS.
#
# Option --dry-run will simulate an import, but not change anything in TCMS.
# Can be used to check an import in advance.
#
# Option --include-attachments will also import attachments to TCMS.
# Attachments must be referenced by pure file name in the input file.
# Attachment files must be placed under subdirectory attachments in the path of the input file,
# then under a subdirectory named like the entity type (case, plan or run) and
# finally under a subdirectory named like the entity ID as specified in the input file.
# -------------------------------------------------------------------------------------------------
# Copyright (c) 2024 Frank Sommer
# =================================================================================================

export PYTHONPATH=..:$PYTHONPATH
python3 cli/issai_import.py $*
