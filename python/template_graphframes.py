#    _____  _____ _____  _____  
#   / ____|/ ____|  __ \|  __ \ 
#  | (___ | |  __| |__) | |__) |
#   \___ \| | |_ |  ___/|  ___/ 
#   ____) | |__| | |    | |     
#  |_____/ \_____|_|    |_|     
#
#   A Solvinity template
#   Created by:             Hugo Z
#   Date:                   04-may-2023
#   Version:                1.0
#   Function:               This is a template for graph processing build
#                           on top of pyspark and graphframes. This program
#                           file will be executed by a warper that controls
#                           the connection with spark, and monitors the
#                           execution of the program. You will be notified
#                           once a program has concluded.
#
#
#   Versions:
#       - Spark:            3.3.2
#       - GraphFrames:      0.8.2
#       - Scala:            2.12
#       - Python:           3.9
#
#   Python libraries:
#       - pandas:           2.0.0
#       - PyYAML:           5.4.1
#       - pyspark:          3.3.2
#       - graphframes:      0.6

# ----------- NEEDED IMPORTS -----------
from graphframes import GraphFrame
from pyspark.sql import SparkSession, DataFrame

# ------------ USER IMPORTS ------------
import pandas as pd


# ----------- HELPER FUNCTION ----------
def file_to_input(file_name: str, spark: SparkSession) -> DataFrame:
    """Function creates spark dataframe

    Args:
        file_name (str): file name of either edges or vertices
        spark (SparkSession): current spark session

    Returns:
        DataFrame: spark dataframe created from file
    """
    # Load data (data type can also be a txt file)
    df = pd.read_csv(file_name, delim_whitespace=True)

    # Convert all data to tuples, each row is a tuple
    data = list(df.itertuples(index=False, name=None))
    return spark.createDataFrame(data, list(df.columns))


# ----------- START FUNCTION -----------
def main(spark: SparkSession, mount_path: str):
    """!!!DO NOT CHANGE THE NAME OF THIS FUNCTION!!!
    This function will be called by the warper program.

    The warper will handle:
        - Establishing a connection to your spark cluster.
        - Mounting to your storage.

    In this function you have to define your data (edges, vertices)
    You can use 'file_to_input' as a helper function.
    Create a Graph and set the algorithm parameters.
    A user guild link is provided for some extra help.
    Good luck.

    Args:
        spark (SparkSession): This is the connection to your live spark cluster.
        mount_path (str): This is the directory where your files are stored.
    """
    SAFE_FILE = f"{mount_path}/result.csv"
    EDGES = f"{mount_path}/[edges].txt"         # <- Change me
    VERTICES = f"{mount_path}/[vertices].txt"   # <- Change me

    # Create vertices and edges
    v = file_to_input(VERTICES, spark)
    e = file_to_input(EDGES, spark)
    g = GraphFrame(v, e)

    # Graph processing
    # For a user guild check the link
    # https://graphframes.github.io/graphframes/docs/_site/user-guide.html#creating-graphframes
    results = g.[algorithm](parameter=value)    # <- Change me

    # Save file
    df = pd.DataFrame(results.toPandas())
    df.to_csv(SAFE_FILE)
