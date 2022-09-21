import time
import datetime
import random
import pandas as pd 
from faker import Faker 
from kafka import KafkaProducer 
from json import dumps 

fake = Faker()
start_time = time.time()

list_of_transactions = ['highway_toll', 'petrol_station', 'supermarket', 'shopping',
                        'mortgage', 'city_service', 'restaurant', 'healthcare']

def generate_random_users():
    list_of_users = []
    for number in range(100):
        list_of_users.append(fake.name())
    return list_of_users

def get_random_user(users):
    return random.choice(users)

def get_usage_amount():
    a = [0, round(random.randint(1, 100) * random.random(), 2)]
    random.shuffle(a)
    return a

def get_usage_date():
    return fake.date_time_between(start_date='-1m', end_date='now').isoformat()

def create_usage_record(list_of_users):
    amount = get_usage_amount()
    return {
        'customer': get_random_user(list_of_users),
        'transaction_type': random.choice(list_of_transactions),
        'online_payment_amount': amount[0],
        'in_store_payment_amount': amount[1],
        'transaction_datetime': get_usage_date(),
    }

users = generate_random_users()
end_datetime = datetime.datetime.combine(datetime.date(2070, 1, 1), datetime.time(1, 0, 0))
current_datetime = datetime.datetime.combine(datetime.date.today(), datetime.datetime.now().time())
try:
    while current_datetime <= end_datetime:
        data_usage = pd.DataFrame([create_usage_record(users) for _ in range(1000)])
        producer = KafkaProducer(bootstrap_servers=['kafka0:29092'],
                                value_serializer=lambda x: dumps(x).encode('utf-8'))

        for row in data_usage.itertuples():
            data_customer = row.customer
            data_transaction_type = row.transaction_type
            data_online_payment_amount = row.online_payment_amount
            data_in_store_payment_amount = row.in_store_payment_amount
            data_lat = random.uniform(44.57, 44.91)
            data_lon = random.uniform(20.20, 20.63)
            data_transaction_datetime = row.transaction_datetime + "Z"
            data = {
                    'customer': data_customer,
                    'transaction_type': data_transaction_type,
                    'online_payment_amount': data_online_payment_amount,
                    'in_store_payment_amount': data_in_store_payment_amount,
                    'lat': data_lat,
                    'lon': data_lon,
                    'transaction_datetime': data_transaction_datetime
                    }
            future = producer.send('transactions-data', value=data)
            result = future.get(timeout=5)
        print("--- {} seconds ---".format(time.time() - start_time))
        time.sleep(5)
        current_datetime = datetime.datetime.combine(datetime.date.today(), datetime.datetime.now().time())
except Exception as e:
    print("Exception during sending messages " + str(e))

