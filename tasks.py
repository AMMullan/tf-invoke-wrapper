import os
import sys
from pathlib import PurePosixPath
import shutil
import contextlib

import yaml
from invoke import task

from lib.utils import assume_client


class color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


role_session_name = 'terraform'
plan_output_file = 'terraform_plan.out'


@contextlib.contextmanager
def remember_cwd():
    curdir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(curdir)


def confirm_choice(message=None):
    if message:
        print(message)
    confirm = input("[c]Confirm or [v]Void: ")
    response = confirm.lower()
    if response not in ['c', 'v']:
        print("\nInvalid Option. Please Enter a Valid Option.")
        return confirm_choice()

    if response == 'c':
        return True

    return False


def configure_task(context):
    if not os.path.exists('tasks.yaml'):
        print('No tasks.yaml exists, exiting.')
        sys.exit(1)

    with open('tasks.yaml') as f:
        try:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        except yaml.scanner.ScannerError as err:
            print(f'{color.BOLD}Error Reading YAML{color.END}\n{err}')
            sys.exit(2)
        except Exception:
            print('Unable to process tasks.yaml')
            sys.exit(1)

    return_config = {}

    all_paths = [context.terraform_path.rstrip('/')] + [
        str(path)
        for path in PurePosixPath(context.terraform_path).parents
        if str(path) != '.'
    ]
    all_paths.reverse()

    assume_role_arn = None
    backend_config = None
    var_file = None
    for path in all_paths:
        if not config.get(path):
            continue

        assume_role_arn = config.get(path, {}).get('assume_role_arn', assume_role_arn)
        backend_config = config.get(path, {}).get('backend_config', backend_config)
        var_file = config.get(path, {}).get('var_file', var_file)

    if assume_role_arn:
        assume_client(
            assume_role_arn,
            session_name=role_session_name,
            profile=context.aws_profile
        )
        return_config['assume_role_arn'] = assume_role_arn

    return_config['backend_config'] = backend_config.replace('${path}', context.terraform_path)
    return_config['var_file'] = var_file.replace('${path}', context.terraform_path)

    return return_config


def clear_cache(context):
    with context.cd(context.terraform_path):
        # Clean the cache folder
        cache_folder = '.terraform'
        pwd = os.getcwd()
        os.chdir(context.terraform_path)
        if os.path.isdir(cache_folder):
            shutil.rmtree(cache_folder)
        os.chdir(pwd)


def terraform_init(context):
    config = configure_task(context)

    opt_str = ""
    if config.get('backend_config'):
        opt_str += f'-backend-config={config.get("backend_config")} '

    with context.cd(context.terraform_path):
        exec = context.run(f'terraform init -reconfigure -get=true {opt_str}')
        config['init_rc'] = exec.return_code

    return config


@task(
    iterable=['target'],
    help={
        'path': 'Folder containing Terraform source',
        'aws_profile': 'AWS CLI profile - will use  \'default\' profile by default',
        'target': 'Terraform Resource(s) to Target - pass multiple times to target multiple resources',
        'output_file': 'Generate an output file for Terraform Plan'
    }
)
def terraform_plan(context, path, target=[], aws_profile='default', output_file=False):
    """ Generate a speculative execution plan, showing what actions Terraform will take """

    context.setdefault('terraform_path', path)
    context.setdefault('aws_profile', aws_profile)

    config = terraform_init(context)

    opt_str = ''
    if config.get('var_file'):
        opt_str += f'-var-file={config.get("var_file")} '

    for resource in target:
        opt_str += f'-target {resource} '

    if output_file:
        opt_str += f'-out={plan_output_file} '

    with context.cd(path):
        # context.run(f'terraform plan -refresh {opt_str}')
        print(f'terraform plan -refresh {opt_str}')

    clear_cache(context)


@task(
    iterable=['target'],
    help={
        'path': 'Folder containing Terraform source',
        'aws_profile': 'AWS CLI profile - will use  \'default\' profile by default',
        'target': 'Terraform Resource(s) to Target - pass multiple times to target multiple resources',
        'output_file': 'Use output file from Terraform Plan',
        'no_ask': '(!) Do NOT ask for approval.'
    }
)
def terraform_apply(context, path, target=[], aws_profile='default', output_file=False, no_ask=False):
    """ Execute a Terraform Apply """

    context.setdefault('terraform_path', path.rstrip('/'))
    context.setdefault('aws_profile', aws_profile)

    config = terraform_init(context)

    opt_str = ''

    if config.get('var_file'):
        opt_str += f'-var-file={config.get("var_file")} '

    if no_ask:
        opt_str += '-auto-approve '

    # Check for a plan
    if output_file:
        with remember_cwd():
            os.chdir(path)
            if os.path.isfile(plan_output_file):
                opt_str += f'{plan_output_file}'
            else:
                print(f'No {plan_output_file} - aborting.')
                sys.exit(1)
    else:
        for resource in target:
            opt_str += f'-target {resource} '

    with context.cd(path):
        context.run(f'terraform apply -refresh {opt_str}')
        if plan_output_file in opt_str:
            context.run(f'rm -f {plan_output_file}')

    clear_cache(context)


@task(
    iterable=['resource'],
    help={
        'path': 'Folder containing Terraform source',
        'aws_profile': 'AWS CLI profile - will use  \'default\' profile by default',
        'resource': 'One or more existing infrastructure resources. Format is [address]=[resource_id]'
    }
)
def terraform_import(context, path, resource, aws_profile='default'):
    """ Import existing infrastructure into Terraform state """
    context.setdefault('terraform_path', path)
    context.setdefault('aws_profile', aws_profile)

    config = terraform_init(context)

    opt_str = ''

    if config.get('var_file'):
        opt_str += f'-var-file={config.get("var_file")} '

    with context.cd(path):
        for item in resource:
            address, resource_id = item.split('=')
            context.run(f'terraform import -backup=- {opt_str} {address} {resource_id}')

    clear_cache(context)


@task(
    iterable=['address']
)
def terraform_delete(context, path, address, aws_profile='default'):
    context.setdefault('terraform_path', path)
    context.setdefault('aws_profile', aws_profile)

    terraform_init(context)

    with context.cd(path):
        for item in address:
            context.run(f'terraform state rm {item}')

    clear_cache(context)


@task(
    help={
        'path': 'Folder containing Terraform source',
        'aws_profile': 'AWS CLI profile - will use  \'default\' profile by default',
        'no_ask': '(!) Do NOT ask for approval.'
    }
)
def terraform_destroy(context, path, aws_profile='default', no_ask=False):
    context.setdefault('terraform_path', path)
    context.setdefault('aws_profile', aws_profile)

    config = terraform_init(context)

    opt_str = ''

    if config.get('var_file'):
        opt_str += f'-var-file={config.get("var_file")} '

    if no_ask:
        opt_str += '-auto-approve '
    else:
        confirm = confirm_choice(f'Are you SURE you want to trash all resources created from {path}?')

    if no_ask or confirm:
        with context.cd(path):
            context.run('terraform destroy {opt_str')

    clear_cache(context)
