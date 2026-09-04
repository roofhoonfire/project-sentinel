SAFE_ACTIONS = {
    "clean_rebuild",
    "reconfigure_project",
    "rerun_tests",
}


def is_safe_action(action: str) -> bool:
    return action in SAFE_ACTIONS
