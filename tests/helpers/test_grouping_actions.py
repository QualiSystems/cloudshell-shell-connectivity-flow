import pytest

from cloudshell.shell.flows.connectivity.cloud_providers_flow import VnicInfo
from cloudshell.shell.flows.connectivity.helpers.group_cp_actions import group_actions
from cloudshell.shell.flows.connectivity.models.connectivity_model import (
    ConnectivityActionModel,
    get_vnic,
)
from tests.base import create_cp_ad


@pytest.mark.parametrize(
    (
        "existed_vnics_info",  # Collection[VnicInfo]
        "actions_vnics",  # Collection[str] - vnic names or "" if missed
        "expected_groups_indexes",  # Collection[Collection[tuple[int, int]]]
        #   the same structure as returns group_actions
        #   first index means vNIC index that should be used for the action
        #   second index means action index from the actions list
    ),
    (
        (  # VM has one vNIC with network that can be replaced
            # one action without vNIC specified
            [VnicInfo("1", 1, True)],
            [""],
            [[("1", 0)]],
        ),
        (  # VM has one vNIC with network that can be replaced
            # one action with vNIC specified
            [VnicInfo("1", 1, True)],
            ["1"],
            [[("1", 0)]],
        ),
        (  # VM has one vNIC with network that cannot be replaced
            # one action without vNIC specified
            [VnicInfo("1", 1, False)],
            [""],
            [[("2", 0)]],
        ),
        (  # VM has one vNIC with network that cannot be replaced
            # one action with vNIC specified that is used
            [VnicInfo("1", 1, False)],
            ["1"],
            (ValueError, "it is already used"),
        ),
        (  # VM has one vNIC with network that cannot be replaced
            # one action with next new vNIC
            [VnicInfo("1", 1, False)],
            ["2"],
            [[("2", 0)]],
        ),
        (  # VM has one vNIC with network that can be replaced
            # 2 actions without vNIC specified
            [VnicInfo("1", 1, True)],
            ["", ""],
            [[("1", 0)], [("2", 1)]],
        ),
        (  # Classic case 3
            # VM has one vNIC with network that can be replaced
            # 2 actions with vNIC specified
            [VnicInfo("1", 1, True)],
            ["1", "2"],
            [[("1", 0)], [("2", 1)]],
        ),
        (  # Classic case 4
            # VM has one vNIC with network that can be replaced
            # 2 actions - with specified vNIC and without
            [VnicInfo("1", 1, True)],
            ["", "1"],
            [[("1", 1)], [("2", 0)]],
        ),
        (  # Classic case 6
            # VM has 2 vNICs with networks that can be replaced
            # 4 actions with vNIC specified
            [VnicInfo("1", 1, True), VnicInfo("2", 2, True)],
            ["1", "3", "2", "4"],
            [[("1", 0)], [("2", 2)], [("3", 1), ("4", 3)]],
        ),
        (  # Broken vNIC order
            # VM has 2 vNICs with networks that can be replaced
            # 1 action with wrong vNIC specified
            [VnicInfo("1", 1, True), VnicInfo("2", 2, True)],
            ["4"],
            (ValueError, "gaps between vNIC"),
        ),
        (  # vNIC order in case first two vNICs are connected to Reserved Network
            # VM has 2 vNICs with networks that cannot be replaced
            # 2 action with 1 vNIC specified and 1 not
            [VnicInfo("1", 1, False), VnicInfo("2", 2, False)],
            ["4", ""],
            [[("3", 1), ("4", 0)]],
        ),
        (
            # VM has 2 vNICs with networks that can be replaced
            # 1 action without vNIC specified
            # should be connected to first vNIC
            [VnicInfo("1", 1, True), VnicInfo("2", 2, True)],
            [""],
            [[("1", 0)]],
        ),
        (
            # VM has 2 vNICs with networks that can be replaced
            # 2 action, 1st without vNIC specified, 2nd with 3rd vNIC specified
            # should be connected to 1st vNIC and 3rd vNIC
            [VnicInfo("1", 1, True), VnicInfo("2", 2, True)],
            ["", "3"],
            [[("1", 0)], [("3", 1)]],
        ),
    ),
)
def test_grouping_actions(
    existed_vnics_info,
    actions_vnics,
    expected_groups_indexes,
):
    requested_actions = [
        ConnectivityActionModel.parse_obj(create_cp_ad(vnic=vnic_name))
        for vnic_name in actions_vnics
    ]

    if isinstance(expected_groups_indexes[0], type) and issubclass(
        expected_groups_indexes[0], Exception
    ):
        with pytest.raises(
            expected_groups_indexes[0], match=expected_groups_indexes[1]
        ):
            group_actions(requested_actions, existed_vnics_info)
        return

    grouped_actions = group_actions(requested_actions, existed_vnics_info)
    assert len(grouped_actions) == len(expected_groups_indexes)
    for actions, expected_actions_indexes in zip(
        grouped_actions, expected_groups_indexes
    ):
        assert len(actions) == len(expected_actions_indexes)
        for action, expected_indexes in zip(actions, expected_actions_indexes):
            assert get_vnic(action) == expected_indexes[0]
            assert requested_actions.index(action) == expected_indexes[1]
