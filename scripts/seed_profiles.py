"""
One-time script to seed the parking-permit-profiles DynamoDB table.
Run with: AWS_PROFILE=terraform-user python -m scripts.seed_profiles
"""

import boto3

PROFILES_TABLE = "parking-permit-profiles"

PROFILES = {
    "bella": {
        "licensePlate": "KWK3467",
        "state": "Texas",
        "year": "2018",
        "make": "Ford",
        "model": "Escape",
        "color": "Gray",
        "firstName": "Bella",
        "lastName": "Madrid",
        "phoneNumber": "8177332863",
    },
    "kaitlyn": {
        "licensePlate": "292LSA",
        "state": "Indiana",
        "year": "2003",
        "make": "Toyota",
        "model": "Camry",
        "color": "Gold",
        "firstName": "Kaitlyn",
        "lastName": "Levan",
        "phoneNumber": "5743093485",
    },
    "logan": {
        "licensePlate": "KWK3467",
        "state": "Texas",
        "year": "2018",
        "make": "Ford",
        "model": "Escape",
        "color": "Gray",
        "firstName": "Bella",
        "lastName": "Madrid",
        "phoneNumber": "8177332863",
    },
    "sammy": {
        "licensePlate": "VSD9482",
        "state": "Texas",
        "year": "2023",
        "make": "Ford",
        "model": "F-150",
        "color": "Red",
        "firstName": "Sammy",
        "lastName": "Ragan",
        "phoneNumber": "8178635546",
    },
    "remi": {
        "licensePlate": "WGF1012",
        "state": "Texas",
        "year": "2021",
        "make": "Tesla",
        "model": "Model 3",
        "color": "White",
        "firstName": "Remington",
        "lastName": "Dodge",
        "phoneNumber": "4695580051",
    },
    "ben": {
        "licensePlate": "TVL8978",
        "state": "Texas",
        "year": "2022",
        "make": "Jeep",
        "model": "Rubicon",
        "color": "Gray",
        "firstName": "Ben",
        "lastName": "Madrid",
        "phoneNumber": "8177094496",
    },
    "lena": {
        "licensePlate": "3F1008",
        "state": "Texas",
        "year": "2023",
        "make": "Lexus",
        "model": "RX",
        "color": "Gray",
        "firstName": "Lena",
        "lastName": "Chambers",
        "phoneNumber": "9729482452",
    },
    "hunter": {
        "licensePlate": "TNG7077",
        "state": "Texas",
        "year": "2022",
        "make": "BMW",
        "model": "740i",
        "color": "Black",
        "firstName": "Hunter",
        "lastName": "Kendrick",
        "phoneNumber": "8172053266",
    },
    "carlo": {
        "licensePlate": "NWG9285",
        "state": "Texas",
        "year": "2020",
        "make": "Infiniti",
        "model": "Q50",
        "color": "Silver",
        "firstName": "Carlo",
        "lastName": "Tashjian",
        "phoneNumber": "7743924720",
    },
    "kuzie": {
        "licensePlate": "NXS4969",
        "state": "Texas",
        "year": "2017",
        "make": "Audi",
        "model": "A4",
        "color": "Black",
        "firstName": "Kuzie",
        "lastName": "Chambers",
        "phoneNumber": "9402311617",
    },
}

if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(PROFILES_TABLE)

    for name, profile in PROFILES.items():
        item = {"name": name, **profile}
        table.put_item(Item=item)
        print(f"seeded: {name}")

    print("done")
