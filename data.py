import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import polars as pl
    from xml.etree.ElementTree import iterparse
    import xml.etree.ElementTree as et
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    xml_path = "data/silver/apple_health_export/export.xml"
    return iterparse, pa, pd, pl, pq, xml_path


@app.cell
def _(TAGS, iterparse, pa, pd, pq, xml_path):
    writers, bufs, schemas, root = {}, {}, {}, None

    def flush(tag, buf):
       df = pd.DataFrame(buf).fillna("").astype(str).apply(lambda c: c.str[:512])
       if tag in schemas:
           df = df.reindex(columns=schemas[tag], fill_value="")
       schema = pa.schema([(c, pa.string()) for c in df.columns])
       table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
       if tag not in writers:
           schemas[tag] = list(df.columns)
           writers[tag] = pq.ParquetWriter(f"{tag}.parquet", schema, data_page_size=1024*1024)
       writers[tag].write_table(table)

    for event, elem in iterparse(xml_path, events=("start", "end")):
       if event == "start" and root is None:
           root = elem
       if event == "end" and elem.tag in TAGS:
           tag = elem.tag
           bufs.setdefault(tag, []).append(elem.attrib)
           if len(bufs[tag]) >= 1_000:
               flush(tag, bufs[tag])
               bufs[tag] = []
           root.clear()

    for tag, buf in bufs.items():
       if buf: flush(tag, buf)

    for w in writers.values(): w.close()

    return


@app.cell
def _(pl):
    record = pl.read_parquet("data/silver/Record.parquet")
    record
    return


@app.cell
def _():
    return


@app.cell
def _(pl):
    workout = pl.read_parquet("data/silver/Workout.parquet")
    workout.filter(pl.col("sourceName") == "Liftosaur")
    return


if __name__ == "__main__":
    app.run()
