


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

### Available configuration options
option | type | description
-----: | ---- | :----------
assume_role_arn | `string` | The IAM Role to Assume
backend_config | `string` OR `dict` | Path to the backend configuration file
vars_file | `string` | Path to a variables file
variables | `dict` | A key/value dictionary

### YAML Configuration Syntax
```yaml
[path_to_terraform]:
  assume_role_arn: [role_arn]
  backend_config: [backend_config_file]
  backend_config:
    bucket: [bucket_name]
    region: [bucket_region]
    acl: [bucket_acl]
    key: [path_to_state_in_s3]
  vars_file: [path_to_tfvars_file]
  variables:
    [var_key]: [var_value]
```
#### Notes
* [path_to_terraform] - at present must be a relative or absolute path, doesn't CURRENTLY support using tildes. This path must currently match to exactly how you put it in the CLI (though trailing slashes are ignored).
* If passing a dictionary to the backend_config key you need to pass the **bucket**, **region**, **acl** and **key** keys, otherwise Terraform won't work.

### Sample YAML Config
```yaml
terraform:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform'

terraform/123456789012:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform'
terraform/123456789012/eu-west-1/production:
  backend_config: '${path}/parameters/backend.tfvars'
  vars_file: '${path}/parameters/production.tfvars'
terraform/123456789012/eu-west-1/development:
  assume_role_arn: 'arn:aws:iam::123456789012:role/terraform-production'
  backend_config: '${path}/parameters/backend.tfvars'
  variables:
    my_key: my_value

terraform/234567890123/my_app/:
  environments:
    production:
      assume_role_arn: arn:aws:iam::234567890123:role/terraform-prod
      vars_file: '${path}/parameters/production/production.tfvars'
      backend_config:
        bucket: "my_state_bucket"
        region: "eu-west-1"
        acl: "bucket-owner-full-control"
        key: "my_state_file.tfstate"

```

## TODO
* Allow more than 1 variables file
* Allow for backend_config to be a path, variables or both
* Configure tflint / tfsec to be executed if found in $PATH (disabled by passing disable_tfsec: true in the YAML)
* Allow quieter mode, maybe?

## Notes
* It is possible to have duplicate config by adding a path with a trailing slash and without, this is not recommended.
