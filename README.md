# Building an Analytics Pipeline with PyFlink

This repo demonstrates two use cases.

## First use case: Fetch data from a DB, process in Flink using a ML algorithm and then write to a DB.

Tbe first one is about fetching some content from a database and then run some ML alogorithm on that data 
and get insights out of it. The base for this repo is from [Ververica fork](https://github.com/ververica/pyflink-nlp). Thanks. 

See the [slides](https://noti.st/morsapaes/2qPOCm/building-an-end-to-end-analytics-pipeline-with-pyflink) for more context.

## Second use case: Fetch data from a Kafka topic, process in Flink and then write to another kafka topic.

This is an example to demonstrate the functionality of fetching the data stream from a Kafka topic, process
that in Apache Flink, and write the processed data to another Kafka topic. The streamed data is accumulated
for every 5 minutes, then a SQL style query is run on that data, and the result is pushed to another Kafka topic.

## Docker

To keep things simple, this demo uses a Docker Compose setup that makes it easier to bundle up all the services you need:

<p align="center">
<img width="750" alt="demo_overview" src="https://user-images.githubusercontent.com/23521087/105339206-b571d100-5bdc-11eb-8fca-925c5c6656f2.png">
</p>

<p align="center">
<img width="750" alt="app_topology" src="https://github.com/kumareshind/streaminganalytics-kafka-flink/blob/main/docker-compose.png">
</p>

#### Getting the setup up and running
`docker-compose build`

`docker-compose up -d`

#### Is everything really up and running?

`docker-compose ps`

The following UI end points will be up as part of this.

1. Flink Web UI - Analytics  (http://localhost:8081)
2. Flink Web UI - Source and Sink are Kafka  (http://localhost:8082)
3. Kafka UI (http://localhost:8080)
4. Superset (http://localhost:8088)

## First use case: Fetch data from a DB, process in Flink using a ML algorithm and then write to a DB.

### Analyzing the Flink User Mailing List

What are people asking more frequently about in the Flink User Mailing List? How can you make sense of such a huge amount of random text?

### Some Background

The model in this demo was trained using a popular topic modeling algorithm called [LDA](https://towardsdatascience.com/lda-topic-modeling-an-explanation-e184c90aadcd) and [Gensim](https://radimrehurek.com/gensim/), a Python library with a good implementation of the algorithm. The trained model knows to some extent what combination of words are associated with certain topics, and can just be passed as a dependency to PyFlink.

Don't trust the model. :japanese_ogre:

### Submitting the PyFlink job

```bash
docker-compose exec jobmanager-nlp ./bin/flink run -py /opt/pyflink-nlp/pipeline.py -d
```

Once you get the `Job has been submitted with JobID <JobId>` green light, you can check and monitor its execution using the [Flink WebUI](http://localhost:8081):

![Flink-Web-UI](https://user-images.githubusercontent.com/23521087/105530322-eab71580-5ce7-11eb-9d21-c2b7d608078e.png)

### Visualizing on Superset

To visualize the results, navigate to (http://localhost:8088) and log into Superset using:

`username: admin`

`password: superset`

There should be a default dashboard named "Flink User Mailing List" listed under `Dashboards`:

![Superset](https://user-images.githubusercontent.com/23521087/105530591-497c8f00-5ce8-11eb-8636-3bad2de7bd90.png)

<hr>

## Second use case: Fetch data from a Kafka topic, process in Flink and then write to another kafka topic.

There is a Kafka producer (pipelines/streaming.py) that creates some data and push it to a Kafka topic. 
For this example, I took credit card purchase information (transaction log) of users. 
The Kafka producer create this mock data and push it to a Kafka topic. 100 records will be created 
for every 5 minutes and being pushed to the Kafka topic.

Flink listenes on this Kafka topic and fetches this data. What I am interested is to find the list of users who have done unusual pattern of purchases in the 5 minute window. There could be many ways to get this insight.
The way I did: group the data for the last 5 minutes, find the sum of all the online transactions, sum of all
instore transactions and then filter the users for which the following conditions are met.
 - Number of total transactions > 5
 - Online transactions > In Store transactions
 - For the In Store transactions, the distance between the two store locations > 2 miles
 - Store the last entry of location data for the previous 5 mins data group

If the above conditions are met, then this "could" be a potential fraud situation. Write the results to another Kafka topic.

You can check the filtered transactions via the Kafka UI.

**And that's it!**

For the latest updates on PyFlink, follow [Apache Flink](https://twitter.com/ApacheFlink) on Twitter.# streaminganalytics-kafka-flink
