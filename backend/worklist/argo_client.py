import requests
import urllib3
from django.conf import settings

# The cluster's API server uses a self-signed cert for local dev.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WORKFLOW_TEMPLATE_NAME = 'monai-spleen-segmentation'
NAMESPACE = 'argo'

# Django talks directly to the Kubernetes API server's CRD endpoints for
# Workflow objects (via workflowTemplateRef), not to Argo Server's own REST
# API. On Docker Desktop's Kubernetes, LoadBalancer/NodePort services (and
# even the apiserver's services/proxy and pods/proxy subresources) aren't
# reachable from other Docker containers - only the apiserver's plain CRUD
# endpoints are, since those only need etcd access, not a route to a pod IP.
# See cluster/README.md for the full story.


def _headers():
    return {'Authorization': f'Bearer {settings.ARGO_TOKEN}'}


def submit_segmentation_workflow(study_instance_uid, series_instance_uid):
    """Create a Workflow referencing the MONAI spleen-segmentation
    WorkflowTemplate. Returns the created workflow's name."""
    payload = {
        'apiVersion': 'argoproj.io/v1alpha1',
        'kind': 'Workflow',
        'metadata': {'generateName': f'{WORKFLOW_TEMPLATE_NAME}-'},
        'spec': {
            'workflowTemplateRef': {'name': WORKFLOW_TEMPLATE_NAME},
            'arguments': {
                'parameters': [
                    {'name': 'study-instance-uid', 'value': study_instance_uid},
                    {'name': 'series-instance-uid', 'value': series_instance_uid},
                ],
            },
        },
    }
    resp = requests.post(
        f'{settings.ARGO_SERVER_URL}/apis/argoproj.io/v1alpha1/namespaces/{NAMESPACE}/workflows',
        json=payload,
        headers=_headers(),
        verify=False,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['metadata']['name']


def get_workflow_status(workflow_name):
    """Returns one of Pending/Running/Succeeded/Failed/Error."""
    resp = requests.get(
        f'{settings.ARGO_SERVER_URL}/apis/argoproj.io/v1alpha1/namespaces/{NAMESPACE}/workflows/{workflow_name}',
        headers=_headers(),
        verify=False,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get('status', {}).get('phase', 'Pending')
