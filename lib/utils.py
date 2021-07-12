import os
import sys

import boto3
import botocore.exceptions


def assume_client(
    role_arn,
    session_name,
    region_name='us-east-1',
    profile='default'
):
    os.environ['AWS_STS_REGIONAL_ENDPOINTS'] = 'regional'
    os.environ['AWS_RETRY_MODE'] = 'standard'

    try:
        session = boto3.Session(profile_name=profile)
    except botocore.exceptions.ProfileNotFound as exc:
        print(exc)
        sys.exit(1)
    sts = session.client(
        'sts',
        endpoint_url=f'https://sts.{region_name}.amazonaws.com',
        region_name=region_name
    )

    try:
        assume_response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name
        )
    except (
        botocore.exceptions.SSOTokenLoadError,
        botocore.exceptions.UnauthorizedSSOTokenError
    ):
        print('Connect to SSO!')
        sys.exit(1)
    except botocore.exceptions.InfiniteLoopConfigError as error:
        print(f'Invalid Config - Error Message was: \n  {error}')
        sys.exit(1)
    except botocore.exceptions.ClientError as exc:
        print(exc.response.get('Error').get('Message'))
        sys.exit(1)
    except Exception as e:
        print(e)
        return False
    else:
        credentials = assume_response.get("Credentials")
        session_args = {
            'aws_access_key_id': credentials.get("AccessKeyId"),
            'aws_secret_access_key': credentials.get("SecretAccessKey"),
            'aws_session_token': credentials.get("SessionToken"),
        }

        os.environ["AWS_ACCESS_KEY_ID"] = credentials.get('AccessKeyId')
        os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.get('SecretAccessKey')
        os.environ["AWS_SESSION_TOKEN"] = credentials.get('SessionToken')

        return boto3.Session(**session_args)
