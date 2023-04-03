# Download Switch Artifacts

This directory contains the required scripts to automatically update switch configs. The configs are created daily by a [scheduled siam pipeline](https://git.selfnet.de/support/siam/-/pipeline_schedules) name `Build switch configs`.

The script `update_switch_artifacts.sh` must be copied located on your target system and the `GITLAB_TOKEN` as well as the `proj_dir` must be adapted. The Gitlab token must be some token that has access to the artifcacts created by the scheduled SIAM pipeline.

The `ExecStart` value of `switch_artifacts.service` must point to the location of the shell script. The `switch_artifacts.*` file must be copied to `~/.config/systemd/user/`. Additionally, the `switch_artifacts.timer` must be symlinked to `~/.config/systemd/user/multi-user.target.wants/switch_artifacts.timer`.

Finally, the unit must be started using `systemctl --user enable --now switch_artifacts` and can be monitored using `journalctl --user -u switch_artifacts`.
