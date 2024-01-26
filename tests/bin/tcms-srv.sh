# Runs TCMS test server with specified test data set.
script_file_path=`realpath $0`
scripts_path=`dirname $script_file_path`
tests_path=`realpath $scripts_path/..`
project_path=`realpath $tests_path/..`
dataset_file_path="$tests_path/testdata/dataset/$1.toml"
venv_act_file_path="$project_path/.venv/bin/activate"
server_module_path="$tests_path/server/tcmsserver.py"
source $venv_act_file_path
export PYTHONPATH=$project_path/src
python $server_module_path $dataset_file_path

