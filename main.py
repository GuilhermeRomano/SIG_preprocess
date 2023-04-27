import rasterio
import rasterio.mask
import numpy as np
import fiona
import os
import csv

DATA_FOLDER = "data"
RAW_FOLDER = "IMAGENS_PLANET"
NDVI_FOLDER = "nvdi_images"
CLIP_FOLDER = "clip_images"
RESULT_FILE = "results.csv"
GEO_NAME = "gleba01.geojson"
HEADER = ["sample_date", "avg_ndvi"]


def extract_ndvi(path_to_file: str) -> None:
    src = rasterio.open(path_to_file)
    band_red = src.read(3)
    band_nir = src.read(4)

    # Allow division by zero
    np.seterr(divide="ignore", invalid="ignore")

    # Calculate NDVI
    ndvi = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)

    # Set spatial characteristics of the output object to mirror the input
    kwargs = src.meta
    kwargs.update(dtype=rasterio.float32, count=1)

    image_name = os.path.splitext(path_to_file)[0]
    # Create the file
    output_file = os.path.join(DATA_FOLDER, NDVI_FOLDER, image_name)
    with rasterio.open(output_file, "w", **kwargs) as dst:
        dst.write_band(1, ndvi.astype(rasterio.float32))
    return None


def clip_image(path_to_file: str) -> None:
    geo_file = os.path.join(DATA_FOLDER, GEO_NAME)

    with fiona.open(geo_file, "r", driver="GeoJSON") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

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

    image_name = os.path.splitext(path_to_file)[0]
    output_file = os.path.join(DATA_FOLDER, CLIP_FOLDER, image_name)

    with rasterio.open(output_file, "w", **out_meta) as dest:
        dest.write(out_image)
    return None


def get_avg_ndvi(path_to_file: str) -> dict[str, str] | None:
    src = rasterio.open(path_to_file)
    band = src.read(1)
    avg = np.average(band)

    sample_results = {}

    image_name = os.path.splitext(path_to_file)[0]
    base_name = os.path.splitext(image_name)[0]
    sample_date = "_".join(base_name.split("_")[0:2])

    sample_results["sample_date"] = sample_date
    sample_results["avg_ndvi"] = avg
    return sample_results


def main() -> None:
    raw_path = os.path.join(DATA_FOLDER, RAW_FOLDER)
    ndvi_path = os.path.join(DATA_FOLDER, NDVI_FOLDER)
    clip_path = os.path.join(DATA_FOLDER, NDVI_FOLDER)
    # Iterate over raw folder and save result images in ndvi folder
    for filename in os.listdir(raw_path):
        extract_ndvi(filename)

    # Iterate over ndvi folder and save result images in clipped images folder
    for filename in os.listdir(ndvi_path):
        clip_image(filename)

    results = []
    for filename in os.listdir(clip_path):
        sample_results = get_avg_ndvi(filename)
        results.append(sample_results)

    output_file = os.path.join(DATA_FOLDER, "results.csv")
    with open(output_file, "w") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=HEADER, delimiter=",", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
