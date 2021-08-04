import json
import logging
import os

import azure.functions as func

from ..exports_store import ExportsTableStore

from ..tenable_helper import get_vuln_export_url, TenableStatus
from ..azure_sentinel import AzureSentinel
from tenable.io import TenableIO

connection_string = os.environ['AzureWebJobsStorage']
vuln_table_name = os.environ['TenableVulnExportTable']
workspace_id = os.environ['WorkspaceID']
workspace_key = os.environ['WorkspaceKey']
log_analytics_uri = os.environ.get('LogAnalyticsUri')
log_type = 'Tenable_IO_Vuln_CL'

logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
logger.setLevel(logging.WARNING)

vendor = os.environ['PyTenableUAVendor'] if 'PyTenableUAVendor' in os.environ else 'Microsoft'
product = os.environ['PyTenableUAProduct'] if 'PyTenableUAProduct' in os.environ else 'Azure Sentinel'
build = os.environ['PyTenableUABuild'] if 'PyTenableUABuild' in os.environ else '0.0.1'


def main(msg: func.QueueMessage) -> None:
    logging.info('Python queue trigger function processed a queue item: %s',
                 msg.get_body().decode('utf-8'))
    decoded_message = msg.get_body().decode('utf-8')

    try:
        export_job_details = json.loads(decoded_message)
        export_job_id = export_job_details['exportJobId'] if 'exportJobId' in export_job_details else ''
        chunk_id = export_job_details['chunkId'] if 'chunkId' in export_job_details else ''

        if export_job_id == '' or chunk_id == '':
            logging.warn('missing information to process a chunk')
            logging.warn(f'message sent - {decoded_message}')
            raise Exception(f'cannot process without export job ID and chunk ID -- found job ID {export_job_id} - chunk ID {chunk_id}')
        else:
            logging.info(
                'using pyTenable client to download asset export job chunk')
            logging.info(
                f'downloading chunk at {get_vuln_export_url()}/{export_job_id}/chunks/{chunk_id}')
            tio = TenableIO(build=build, product=product, vendor=vendor)
            r = tio.get(
                f'{get_vuln_export_url()}/{export_job_id}/chunks/{chunk_id}')
            logging.info(
                f'received a response from {get_vuln_export_url()}/{export_job_id}/chunks/{chunk_id}')
            logging.warn(r.status_code)
            if r.status_code == 200 and r.status_code <= 299:
                # Send to Azure Sentinel here
                az_sentienl = AzureSentinel(workspace_id, workspace_key, log_type, log_analytics_uri)
                az_code = az_sentienl.post_data(json.dumps(r.json()))
                logging.warn(f'Azure Sentinel reports the following status code: {az_code}')
                if (az_code >= 200 and az_code <= 299):
                    vuln_table = ExportsTableStore(
                        connection_string, vuln_table_name)
                    if vuln_table.get(export_job_id, chunk_id) is not None:
                        vuln_table.merge(export_job_id, str(chunk_id), {
                            'jobStatus': TenableStatus.finished.value
                        })
                else:
                    logging.warn(
                        f'Failure to send to Azure Sentinel. Response code: {az_code}')
                    raise Exception(
                        f'Sending to Azure Sentinel failed with status code {az_code}')
            else:
                request_id = r.headers['X-Request-Uuid'] if 'X-Request-Uuid' in r.headers else ''
                logging.warn(
                        f'Failure to retrieve vuln data from Tenable. Response code: {r.status_code} Request ID: {request_id} Export Job ID: {export_job_id} Chunk ID: {chunk_id}')
                raise Exception(
                    f'Retrieving from Tenable failed with status code {r.status_code}')

    except Exception as e:
        vuln_table = ExportsTableStore(connection_string, vuln_table_name)
        if vuln_table.get(export_job_id, chunk_id) is not None:
            vuln_table.merge(export_job_id, str(chunk_id), {
                'jobStatus': TenableStatus.failed.value
            })
        logging.warn(
            f'there was an error processing chunks. message sent - {decoded_message}')
        logging.warn(e)
        return
