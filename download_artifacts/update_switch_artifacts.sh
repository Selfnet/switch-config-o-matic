#!/bin/sh
set -e
GITLAB_TOKEN=<YOUR_TOKEN>
proj_dir=/home/selfnet/switch-config-o-matic

output=artifacts.zip
target=switch_configs

cd "${proj_dir}"
rm -r "${output}" "switch_configs_huawei" || true
python3 download_artifacts.py --output "${output}" --token "${GITLAB_TOKEN}"
unzip "${output}"
for config in ./switch_configs_huawei/*; do
  mv "${config}" "${target}/$(basename $config).cfg"
done
rm "${output}"
