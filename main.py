import rasterio
import rasterio.mask
import numpy as np
import fiona
import os
import csv

DATA_FOLDER = "data"
RAW_FOLDER = "IMAGENS_PLANET"
NDVI_FOLDER = "ndvi_images"
CLIP_FOLDER = "clip_images"
RESULT_FILE = "results.csv"
GEO_NAME = "gleba01.geojson"
HEADER = ["sample_date", "avg_ndvi"]


def extract_ndvi(path_to_file: str) -> None:
    """Extreacts NDVI value for each pixel in a image
    containing Blue, Green, Red and Near Infrared bands.
    Saves this new band and related metadata as a new image.

    Args:
        path_to_file (str): path to image file.

    Returns:
        None
    """
    src = rasterio.open(path_to_file)
    band_red = src.read(3)
    band_nir = src.read(4)

    # Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")

    # Calculate NDVI
    ndvi = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)

    # Set spatial characteristics of the output object to mirror the input.
    out_meta = src.meta
    out_meta.update(dtype=rasterio.float32, count=1)

    image_name = os.path.basename(path_to_file)
    # Create the file
    output_file = os.path.join(DATA_FOLDER, NDVI_FOLDER, image_name)
    with rasterio.open(output_file, "w", **out_meta) as dst:
        dst.write_band(1, ndvi.astype(rasterio.float32))
    return None


def clip_image(path_to_file: str) -> None:
    """Clips an image using a shape file, in this case a GeoJSON file.
    Saves new clipped image as a new file in another folder.

    Args:
        path_to_file (str): path to image file.

    Returns:
        None
    """
    geo_file = os.path.join(DATA_FOLDER, GEO_NAME)

    # get shapefile
    with fiona.open(geo_file, "r", driver="GeoJSON") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

    # Get new cropped image and metadata
    with rasterio.open(path_to_file) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta

    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        }
    )

    # export
    image_name = os.path.basename(path_to_file)
    output_file = os.path.join(DATA_FOLDER, CLIP_FOLDER, image_name)

    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(out_image)
    return None


def get_avg_ndvi(path_to_file: str) -> dict[str, str] | None:
    """Gets average value of NDVI in a image. This ignores NaN values.

    Args:
        path_to_file (str): path to image file.

    Returns:
        dict[str, str] | None: Dictonary containing date and mean NDVI value.
    """
    src = rasterio.open(path_to_file)

    # Get mean value ignoring NaN values
    # (possibly exist because of an extraction problem in original file).
    band = src.read(1)
    avg = np.nanmean(band)

    image_name = os.path.basename(path_to_file)
    base_name = os.path.splitext(image_name)[0]
    sample_date = "_".join(base_name.split("_")[0:2])

    sample_results = {}
    sample_results["sample_date"] = sample_date
    sample_results["avg_ndvi"] = avg
    return sample_results


def main() -> None:
    """Executes entire pipeline, saving each intermediary step into a specific folder.
    Can be changed to run in memory instead of saving to disk.
    """
    raw_path = os.path.join(DATA_FOLDER, RAW_FOLDER)
    ndvi_path = os.path.join(DATA_FOLDER, NDVI_FOLDER)
    clip_path = os.path.join(DATA_FOLDER, CLIP_FOLDER)
    # Iterate over raw folder and save result images in ndvi folder.
    for filename in os.listdir(raw_path):
        file_path = os.path.join(raw_path, filename)
        extract_ndvi(file_path)

    # Iterate over ndvi folder and save result images in clipped images folder.
    for filename in os.listdir(ndvi_path):
        file_path = os.path.join(ndvi_path, filename)
        clip_image(file_path)

    results = []
    # Iterate over clipped images folder and get the mean value
    # (ignoring any nan values that may appear).
    for filename in os.listdir(clip_path):
        file_path = os.path.join(clip_path, filename)
        sample_results = get_avg_ndvi(file_path)
        results.append(sample_results)

    # Export to csv.
    output_file = os.path.join(DATA_FOLDER, "results.csv")
    with open(output_file, "w") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=HEADER, delimiter=",", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
