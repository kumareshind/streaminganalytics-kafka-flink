import os
from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.table import StreamTableEnvironment, CsvTableSink, DataTypes, EnvironmentSettings
from pyflink.table.descriptors import Schema, Rowtime, Json, Kafka, Elasticsearch
from pyflink.table.window import Tumble
from pyflink.datastream.checkpointing_mode import CheckpointingMode

def register_transactions_source(st_env):
    st_env.connect(Kafka()
                   .version("universal")
                   .topic("transactions-data")
                   .start_from_latest()
                   .property("zookeeper.connect", "zookeeper0:2181")
                   .property("bootstrap.servers", "kafka0:29092")
                   .property("group.id",  "source_data")) \
        .with_format(Json()
        .fail_on_missing_field(True)
        .schema(DataTypes.ROW([
        DataTypes.FIELD("customer", DataTypes.STRING()),
        DataTypes.FIELD("transaction_type", DataTypes.STRING()),
        DataTypes.FIELD("online_payment_amount", DataTypes.DOUBLE()),
        DataTypes.FIELD("in_store_payment_amount", DataTypes.DOUBLE()),
        DataTypes.FIELD("lat", DataTypes.DOUBLE()),
        DataTypes.FIELD("lon", DataTypes.DOUBLE()),
        DataTypes.FIELD("transaction_datetime", DataTypes.TIMESTAMP())]))) \
        .with_schema(Schema()
        .field("customer", DataTypes.STRING())
        .field("transaction_type", DataTypes.STRING())
        .field("online_payment_amount", DataTypes.DOUBLE())
        .field("in_store_payment_amount", DataTypes.DOUBLE())
        .field("lat", DataTypes.DOUBLE())
        .field("lon", DataTypes.DOUBLE())
        .field("rowtime", DataTypes.TIMESTAMP())
        .rowtime(
        Rowtime()
            .timestamps_from_field("transaction_datetime")
            .watermarks_periodic_bounded(60000))) \
        .in_append_mode() \
        .register_table_source("source")

def register_transactions_sink(st_env):
    st_env.connect(Kafka()
                   .version("universal")
                   .topic("transactions-data-result")
                   .property("zookeeper.connect", "zookeeper0:2181")
                   .property("bootstrap.servers", "kafka0:29092") 
                   .property("group.id",  "sink_data")) \
        .with_schema(Schema()
        .field("customer", DataTypes.STRING())
        .field("count_transactions", DataTypes.DOUBLE())
        .field("total_online_payment_amount", DataTypes.DOUBLE())
        .field("total_in_store_payment_amount", DataTypes.DOUBLE())
        .field("lat", DataTypes.DOUBLE())
        .field("lon", DataTypes.DOUBLE())
        .field("last_transaction_time", DataTypes.TIMESTAMP())) \
        .with_format(Json().derive_schema()) \
        .register_table_sink("sink_into_kafka")

def register_transactions_sink_into_csv(st_env):
    result_file = "/opt/pyflink-nlp/data/output/output_file.csv"
    if os.path.exists(result_file):
        os.remove(result_file)
    st_env.register_table_sink("sink_into_csv",
                               CsvTableSink(["customer",
                                             "count_transactions",
                                             "total_online_payment_amount",
                                             "total_in_store_payment_amount",
                                             "lat",
                                             "lon",
                                             "last_transaction_time"],
                                            [DataTypes.STRING(),
                                             DataTypes.DOUBLE(),
                                             DataTypes.DOUBLE(),
                                             DataTypes.DOUBLE(),
                                             DataTypes.DOUBLE(),
                                             DataTypes.DOUBLE(),
                                             DataTypes.TIMESTAMP()],
                                            result_file))

def transactions_job():
    s_env = StreamExecutionEnvironment.get_execution_environment()
    s_env.set_parallelism(1)
    s_env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
    s_env.enable_checkpointing(3000, CheckpointingMode.AT_LEAST_ONCE)
    st_env = StreamTableEnvironment \
        .create(s_env, environment_settings=EnvironmentSettings
                .new_instance()
                .in_streaming_mode()
                .use_blink_planner().build())

    register_transactions_source(st_env)
    #register_transactions_sink_into_csv(st_env)
    register_transactions_sink(st_env)

    st_env.from_path("source") \
        .window(Tumble.over("5.minutes").on("rowtime").alias("w")) \
        .group_by("customer, w") \
        .select("""customer as customer, 
                   count(transaction_type) as count_transactions,
                   sum(online_payment_amount) as total_online_payment_amount, 
                   sum(in_store_payment_amount) as total_in_store_payment_amount,
                   max(lat) as lat,
                   max(lon) as lon,
                   w.end as last_transaction_time
                   """) \
        .filter("total_online_payment_amount<total_in_store_payment_amount") \
        .filter("count_transactions>=3") \
        .insert_into("sink_into_kafka")

    st_env.execute("app")


if __name__ == '__main__':
    transactions_job()