import logging
import os

from ..exports_store import ExportsTableStore
from ..exports_queue import ExportsQueue

from ..tenable_helper import get_asset_export_url,TenableStatus,TenableExportType
from tenable.io import TenableIO

connection_string = os.environ['AzureWebJobsStorage']
assets_table_name = os.environ['TenableAssetExportTable']
assets_queue_name = os.environ['TenableAssetExportQueue']

vendor = os.environ['PyTenableUAVendor'] if 'PyTenableUAVendor' in os.environ else 'Microsoft'
product = os.environ['PyTenableUAProduct'] if 'PyTenableUAProduct' in os.environ else 'Azure Sentinel'
build = os.environ['PyTenableUABuild'] if 'PyTenableUABuild' in os.environ else '0.0.1'


def send_chunks_to_queue(exportJobDetails):
    logging.info(f'Sending chunk to queue.')
    chunks = exportJobDetails['chunks_available'] if 'chunks_available' in exportJobDetails else [
    ]
    exportJobId = exportJobDetails['exportJobId'] if 'exportJobId' in exportJobDetails else ''

    if len(chunks) > 0:
        assets_table = ExportsTableStore(connection_string, assets_table_name)
        for chunk in chunks:
            if assets_table.get(exportJobId, chunk) is None:
                assets_table.post(exportJobId, str(chunk), {
                                  'jobStatus': TenableStatus.sending_to_queue.value,
                                  'jobType': TenableExportType.asset.value
                                  })
            
            assets_queue = ExportsQueue(connection_string, assets_queue_name)
            try:
                sent = assets_queue.send_chunk_info(exportJobId, chunk)
                logging.warn(f'chunk queued -- {exportJobId} {chunk}')
                logging.warn(sent)
                assets_table.merge(exportJobId, str(chunk), {
                                   'jobStatus': TenableStatus.sent_to_queue.value
                                   })
            except Exception as e:
                logging.warn(
                    f'Failed to send {exportJobId} - {chunk} to be processed')
                logging.warn(e)
    else:
        logging.info('no chunk found to process.')
        return


def main(exportJobId: str) -> object:
    logging.info('using pyTenable client to check asset export job status')
    logging.info(
        f'checking status at {get_asset_export_url()}/{exportJobId}/status')
    tio = TenableIO(vendor=vendor, product=product, build=build)
    r = tio.get(f'{get_asset_export_url()}/{exportJobId}/status')
    logging.info(
        f'received a response from {get_asset_export_url()}/{exportJobId}/status')
    logging.info(r.text)
    logging.info(r.json())

    try:
        job_details = r.json()
        job_details['exportJobId'] = exportJobId
        send_chunks_to_queue(job_details)
    except Exception as e:
        logging.warn('error while sending chunks to queue')
        logging.warn(job_details)
        logging.warn(e)

    return r.json()
