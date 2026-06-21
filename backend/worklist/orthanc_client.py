import requests
from django.conf import settings

from .models import Study


def _auth():
    return (settings.ORTHANC_USERNAME, settings.ORTHANC_PASSWORD)


def sync_studies_from_orthanc():
    """Pull study list from Orthanc's native REST API and upsert into the local cache."""
    study_ids = requests.get(
        f'{settings.ORTHANC_URL}/studies', auth=_auth(), timeout=10
    ).json()

    for study_id in study_ids:
        detail = requests.get(
            f'{settings.ORTHANC_URL}/studies/{study_id}', auth=_auth(), timeout=10
        ).json()
        tags = detail.get('MainDicomTags', {})
        patient_tags = detail.get('PatientMainDicomTags', {})

        series = requests.get(
            f'{settings.ORTHANC_URL}/studies/{study_id}/series', auth=_auth(), timeout=10
        ).json()
        modalities = sorted(
            {s.get('MainDicomTags', {}).get('Modality', '') for s in series} - {''}
        )

        Study.objects.update_or_create(
            study_instance_uid=tags.get('StudyInstanceUID', study_id),
            defaults={
                'patient_name': patient_tags.get('PatientName', ''),
                'patient_id': patient_tags.get('PatientID', ''),
                'study_date': tags.get('StudyDate', ''),
                'study_description': tags.get('StudyDescription', ''),
                'modalities': ', '.join(modalities),
            },
        )


def proxy_request(method, subpath, query_string=b'', body=b'', headers=None):
    """Forward a DICOMweb request to Orthanc with server-side basic auth."""
    url = f'{settings.ORTHANC_URL}/dicom-web/{subpath}'
    if query_string:
        url += f'?{query_string.decode()}'

    forward_headers = {}
    for key in ('Accept', 'Content-Type'):
        if headers and headers.get(key):
            forward_headers[key] = headers[key]

    return requests.request(
        method=method,
        url=url,
        data=body or None,
        headers=forward_headers,
        auth=_auth(),
        timeout=30,
    )
