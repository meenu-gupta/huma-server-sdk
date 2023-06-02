import logging
from datetime import datetime
from io import BytesIO
from typing import Generator

import pdfkit
from celery.schedules import crontab
from flask import render_template, Flask

from extensions.common.monitoring import report_exception
from extensions.common.s3object import S3Object
from extensions.deployment.exceptions import EConsentPdfGenerationError
from extensions.deployment.models.deployment import Deployment
from extensions.deployment.models.econsent.econsent import EConsent
from extensions.deployment.models.econsent.econsent_log import EConsentLog
from extensions.deployment.models.econsent.econsent_section import EConsentSection
from extensions.deployment.models.stats_calculator import DeploymentStatsCalculator
from extensions.deployment.repository.econsent_repository import EConsentRepository
from extensions.deployment.router.deployment_requests import (
    UpdateDeploymentRequestObject,
)
from extensions.deployment.service.deployment_service import DeploymentService
from sdk.celery.app import celery_app
from sdk.common.adapter.file_storage_adapter import FileStorageAdapter
from sdk.common.constants import SEC_IN_HOUR
from sdk.common.utils import inject
from sdk.common.utils.validators import remove_none_values

app = Flask(__name__, template_folder="service/templates/")

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0),
        calculate_stats_per_deployment.s(),
        name="Deployment stats calculator",
    )


@celery_app.task(expires=SEC_IN_HOUR)
def calculate_stats_per_deployment():
    deployment_service = DeploymentService()
    for deployment in _get_deployments_by_batches(service=deployment_service):
        logger.info(f"Stats Calculation initialized for deployment {deployment.id}")
        stats = DeploymentStatsCalculator(deployment).run()
        deployment_data = {
            UpdateDeploymentRequestObject.ID: deployment.id,
            UpdateDeploymentRequestObject.STATS: stats,
        }
        req_obj = UpdateDeploymentRequestObject.from_dict(deployment_data)
        req_obj.language = None
        req_obj.version = None
        deployment_service.update_deployment(
            req_obj, update_revision=False, set_update_time=False
        )
        logger.info(f"Stats Calculation finished for deployment {deployment.id}")


def _get_deployments_by_batches(
    batch_size=100, service: DeploymentService = None
) -> Generator[Deployment, None, None]:
    skip = 0
    total = 0
    if not service:
        service = DeploymentService()

    while skip == 0 or skip < total:
        deployments, total = service.retrieve_deployments(skip=skip, limit=batch_size)
        if not total:
            break

        skip += batch_size
        yield from iter(deployments)


def _upload_econsent_to_bucket(
    file_storage: FileStorageAdapter,
    filename: str,
    file_data: bytes,
    file_type: str,
    bucket: str,
):
    file_storage.upload_file(
        bucket, filename, BytesIO(file_data), len(file_data), file_type
    )
    return bucket, filename


def _generate_econsent_pdf(
    file_storage: FileStorageAdapter,
    signature: S3Object,
    pdf_url: str,
    sections_list: list[EConsentSection],
    full_name: str,
    title: str,
    answers: list[dict],
    other_strings: dict,
):
    signature = S3Object.from_dict(signature)
    sections = []
    for section in sections_list:
        sections.append(EConsentSection.from_dict(remove_none_values(section)))
    signature_url = file_storage.get_pre_signed_url(signature.bucket, signature.key)
    options = {
        "page-size": "A4",
        "margin-top": "0.75in",
        "margin-right": "0.5in",
        "margin-bottom": "0.5in",
        "margin-left": "0.5in",
        "encoding": "UTF-8",
    }

    date = datetime.utcnow().strftime("%b %d %Y %H:%M GMT").upper()
    with app.app_context():
        html = render_template(
            "econsent_pdf_template.html",
            title=title,
            items=sections,
            signature_url=signature_url,
            full_name=full_name,
            date=date,
            answers=answers,
            other_strings=other_strings,
        )
    pdf = pdfkit.from_string(html, False, options=options)
    return _upload_econsent_to_bucket(
        file_storage, pdf_url, pdf, "application/pdf", signature.bucket
    )


@celery_app.task
def update_econsent_pdf_location(
    econsent: dict,
    econsent_log: dict,
    deployment_id: str,
    full_name: str,
    econsent_log_id: str,
    request_id: str,
    answers: list[dict],
    other_strings: dict,
):
    econsent_repo = inject.instance(EConsentRepository)
    file_storage = inject.instance(FileStorageAdapter)
    revision = str(econsent[EConsent.REVISION])
    pdf_url = f"user/{str(econsent_log[EConsentLog.USER_ID])}/deployment/{deployment_id}/econsent/econsent_revision_{revision}.pdf"
    try:
        bucket, filename = _generate_econsent_pdf(
            file_storage,
            econsent_log[EConsentLog.SIGNATURE],
            pdf_url,
            econsent[EConsent.SECTIONS],
            full_name,
            econsent[EConsent.TITLE],
            answers,
            other_strings,
        )
    except Exception as error:
        context_name = "GenerateEConsent"
        context_content = {
            "econsent": econsent,
            "econsentLog": econsent_log,
        }
        tags = {
            "requestId": request_id,
            "userId": str(econsent_log[EConsentLog.USER_ID]),
            "deploymentId": deployment_id,
            "econsentId": econsent[EConsent.ID],
            "econsentLogId": econsent_log_id,
        }

        report_exception(
            error,
            context_name=context_name,
            context_content=context_content,
            tags=tags,
        )
        raise EConsentPdfGenerationError(error)
    else:
        pdf_location = {
            "key": filename,
            "bucket": bucket,
            "region": econsent_log[EConsentLog.SIGNATURE][S3Object.REGION],
        }
        econsent_repo.update_user_econsent_pdf_location(
            pdf_location=pdf_location, inserted_id=econsent_log_id
        )
