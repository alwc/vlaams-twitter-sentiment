"""Terraform tasks."""

import json
import logging
import os

from invoke import Context, call, task

from . import aws, utils

logger = logging.getLogger(__name__)
REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TERRAFORM_PATH = os.path.join(REPO_PATH, "terraform")
TFVARS_FILEPATH = os.path.join(
    REPO_PATH, "src", "sentiment_flanders", "config", "terraform.tfvars.json"
)
print ("variable REPO_PATH = ", REPO_PATH)
print ("variable TERRAFORM_PATH = ", TERRAFORM_PATH)
print ("variable TFVARS_FILEPATH = ", TFVARS_FILEPATH)


def terraform_backend_name() -> str:
    """Get the name of the Terraform backend for the active workspace."""
    return f"vo-vsa-twitter-state-bucket"


def terraform_state_name(c: Context) -> str:
    """Get the name of the Terraform state file."""
    tfstate_name = "terraform"
    return tfstate_name


@task(call(aws.role, session_name="terraform-init-session", duration=900, write_dotenv=False))
def init(c):
    """Create the Terraform backend for the workspace corresponding to the active git branch."""
    import boto3
    from botocore.exceptions import ClientError

    s3 = boto3.resource("s3", region_name=aws.ENV["AWS_DEFAULT_REGION"])
    bucket_name = terraform_backend_name()
    try:
        bucket_exists = True
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError:
        bucket_exists = False
    if bucket_exists:
        logger.info(f"Terraform backend {bucket_name} is available!")
    else:
        logger.info(f"Creating Terraform backend {bucket_name} ...")
        bucket = s3.Bucket(bucket_name)
        bucket.create(
            CreateBucketConfiguration={"LocationConstraint": aws.ENV["AWS_DEFAULT_REGION"]}
        )
        bucket.wait_until_exists()
        s3 = boto3.client("s3", region_name=aws.ENV["AWS_DEFAULT_REGION"])
        s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"})
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )


def terraform_init_and_select_workspace(c: Context) -> None:
    """Initialise Terraform and select the workspace corresponding to the active git branch."""
    # Delete the local Terraform state to avoid issues.
    # CLOUDAR REMOVE
    # c.run("rm -rf .terraform/modules/ .terraform/environment .terraform/*.tfstate", hide="out")

    # Select the Terraform workspace.
    c.run(
        f"terraform init "
        f"-backend-config=\"region=eu-west-1\" "
        f'-backend-config="bucket=vo-vsa-twitter-state-bucket" '
        f'-backend-config="key=terraform.tfstate"',
        env=aws.ENV,
    )
    # CLOUDAR REMOVE
    #c.run(
    #    f"terraform workspace new {aws.ENV['WORKSPACE']} || terraform workspace select {aws.ENV['WORKSPACE']}",
    #    env=aws.ENV,
    #)


@task(
    pre=[
        call(init),
        call(aws.role, session_name="terraform-deploy-session", duration=900, write_dotenv=False),
    ]
)
def deploy(c, force=False):
    """Deploy the desired Terraform state to the active workspace account."""
    import boto3
    from botocore.exceptions import ClientError
 
    # Determine the deployed Terraform state, if there is one.
    ssm = boto3.client("ssm", region_name="eu-west-1")
    try:
        deployed_terraform_state = json.loads(ssm.get_parameter(
            Name=f"/default/sentiment-flanders/latest",
            WithDecryption=True,
        ).get("Parameter", {}).get("Value", "{}")).get("terraform_state_hash", "undefined")
    except ClientError:
        deployed_terraform_state = "undefined"
 
    # Determine the desired Terraform state.
    with c.cd(TERRAFORM_PATH):
        with open(TFVARS_FILEPATH) as tfvars:
            tfvars = json.load(tfvars)
        with open(TFVARS_FILEPATH, "w") as f:
            tfvars["git_branch"] = utils.current_git_branch(c)
            json.dump(tfvars, f, indent=2)
        desired_terraform_state = c.run(
            r'(find . -type f -not -path "*/\.*" -exec shasum {} + ; '
            r"shasum ../src/sentiment_flanders/config/terraform.tfvars.json) | "
            r"sort | shasum | cut -c -8",
            hide="out",
        ).stdout.strip()
 
    # Deploy with Terraform if the desired state is different from the deployed state.
    if not force and desired_terraform_state == deployed_terraform_state:
        logger.info("Infrastructure is up to date!")
    else:
        logger.info(
            f"Provisioning infrastructure (desired={desired_terraform_state} != deployed={deployed_terraform_state})..."
        )
        with c.cd(TERRAFORM_PATH):
            # Select the Terraform workspace.
            terraform_init_and_select_workspace(c)
 
            # Generate deployment info to include in the runtime config.
            # deploy = {
            #     "deploy_id": terraform_state_name(c),
            #     "git_ref": c.run("git rev-parse HEAD", hide="out").stdout[:8],
            #     "git_commit_datetime": c.run("git log -1 --format=%ai", hide="out").stdout.strip(),
            #     "git_commit_author": c.run("git log -1 --format=%ae", hide="out").stdout.strip(),
            #     "gitlab_pipeline_url": os.environ.get("CI_PIPELINE_URL", ""),
            #     "terraform_state_hash": desired_terraform_state,
            # }
 
            # TODO: Uncomment to remove previous compute environment
            # c.run(
            #     f"terraform state rm 'module.scheduled_batch_job.module.batch_compute_environment.aws_batch_compute_environment.compute_environment' ",
            #     env=aws.ENV,
            # )

            # Apply the changes.
            
            c.run(
                f"terraform apply -input=false -auto-approve "
                f"-var-file='{TFVARS_FILEPATH}' "
                # f"-var='deploy={json.dumps(deploy, indent=None)}'",
                # env=aws.ENV,
            )


@task(
    pre=[
        call(aws.role, session_name="terraform-destroy-session", duration=900, write_dotenv=False)
    ]
)
def destroy(c, dry_run=True):
    """Destroy the Terraform state on the active workspace account."""
    nodeploy = "{}"
    if dry_run:
        logger.info("Generating Terraform destroy plan...")
        with c.cd(TERRAFORM_PATH):
            # Select the Terraform workspace.
            terraform_init_and_select_workspace(c)
            # Dry run the destroy.
            c.run(
                f"terraform plan -destroy "
                f"-var-file='{TFVARS_FILEPATH}' "
                f"-var='deploy={nodeploy}'",
                env=aws.ENV,
            )
    else:
        logger.warning("Destroying Terraform deployment...")
        with c.cd(TERRAFORM_PATH):
            # Select the Terraform workspace.
            terraform_init_and_select_workspace(c)
            # Destroy the state.
            c.run(
                f"terraform destroy -input=false -auto-approve "
                f"-var-file='{TFVARS_FILEPATH}' "
                f"-var='deploy={nodeploy}'",
                env=aws.ENV,
            )


@task(pre=[call(aws.role, session_name="terraform-show-session", duration=900, write_dotenv=False)])
def show(c):
    """Show the resources managed by Terraform on the active workspace account."""
    with c.cd(TERRAFORM_PATH):
        terraform_init_and_select_workspace(c)
        c.run("terraform show", env=aws.ENV)
