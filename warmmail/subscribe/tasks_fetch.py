from datetime import date

import pandas as pd
import requests
from csci_utils.io import atomic_write
from csci_utils.luigi.requires import Requirement, Requires
from csci_utils.luigi.target import TargetOutput
from luigi import DateParameter, LocalTarget, Parameter
from luigi.task import Task


class DownloadAQI(Task):

    __version__ = "v0.1.0"

    output = TargetOutput(
        factory=LocalTarget,
        file_pattern="data/waqi-covid19-airqualitydata-2020-{task.date}",
        ext="csv",
    )

    date = DateParameter(default=date.today())

    def run(self):
        remote_url = "https://aqicn.org/data-platform/covid19/report/23262-7905da53/"
        with atomic_write(self.output().path, "wb") as f:
            with requests.get(remote_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
            # TODO: check if generated date is not the same date as expected date, then, discard without saving


class ConvertAQIFileToParquet(Task):

    __version__ = "v0.1.0"

    requires = Requires()
    download = Requirement(DownloadAQI)
    date = DateParameter(default=date.today())

    path = Parameter(default="data/AQI_Data")

    output = TargetOutput(
        factory=LocalTarget,
        file_pattern="{task.path}-{task.date}",
        ext="parquet",
    )

    def run(self):
        # load the csv file
        with open(self.download.output().path, "r") as f:
            # read lines and remove the first 4 lines since they are junk
            lines = f.readlines()[4:]

        df = pd.DataFrame(
            [x.split(",") for x in lines[1:]], columns=lines[0].split(",")
        )
        df.set_index("Date", inplace=True)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        cols = ["count", "min", "max", "median"]
        df = df.astype({k: "float64" for k in cols})
        with atomic_write(self.output().path, "w", as_file=False) as f:
            df.to_parquet(f, compression="gzip")

        # ddf = dataframe.from_pandas(df, npartitions=14)
        # ddf = ddf.set_index('Date')
        # self.output().write_dask(ddf, compute=True)
