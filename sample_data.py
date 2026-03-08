import csv
import random
import os

FIELDS = ["id", "name", "age", "city", "score"]

NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve",
    "Frank", "Grace", "Hank", "Ivy", "Jack",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
]


def generate_sample_data(num_records=10):
    records = []
    for i in range(1, num_records + 1):
        record = {
            "id": i,
            "name": random.choice(NAMES),
            "age": random.randint(18, 65),
            "city": random.choice(CITIES),
            "score": round(random.uniform(0, 100), 2),
        }
        records.append(record)
    return records


def write_csv(records, filename="output.csv"):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {filename}")


def read_csv(filename="output.csv"):
    records = []
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            records.append(row)
    return records


def print_summary(records):
    print(f"\nTotal records: {len(records)}")
    if not records:
        return
    ages = [int(r["age"]) for r in records]
    scores = [float(r["score"]) for r in records]
    print(f"Age   - min: {min(ages)}, max: {max(ages)}, avg: {sum(ages)/len(ages):.1f}")
    print(f"Score - min: {min(scores):.2f}, max: {max(scores):.2f}, avg: {sum(scores)/len(scores):.2f}")


if __name__ == "__main__":
    random.seed(42)
    records = generate_sample_data(10)
    write_csv(records)
    loaded = read_csv()
    print_summary(loaded)
