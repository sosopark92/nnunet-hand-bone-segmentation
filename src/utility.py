import SimpleITK as sitk
from pathlib import Path


def convert_mhd_to_nii(input_mhd, output_nii):
    image = sitk.ReadImage(input_mhd)
    sitk.WriteImage(image, output_nii)
    print(f"Converted {input_mhd} to {output_nii}")
