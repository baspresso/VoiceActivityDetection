def get_producer_config():
    """
    Returns a dict with Kafka producer configuration.
    Adjust bootstrap.servers or other settings as needed.
    """
    return {
        "bootstrap.servers": "localhost:9092",
    }

def get_consumer_config(group_id):
    """
    Returns a dict with Kafka consumer configuration.
    """
    return {
        "bootstrap.servers": "localhost:9092",
        "group.id": group_id,
        "auto.offset.reset": "earliest",
    }