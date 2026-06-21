"""
Pulls a CT series from Orthanc, runs the MONAI Model Zoo
'spleen_ct_segmentation' bundle on it, encodes the resulting mask as a
DICOM-SEG instance, and pushes it back into Orthanc as part of the same
study.

The bundle's own configs/inference.json handles preprocessing, inference,
and - critically - inverts its resampling back to the original image's
geometry (see the Invertd transform), so the output mask we read back
already aligns 1:1 with the source series' pixel grid.
"""

import argparse
import glob
import os
import subprocess
import sys
import tempfile

import highdicom as hd
import numpy as np
import pydicom
import requests
import SimpleITK as sitk
from pydicom.sr.codedict import codes

BUNDLE_ROOT = "/opt/monai/bundles/spleen_ct_segmentation"


def orthanc_auth():
    return (os.environ["ORTHANC_USERNAME"], os.environ["ORTHANC_PASSWORD"])


def orthanc_url():
    return os.environ["ORTHANC_URL"].rstrip("/")


def lookup_orthanc_id(dicom_uid, expected_type):
    """Resolve a DICOM UID (Study/Series Instance UID) to Orthanc's internal resource ID."""
    resp = requests.post(
        f"{orthanc_url()}/tools/lookup",
        data=dicom_uid,
        auth=orthanc_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    matches = [m for m in resp.json() if m["Type"] == expected_type]
    if not matches:
        raise RuntimeError(f"No Orthanc {expected_type} found for UID {dicom_uid}")
    return matches[0]["ID"]


def download_series_instances(series_orthanc_id, dest_dir):
    """Download every instance in the series as a .dcm file. Returns the list of paths."""
    resp = requests.get(
        f"{orthanc_url()}/series/{series_orthanc_id}/instances",
        auth=orthanc_auth(),
        timeout=30,
    )
    resp.raise_for_status()
    instance_ids = [i["ID"] for i in resp.json()]

    paths = []
    for instance_id in instance_ids:
        file_resp = requests.get(
            f"{orthanc_url()}/instances/{instance_id}/file",
            auth=orthanc_auth(),
            timeout=60,
        )
        file_resp.raise_for_status()
        path = os.path.join(dest_dir, f"{instance_id}.dcm")
        with open(path, "wb") as f:
            f.write(file_resp.content)
        paths.append(path)
    return paths


def upload_instance(dicom_path):
    with open(dicom_path, "rb") as f:
        resp = requests.post(
            f"{orthanc_url()}/instances",
            data=f.read(),
            headers={"Content-Type": "application/dicom"},
            auth=orthanc_auth(),
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()


def run_bundle_inference(dataset_dir, output_dir):
    """Invoke the MONAI bundle's own published inference config via its CLI."""
    cmd = [
        sys.executable,
        "-m",
        "monai.bundle",
        "run",
        "--config_file",
        os.path.join(BUNDLE_ROOT, "configs/inference.json"),
        "--bundle_root",
        BUNDLE_ROOT,
        "--dataset_dir",
        dataset_dir,
        "--output_dir",
        output_dir,
        # The published checkpoint was saved from a CUDA run; remap it to
        # CPU explicitly since this pipeline has no GPU.
        "--checkpointloader#map_location",
        "cpu",
    ]
    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def build_segmentation_instance(mask_array, source_datasets, output_path):
    segment_description = hd.seg.SegmentDescription(
        segment_number=1,
        segment_label="Spleen",
        segmented_property_category=codes.SCT.Organ,
        segmented_property_type=codes.SCT.Spleen,
        algorithm_type=hd.seg.SegmentAlgorithmTypeValues.AUTOMATIC,
        algorithm_identification=hd.AlgorithmIdentificationSequence(
            name="MONAI spleen_ct_segmentation",
            version="1.0.0",
            family=codes.DCM.ArtificialIntelligence,
        ),
    )

    seg_dataset = hd.seg.Segmentation(
        source_images=source_datasets,
        pixel_array=mask_array.astype(np.uint8),
        segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
        segment_descriptions=[segment_description],
        series_instance_uid=hd.UID(),
        series_number=100,
        sop_instance_uid=hd.UID(),
        instance_number=1,
        manufacturer="MONAI",
        manufacturer_model_name="spleen_ct_segmentation",
        software_versions="1.0.0",
        device_serial_number="monai-pipeline",
    )
    seg_dataset.save_as(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--series-uid", required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as workdir:
        dicom_dir = os.path.join(workdir, "dicom")
        dataset_dir = os.path.join(workdir, "dataset", "imagesTs")
        output_dir = os.path.join(workdir, "output")
        os.makedirs(dicom_dir)
        os.makedirs(dataset_dir)
        os.makedirs(output_dir)

        # Orthanc's REST API is keyed by its own internal IDs, not DICOM UIDs,
        # so resolve those first.
        lookup_orthanc_id(args.study_uid, "Study")  # validates the study exists
        series_id = lookup_orthanc_id(args.series_uid, "Series")

        print(f"Downloading series {args.series_uid} (Orthanc ID {series_id})...", flush=True)
        dicom_paths = download_series_instances(series_id, dicom_dir)
        if not dicom_paths:
            raise RuntimeError("Series has no instances")

        # SimpleITK sorts the series into a single coherent volume; this
        # ordering is what mask_array's slice order will need to match later.
        sorted_filenames = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(dicom_dir)
        if not sorted_filenames:
            sorted_filenames = dicom_paths  # fallback for single-instance series
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(sorted_filenames)
        reference_image = reader.Execute()

        nifti_path = os.path.join(dataset_dir, "case.nii.gz")
        sitk.WriteImage(reference_image, nifti_path)

        print("Running MONAI bundle inference...", flush=True)
        run_bundle_inference(os.path.dirname(dataset_dir), output_dir)

        output_candidates = glob.glob(
            os.path.join(output_dir, "case", "case_trans.nii.gz")
        )
        if not output_candidates:
            output_candidates = glob.glob(os.path.join(output_dir, "**", "*.nii.gz"), recursive=True)
        if not output_candidates:
            raise RuntimeError(f"Bundle produced no output in {output_dir}")

        mask_image = sitk.ReadImage(output_candidates[0])
        mask_array = sitk.GetArrayFromImage(mask_image)

        reference_array_shape = sitk.GetArrayFromImage(reference_image).shape
        # A single-slice source series has a singleton leading (z) dimension
        # that the NIfTI round-trip through the bundle can drop; restore it
        # rather than treating it as a real mismatch.
        if mask_array.ndim == len(reference_array_shape) - 1 and reference_array_shape[0] == 1:
            mask_array = mask_array[None, ...]

        if mask_array.shape != reference_array_shape:
            raise RuntimeError(
                f"Mask shape {mask_array.shape} does not match source series "
                f"shape {reference_array_shape} - inversion back to original "
                "geometry did not line up as expected"
            )

        source_datasets = [pydicom.dcmread(f) for f in sorted_filenames]

        seg_path = os.path.join(workdir, "segmentation.dcm")
        print("Encoding DICOM-SEG...", flush=True)
        build_segmentation_instance(mask_array, source_datasets, seg_path)

        print("Uploading segmentation to Orthanc...", flush=True)
        result = upload_instance(seg_path)
        print("Done:", result, flush=True)


if __name__ == "__main__":
    main()
