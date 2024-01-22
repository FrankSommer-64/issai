# =================================================================================================
# Run test plan.
# -------------------------------------------------------------------------------------------------
# Usage:
#   issai_run.sh [options] {plan | plan-id | input-file} entity_ref
#     Options: --dry-run (default: not set, i.e. False)
#              --environment <environment-name> (default: not set, i.e. None)
#              --include-descendants (default: not set, i.e. False)
#              --product <product-name> (default: not set, i.e. None)
#              --product-build <build-name> (default: not set, i.e. None)
#              --product-version <version-value> (default: not set, i.e. None)
#              --store-result (default: not set, i.e. False)
# -------------------------------------------------------------------------------------------------
# The file to import must contain the entity data in TOML format.
#
# Option --dry-run will simulate a run, but not change anything in TCMS.
# Can be used to check, whether all preconditions for a run are fulfilled
#
# Option --environment will set an environment variable for every property of the TCMS environment.
#
# Option --include-descendants will run all descendant test plans, too.
#
# Option --product specifies the name of the TCMS product to use.
# Required, if the test plan is specified by name, and TCMS contains
# more than one test plan with that name.
#
# Option --product-build specifies the name of the TCMS build to use.
# Required, if a unique build cannot be determined otherwise.
#
# Option --product-version specifies the value of the TCMS version to use.
# Required, if a unique version cannot be determined otherwise.
#
# Option --store-result will automatically update affected test runs and
# executions in TCMS with the result.
# -------------------------------------------------------------------------------------------------
# Copyright (c) 2024 Frank Sommer
# =================================================================================================

export PYTHONPATH=..:$PYTHONPATH
python3 cli/issai_run.py $*
