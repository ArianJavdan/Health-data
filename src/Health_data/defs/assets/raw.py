import dagster as dg
import polars as pl
import zipfile
import xml.etree.ElementTree as et
from dagster import AssetExecutionContext

@dg.asset
def raw_data() -> None:
    with open("data/bronze/export.zip", "rb") as f:
        zipfile.ZipFile(f).extractall("data/silver")

@dg.asset
def xml_data(context: AssetExecutionContext) -> None:
    tree = et.parse("data/silver/apple_health_export/export.xml")
    root = tree.getroot()
    data = []
    for record in root:
        data.append(record.attrib)
        context.log.info(record)
        return
    df = pl.DataFrame(data)
    df.write_parquet("data/gold/health_data.parquet")