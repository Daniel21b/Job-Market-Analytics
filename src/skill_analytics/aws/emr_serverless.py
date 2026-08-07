import asyncio
from typing import Any

import boto3

from skill_analytics.config import Settings

TERMINAL_STATES = {"SUCCESS", "FAILED", "CANCELLED"}


class EmrServerlessError(RuntimeError):
    pass


class EmrServerlessRunner:
    def __init__(self, settings: Settings) -> None:
        required = {
            "application_id": settings.aws_emr_serverless_application_id,
            "execution_role": settings.aws_emr_serverless_execution_role_arn,
            "entrypoint": settings.aws_emr_serverless_entrypoint_uri,
            "log_uri": settings.aws_emr_serverless_log_uri,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise EmrServerlessError(f"missing EMR Serverless settings: {', '.join(missing)}")
        self.settings = settings
        self.client = boto3.client("emr-serverless", region_name=settings.aws_region)

    async def submit_and_wait(self, message: dict[str, object]) -> dict[str, object]:
        arguments = [
            "--input-uri",
            str(message["input_uri"]),
            "--output-uri",
            str(message["output_uri"]),
            "--taxonomy-path",
            self.settings.skill_taxonomy_path,
            "--master",
            "yarn",
            "--partitions",
            str(message.get("partitions", self.settings.spark_partitions)),
            "--minimum-canonical-skills",
            str(self.settings.minimum_canonical_skills),
            "--optimized" if bool(message.get("optimized", True)) else "--no-optimized",
        ]
        request: dict[str, Any] = {
            "applicationId": self.settings.aws_emr_serverless_application_id,
            "executionRoleArn": self.settings.aws_emr_serverless_execution_role_arn,
            "name": f"skill-analytics-{message['run_id']}",
            "jobDriver": {
                "sparkSubmit": {
                    "entryPoint": self.settings.aws_emr_serverless_entrypoint_uri,
                    "entryPointArguments": arguments,
                    "sparkSubmitParameters": (
                        "--conf spark.sql.adaptive.enabled=true "
                        "--conf spark.sql.adaptive.skewJoin.enabled=true"
                    ),
                }
            },
            "configurationOverrides": {
                "monitoringConfiguration": {
                    "s3MonitoringConfiguration": {
                        "logUri": self.settings.aws_emr_serverless_log_uri
                    }
                }
            },
        }
        submitted = await asyncio.to_thread(self.client.start_job_run, **request)
        job_run_id = submitted["jobRunId"]

        while True:
            response = await asyncio.to_thread(
                self.client.get_job_run,
                applicationId=self.settings.aws_emr_serverless_application_id,
                jobRunId=job_run_id,
            )
            job = response["jobRun"]
            state = job["state"]
            if state in TERMINAL_STATES:
                if state != "SUCCESS":
                    raise EmrServerlessError(
                        f"EMR Serverless job {job_run_id} ended in {state}: "
                        f"{job.get('stateDetails', 'no details')}"
                    )
                return {
                    "execution_backend": "emr-serverless",
                    "aws_application_id": self.settings.aws_emr_serverless_application_id,
                    "aws_job_run_id": job_run_id,
                    "aws_state": state,
                    "output_uri": str(message["output_uri"]),
                }
            await asyncio.sleep(10)
