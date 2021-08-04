from enum import Enum

base_url = 'https://cloud.tenable.com'
asset_base_url = 'assets'
asset_export_url = f'{asset_base_url}/export'
vuln_base_url = 'vulns'
vuln_export_url = f'{vuln_base_url}/export'

def get_base_url():
    return base_url

def get_asset_base_url():
    return asset_base_url

def get_asset_export_url():
    return asset_export_url

def get_vuln_base_url():
    return vuln_base_url

def get_vuln_export_url():
    return vuln_export_url

class TenableStatus(Enum):
    finished = 'FINISHED'
    failed = 'FAILED'
    no_job = 'NO_JOB_FOUND'
    processing = 'PROCESSING'
    sending_to_queue = 'SENDING_TO_QUEUE'
    sent_to_queue = 'SENT_TO_QUEUE'
    sent_to_sub_orchestrator = 'SENT_TO_SUB_ORCHESTRATOR'

class TenableExportType(Enum):
    asset = 'ASSET_EXPORT_JOB'
    vuln = 'VULN_EXPORT_JOB'
