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