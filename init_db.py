from pymongo import MongoClient  # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

client = MongoClient("localhost", 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbrefrigerator  # 'dbrefrigerator'라는 이름의 db를 만듭니다.
# MongoDB에 insert 하기


# collection에 {doc}을 넣습니다.
def insert_all():

    doc = {
        "user_id": "user1",
        "pwd": "test123",
        "name": "김회일",
        "room_number": 426,
        "refrigerator_floor": 4,
        "registration_year": 2024,
        "registration_month": 3,
        "registration_day": 19,
        "expiration_year": 2024,
        "expiration_month": 3,
        "expiration_day": 30,
        "food_name": "커피",
        "food_image": "커피 사진",
        "food_count": 2,
    }
    db.refrigerator.insert_one(doc)

    doc = {
        "user_id": "user2",
        "pwd": "test1234",
        "name": "김철수",
        "room_number": 125,
        "refrigerator_floor": 1,
        "registration_year": 2024,
        "registration_month": 3,
        "registration_day": 18,
        "expiration_year": 2024,
        "expiration_month": 3,
        "expiration_day": 29,
        "food_name": "빵",
        "food_image": "빵 사진",
        "food_count": 3,
    }
    db.refrigerator.insert_one(doc)

    doc = {
        "user_id": "user3",
        "pwd": "test12345",
        "name": "김영희",
        "room_number": 526,
        "refrigerator_floor": 5,
        "registration_year": 2024,
        "registration_month": 3,
        "registration_day": 17,
        "expiration_year": 2024,
        "expiration_month": 3,
        "expiration_day": 31,
        "food_name": "우유",
        "food_image": "우유 사진",
        "food_count": 1,
    }
    db.refrigerator.insert_one(doc)

    print("완료")


if __name__ == "__main__":
    # 기존의 refrigerator 콜렉션을 삭제하기
    db.refrigerator.drop()

    # 영화 사이트를 scraping 해서 db 에 채우기
    insert_all()
