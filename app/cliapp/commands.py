import argparse

from pprint import pprint
from clap.common.config import Defaults
from clap.common.factory import PlatformFactory
from . import interactive


def common_arguments_parser():
    parser = argparse.ArgumentParser(prog='clap', description='CLPits starts and manages modules in the cloud')
    parser.add_argument('--platform-db', '-p', action='store', default=Defaults.PLATFORM_REPOSITORY,
                        help='Platform database to be used (default: `{}`)'.format(Defaults.PLATFORM_REPOSITORY))
    parser.add_argument('--repo-type', '-r', action='store', default=Defaults.REPOSITORY_TYPE,
                        help='Default repository type (default: `{}`)'.format(Defaults.REPOSITORY_TYPE))
    parser.add_argument('--driver', '-d', action='store', default=Defaults.DRIVER_ID,
                        help='Cloud driver to manage instances (default: `{}`'.format(Defaults.DRIVER_ID))
    parser.add_argument('--show-all-help', '-hh', help='Show help of all commands', action='store_true', default=False)
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increase the verbosity level. 0 for error only (default); 1 for more info; 2 to debug')

    commands_parser = parser.add_subparsers(title='commands', dest='command')

     # Node Commands
    node_parser = commands_parser.add_parser('node', help='Manage/perform operations in the nodes of the clusters')
    node_com_parser = node_parser.add_subparsers(title='subcommand', dest='subcommand')

    node_subcom_parser = node_com_parser.add_parser('start', help='Start nodes in the cluster (based on the template)')
    node_subcom_parser.add_argument(
        'nodes', action='store', nargs='+', metavar='node_type:num',
        help='Type of the nodes to be instantiated (based on the cluster template). Format is <node_type>:<num>, '
             'if num is not provided, default is 1')
    node_subcom_parser.add_argument('--group', action='store', nargs='+', help='Groups to add nodes after started')
    node_subcom_parser.add_argument('--extra', nargs=argparse.REMAINDER, metavar='arg=val',
                                    help="Keyworded (format: x=y) Arguments to be passed to the group setup action")
    node_subcom_parser.set_defaults(func=node_start)

    node_subcom_parser = node_com_parser.add_parser('list', help='List nodes')
    node_subcom_parser.set_defaults(func=node_list)

    node_subcom_parser = node_com_parser.add_parser('show', help='Show detailed information of the nodes')
    node_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be displayed')
    node_subcom_parser.set_defaults(func=node_show)

    node_subcom_parser = node_com_parser.add_parser('alive', help='Check if nodes are alive')
    node_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be checked')
    node_subcom_parser.set_defaults(func=node_alive)

    node_subcom_parser = node_com_parser.add_parser('stop', help='Stop and terminate nodes')
    node_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be stopped')
    node_subcom_parser.set_defaults(func=node_stop)

    node_subcom_parser = node_com_parser.add_parser('pause', help='Pause nodes')
    node_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be paused')
    node_subcom_parser.set_defaults(func=node_pause)

    node_subcom_parser = node_com_parser.add_parser('playbook', help='Execute playbook in nodes')
    node_subcom_parser.add_argument('playbook_file', action='store', help='Playbook file to be executed')
    node_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be stopped')
    node_subcom_parser.add_argument('--extra', nargs=argparse.REMAINDER, metavar='arg=val',
                                    help="Keyworded (format: x=y) Arguments to be passed to the playbook")
    node_subcom_parser.set_defaults(func=node_playbook)

    node_subcom_parser = node_com_parser.add_parser('execute', help='Execute a command in the node (via SSH)')
    node_subcom_parser.add_argument('node_id', action='store', help='ID of the node to get an SSH connection')
    node_subcom_parser.add_argument('cmd', nargs=argparse.REMAINDER, metavar='"cmd"',
                                    help='Command to be executed')
    node_subcom_parser.set_defaults(func=node_exec_command)

    node_subcom_parser = node_com_parser.add_parser('connect', help='Connect via SSH to a node')
    node_subcom_parser.add_argument('node_id', action='store', help='ID of the node to get an SSH connection')
    node_subcom_parser.set_defaults(func=node_connect)

    # Group commands
    group_parser = commands_parser.add_parser('group', help='Group operation in nodes')
    group_com_parser = group_parser.add_subparsers(title='subcommand', dest='subcommand')

    group_subcom_parser = group_com_parser.add_parser('add', help='Add nodes to a group')
    group_subcom_parser.add_argument('group', action='store', help='Name of the group to be added')
    group_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be added to the group')
    group_subcom_parser.add_argument('--extra', nargs=argparse.REMAINDER, metavar='arg=val',
                                     help="Keyworded (format: x=y) Arguments to be passed to the action")
    group_subcom_parser.set_defaults(func=add_group_to_node)

    group_subcom_parser = group_com_parser.add_parser('list', help='List available groups')
    group_subcom_parser.set_defaults(func=list_groups)

    group_subcom_parser = group_com_parser.add_parser('action', help='Perform an action in the node group')
    group_subcom_parser.add_argument('group', action='store', help='Name of the group to perform the action')
    group_subcom_parser.add_argument('action', action='store', help='Name of the action to be performed')
    group_subcom_parser.add_argument('--nodes', action='store', nargs='+', help='ID of the nodes to be perform the action')
    group_subcom_parser.add_argument('--extra', nargs=argparse.REMAINDER, metavar='arg=val',
                                     help="Keyworded (format: x=y) Arguments to be passed to the action")
    group_subcom_parser.set_defaults(func=execute_group_action)

    group_subcom_parser = group_com_parser.add_parser('remove', help='Remove nodes from a group')
    group_subcom_parser.add_argument('group', action='store', help='Name of the group to be removed')
    group_subcom_parser.add_argument('node_ids', action='store', nargs='+', help='ID of the nodes to be removed from the group')
    group_subcom_parser.add_argument('--extra', nargs=argparse.REMAINDER, metavar='arg=val',
                                     help="Keyworded (format: x=y) Arguments to be passed to the action")
    group_subcom_parser.set_defaults(func=remove_group_from_node)

    return parser, commands_parser


def __get_instance_api(namespace: argparse.Namespace):
    return PlatformFactory.get_instance_api(
        platform_db=namespace.platform_db, repository_type=namespace.repo_type, default_driver=namespace.driver)


def get_commands_parser():
    return common_arguments_parser()


def node_start(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    nodes = {}

    for node in namespace.nodes:
        splited_values = node.split(':')
        nodes[splited_values[0]] = 1 if len(splited_values) == 1 else int(splited_values[1])

    nodes_info = multi_instance.start_nodes(nodes)

    for node_info in nodes_info:
        print('* ', node_info)

    print("Started {} nodes".format(len(nodes_info)))

    if namespace.group:
        try:
            extra = {arg.split('=')[0]: arg.split('=')[1] for arg in namespace.extra} if namespace.extra else {}
        except Exception:
            raise Exception("Error mounting extra parameters. Are you putting spaces after `=`? "
                            "Please check the extra parameters passed")

        for group in namespace.group:
            started_nodes = [n.node_id for n in nodes_info]
            print("Adding nodes `{}` to group: `{}`".format(', '.join(started_nodes), group))
            added_nodes = multi_instance.add_nodes_to_group(started_nodes, group, group_args=extra)
            if added_nodes:
                print("Nodes `{}` were successfully added to group `{}`".format(', '.join(added_nodes), group))


def node_list(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    nodes = multi_instance.get_nodes()

    for node_info in nodes:
        print('* ', node_info)

    print("Listed {} nodes(s)".format(len(nodes)))


def node_show(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    nodes = multi_instance.get_nodes(namespace.node_ids)

    for node_info in nodes:
        print('------- `{}` --------'.format(node_info.node_id))
        pprint(node_info.__dict__, indent=4)

    print("Listed {} nodes(s)".format(len(nodes)))


def node_alive(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    alive_nodes = multi_instance.check_nodes_alive(namespace.node_ids)

    print(' ------ ALIVE NODES ------ ')
    for k in sorted(alive_nodes.keys()):
        print("* {} --> {}".format(k, 'alive' if alive_nodes[k] else 'not reachable'))

    print('Checked {} nodes'.format(len(alive_nodes)))


def node_stop(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    multi_instance.stop_nodes(namespace.node_ids)
    print("Nodes `{}` stopped!".format(', '.join(namespace.node_ids)))


def node_pause(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    multi_instance.pause_nodes(namespace.node_ids)
    print("Nodes `{}` paused!".format(', '.join(namespace.node_ids)))


def node_playbook(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    try:
        extra = {arg.split('=')[0]: arg.split('=')[1] for arg in namespace.extra} if namespace.extra else {}
    except Exception:
        raise Exception("Error mounting extra parameters. Are you putting spaces after `=`? "
                        "Please check the extra parameters passed")
    multi_instance.execute_playbook_in_nodes(namespace.node_ids, namespace.playbook_file, **extra)


def node_exec_command(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    command = ' '.join(namespace.cmd)
    print('Executing in node `{}` the command (via SSH): `{}`'.format(namespace.node_id, command))
    ssh_client = multi_instance.get_connection_to_nodes([namespace.node_id])[namespace.node_id]
    _, stdout, stderr = ssh_client.exec_command(command)
    print("{} STD OUTPUT {}".format('-'*40, '-'*40))
    print(''.join(stdout.readlines()))
    print("{} ERR OUTPUT {}".format('-'*40, '-'*40))
    print(''.join(stderr.readlines()))
    print('-' * 80)

    ssh_client.close()


def node_connect(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    print('Connecting to node `{}` (via SSH)'.format(namespace.node_id))
    ssh_client = multi_instance.get_connection_to_nodes([namespace.node_id])[namespace.node_id]
    channel = ssh_client.get_transport().open_session()
    channel.get_pty()
    channel.invoke_shell()
    interactive.interactive_shell(channel)
    ssh_client.close()
    print("Connection to `{}` closed".format(namespace.node_id))


def add_group_to_node(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    try:
        extra = {arg.split('=')[0]: arg.split('=')[1] for arg in namespace.extra} if namespace.extra else {}
    except Exception:
        raise Exception("Error mounting extra parameters. Are you putting spaces after `=`? "
                        "Please check the extra parameters passed")

    added_nodes = multi_instance.add_nodes_to_group(namespace.node_ids, namespace.group, group_args=extra)
    if added_nodes:
        print("Nodes `{}` were successfully added to group `{}`".format(', '.join(added_nodes), namespace.group))


def execute_group_action(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    try:
        extra = {arg.split('=')[0]: arg.split('=')[1] for arg in namespace.extra} if namespace.extra else {}
    except Exception:
        raise Exception("Error mounting extra parameters. Are you putting spaces after `=`? "
                        "Please check the extra parameters passed")

    if namespace.nodes:
        actioned_nodes = multi_instance.execute_group_action(namespace.nodes, namespace.group, namespace.action, group_args=extra)
    else:
        actioned_nodes = multi_instance.execute_action_in_nodes_of_group(namespace.group, namespace.action, group_args=extra)

    if actioned_nodes:
        print("Nodes `{}` successfully performed action `{}` from group `{}`".format(', '.join(actioned_nodes), namespace.action, namespace.group))


def list_groups(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    groups = multi_instance.get_groups()

    for group in sorted(groups):
        print('* ', group)

    print("Listed {} groups".format(len(groups)))


def remove_group_from_node(namespace: argparse.Namespace):
    multi_instance = __get_instance_api(namespace)
    try:
        extra = {arg.split('=')[0]: arg.split('=')[1] for arg in namespace.extra} if namespace.extra else {}
    except Exception:
        raise Exception("Error mounting extra parameters. Are you putting spaces after `=`? "
                        "Please check the extra parameters passed")

    removed_nodes = multi_instance.remove_node_from_group(namespace.node_ids, namespace.group, group_args=extra)
    if removed_nodes:
        print("Nodes `{}` were successfully removed from group `{}`".format(', '.join(removed_nodes), namespace.group))


def print_all_help(parser):
    print('\n ------------ Printing usage of: `{}` --------------'.format(parser.prog))
    parser.print_help()

    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction):
            for name, p in a._name_parser_map.items():
                print_all_help(p)

