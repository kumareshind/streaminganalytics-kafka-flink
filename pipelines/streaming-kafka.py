# import json

# from pyflink.common import Row
# from pyflink.common.serialization import SimpleStringSchema,SerializationSchema,JsonRowSerializationSchema,JsonRowDeserializationSchema,Encoder
# from pyflink.common.typeinfo import Types,BasicType,TypeInformation,BasicTypeInfo
# from pyflink.datastream import StreamExecutionEnvironment
# from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
# from pyflink.common.typeinfo import Types

# # from pyflink.common.typeinfo import Types
# # from pyflink.datastream.connectors.kafka import FlinkKafkaProducer
# # from pyflink.datastream.formats.json import JsonRowSerializationSchema


# def my_map(obj):
#     json_obj = json.loads(json.loads(obj))
#     return json.dumps(json_obj["name"])

# def utf8_decoder(s):
#     """ Decode the unicode as UTF-8 """
#     if s is None:
#         return None
#     return s.decode('utf-8')

# def datastream_api_demo():
#     # 1. create a StreamExecutionEnvironment
#     env = StreamExecutionEnvironment.get_execution_environment()
#     env.set_parallelism(1)
#     # the sql connector for kafka is used here as it's a fat jar and could avoid dependency issues
#     # env.add_jars("file:///Users/niaz/Downloads/f2.jar")

#     # 2. create source DataStream
#     deserialization_schema = SimpleStringSchema()

#     deserialization_schema = JsonRowDeserializationSchema.builder() \
#         .type_info(type_info=Types.ROW([ 
#             Types("customer", Types.STRING()), 
#             Types.FIELD("transaction_type", Types.DOUBLE()),
#             Types.FIELD("online_payment_amount", Types.DOUBLE()),
#             Types.FIELD("in_store_payment_amount", Types.DOUBLE()),
#             Types.FIELD("lat", Types.DOUBLE()),
#             Types.FIELD("lon", Types.DOUBLE()),
#             Types.FIELD("transaction_datetime", Types.TIMESTAMP()),
#             ])).build()

#     kafka_source = FlinkKafkaConsumer(
#         topics='transactions-data',
#         deserialization_schema=deserialization_schema,
#         properties={'bootstrap.servers': 'kafka0:29092', 'group.id': 'test_group'})

#     ds = env.add_source(kafka_source)
#     ds = ds.map(lambda a: my_map(a),Types.STRING()) 

#     # 3. define the execution logic
#     # ds = ds.map(lambda a: Row(a % 4, 1), output_type=Types.ROW([Types.LONG(), Types.LONG()])) \
#     #        .key_by(lambda a: a[0]) \
#     #        .reduce(lambda a, b: Row(a[0], a[1] + b[1]))

#     # 4. create sink and emit result to sink
#     serialization_schema = SimpleStringSchema()
#     kafka_sink = FlinkKafkaProducer(
#         topic='transactions-data-results',
#         serialization_schema=serialization_schema,
#         producer_config={'bootstrap.servers': 'kafka0:9092', 'group.id': 'test_group'})
#     ds.add_sink(kafka_sink)
#     #ds.print()
#     # 5. execute the job
#     env.execute('datastream_api_demo')


# if __name__ == '__main__':
#     datastream_api_demo()


# def register_transactions_source(st_env):
#     st_env.connect(Kafka()
#                    .version("universal")
#                    .topic("transactions-data")
#                    .start_from_latest()
#                    .property("zookeeper.connect", "zookeeper0:2181")
#                    .property("bootstrap.servers", "kafka0:29092")) \
#         .with_format(Json()
#         .fail_on_missing_field(True)
#         .schema(DataTypes.ROW([
#         DataTypes.FIELD("customer", DataTypes.STRING()),
#         DataTypes.FIELD("transaction_type", DataTypes.STRING()),
#         DataTypes.FIELD("online_payment_amount", DataTypes.DOUBLE()),
#         DataTypes.FIELD("in_store_payment_amount", DataTypes.DOUBLE()),
#         DataTypes.FIELD("lat", DataTypes.DOUBLE()),
#         DataTypes.FIELD("lon", DataTypes.DOUBLE()),
#         DataTypes.FIELD("transaction_datetime", DataTypes.TIMESTAMP())]))) \
#         .with_schema(Schema()
#         .field("customer", DataTypes.STRING())
#         .field("transaction_type", DataTypes.STRING())
#         .field("online_payment_amount", DataTypes.DOUBLE())
#         .field("in_store_payment_amount", DataTypes.DOUBLE())
#         .field("lat", DataTypes.DOUBLE())
#         .field("lon", DataTypes.DOUBLE())
#         .field("rowtime", DataTypes.TIMESTAMP())
#         .rowtime(
#         Rowtime()
#             .timestamps_from_field("transaction_datetime")
#             .watermarks_periodic_bounded(60000))) \
#         .in_append_mode() \
#         .register_table_source("source")

# def register_transactions_sink_into_csv(st_env):
#     result_file = "/opt/pyflink-nlp/data/output/output_file.csv"
#     if os.path.exists(result_file):
#         os.remove(result_file)
#     st_env.register_table_sink("sink_into_csv",
#                                CsvTableSink(["customer",
#                                              "count_transactions",
#                                              "total_online_payment_amount",
#                                              "total_in_store_payment_amount",
#                                              "lat",
#                                              "lon",
#                                              "last_transaction_time"],
#                                             [DataTypes.STRING(),
#                                              DataTypes.DOUBLE(),
#                                              DataTypes.DOUBLE(),
#                                              DataTypes.DOUBLE(),
#                                              DataTypes.DOUBLE(),
#                                              DataTypes.DOUBLE(),
#                                              DataTypes.TIMESTAMP()],
#                                             result_file))

# def transactions_job():
#     s_env = StreamExecutionEnvironment.get_execution_environment()
#     s_env.set_parallelism(3)
#     s_env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
#     st_env = StreamTableEnvironment \
#         .create(s_env, environment_settings=EnvironmentSettings
#                 .new_instance()
#                 .in_streaming_mode()
#                 .use_blink_planner().build())

#     register_transactions_source(st_env)
#     register_transactions_sink_into_csv(st_env)

#     st_env.from_path("source") \
#         .window(Tumble.over("10.hours").on("rowtime").alias("w")) \
#         .group_by("customer, w") \
#         .select("""customer as customer, 
#                    count(transaction_type) as count_transactions,
#                    sum(online_payment_amount) as total_online_payment_amount, 
#                    sum(in_store_payment_amount) as total_in_store_payment_amount,
#                    max(lat) as lat,
#                    max(lon) as lon,
#                    w.end as last_transaction_time
#                    """) \
#         .filter("total_online_payment_amount<total_in_store_payment_amount") \
#         .filter("count_transactions>=3") \
#         .filter("lon < 20.62") \
#         .filter("lon > 20.20") \
#         .filter("lat < 44.91") \
#         .filter("lat > 44.57") \
#         .insert_into("destination")

#     st_env.execute("app")


# if __name__ == '__main__':
#     transactions_job()

import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import *


def main():
    # Create streaming environment
    env = StreamExecutionEnvironment.get_execution_environment()

    settings = EnvironmentSettings.new_instance()\
                      .in_streaming_mode()\
                      .use_blink_planner()\
                      .build()


    # add kafka connector dependency
    curr_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    jars = f"""
file://{curr_path}/flink-sql-connector-kafka_2.11-1.10.1.jar;
"""

    # create table environment
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                            environment_settings=settings)


    #######################################################################
    # Create Kafka Source Table with DDL
    #######################################################################

    src_ddl = """
        CREATE TABLE customer_table (
            customer VARCHAR,
            transaction_type DOUBLE,
            online_payment_amount DOUBLE,
            in_store_payment_amount DOUBLE,
            lat DOUBLE,
            lon DOUBLE,
            transaction_datetime TIMESTAMP(6)
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'transactions-data',
            'properties.bootstrap.servers' = 'kafka0:29092',
            'format' = 'json'
        )
    """

    tbl_env.execute_sql(src_ddl)

    # create and initiate loading of source Table
    tbl = tbl_env.from_path('customer_table')

    print('\nSource Schema')
    tbl.print_schema()

    #####################################################################
    # Define Tumbling Window Aggregate Calculation (Seller Sales Per Minute)
    #####################################################################
    sql = """
        SELECT
          customer as customer,
          count(transaction_type) as count_transactions,
          sum(online_payment_amount) as total_online_payment_amount,
          sum(in_store_payment_amount) as total_in_store_payment_amount,
          max(lat) as lat,
          max(lon) as lon,
          W.end as last_transaction_time,
        FROM customer_table
        WHERE
            (total_online_payment_amount<total_in_store_payment_amount AND
            count_transactions>=3 AND
            lon < 20.62 AND
            lon > 20.20 AND
            lat < 44.91 AND
            lat > 44.57)
        GROUP BY
          TUMBLE_OVER(transaction_datetime, INTERVAL '10' HOURS) as W,
          customer
    """
    aggr_tbl = tbl_env.sql_query(sql)

    print('\nProcess Sink Schema')
    aggr_tbl.print_schema()

    ###############################################################
    # Create Kafka Sink Table
    ###############################################################
    sink_ddl = """
        CREATE TABLE customer-results (
            customer VARCHAR,
            count_transactions DOUBLE,
            total_online_payment_amount DOUBLE,
            total_in_store_payment_amount DOUBLE,
            lat DOUBLE,
            lon DOUBLE,
            last_transaction_time TIMESTAMP(6)
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'transactions-data-results',
            'properties.bootstrap.servers' = 'kafka0:29092',
            'format' = 'json'
        )
    """
    tbl_env.execute_sql(sink_ddl)

    # write time windowed aggregations to sink table
    aggr_tbl.execute_insert('customer-results').wait()

    tbl_env.execute('windowed-customer-results')

if __name__ == '__main__':
    main()