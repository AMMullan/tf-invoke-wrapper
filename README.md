
# Python Invoke Terraform Wrapper

When you're working in an environment that has lots of Terraform projects in one repo, or just want an easier way to call Terraform then this script can help simplify everything.

This script uses the [Invoke](https://pypi.org/project/invoke/) Python package and aims provide a config-driven approach and allow for as much flexability as possible.

Currently it supports the following Terraform features:
* Plan
* Apply
* Import
* Delete
* Destroy

## Requirements
 name   | version
 ------ | -------
 python | >= 3.6
 invoke | >= 1.5.0

## Configuration

By default, the configuration is stored in YAML, with the name **tasks.yaml** (JSON support forthcoming). The configuration is designed so that the more granular your path configuration is, the preference it gets parsed.

Sample YAML:
```yaml
terraform:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform'

terraform/123456789012:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform'
terraform/123456789012/eu-west-1/production:
  backend_path: '${path}/parameters/backend.tfvars'
  vars_file: '${path}/parameters/production.tfvars'
terraform/123456789012/eu-west-1/development:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform-production'
  backend_path: '${path}/parameters/backend.tfvars'

terraform/234567890123/infront/:
  environments:
    production:
        assume_role_arn: arn:aws:iam::234567890123:role/terraform-prod
        parameters: '${path}/parameters/production/production.tfvars'
        backend_path: '${path}/parameters/production/backend.tfvars'
```
