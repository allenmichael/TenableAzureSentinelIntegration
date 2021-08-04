import json
import os
import logging

from tenable.io import TenableIO
from ..tenable_helper import get_asset_export_url

default_chunk_size = os.environ['TenableDefaultAssetChunkSize']

vendor = os.environ['PyTenableUAVendor'] if 'PyTenableUAVendor' in os.environ else 'Microsoft'
product = os.environ['PyTenableUAProduct'] if 'PyTenableUAProduct' in os.environ else 'Azure Sentinel'
build = os.environ['PyTenableUABuild'] if 'PyTenableUABuild' in os.environ else '0.0.1'

def main(timestamp: int) -> object:
    logging.info('using pyTenable client to create new asset export job')
    tio = TenableIO(vendor=vendor, product=product, build=build)
    body = {'chunk_size': default_chunk_size}
    body['updated_at'] = timestamp
    
    logging.info(
        f'sending {json.dumps(body)} to {get_asset_export_url()}')
    r = tio.post(get_asset_export_url(), data=json.dumps(body))
    logging.info(f'received a response from {get_asset_export_url()}')
    logging.info(r.text)
    logging.info(r.json())
    return r.json()
