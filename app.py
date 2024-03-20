import json
from bson import ObjectId
from flask.json.provider import JSONProvider

from flask import (
    Flask,
    flash,
    make_response,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
)
import jwt
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
SECRET_KEY = "REDSEVEN"
app.secret_key = "your_very_secret_and_complex_key_here"

from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.dbrefrigerator


######################################################################################
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# #####################################################################################


## HTML을 주는 부분
@app.route("/")
def home():
    return render_template("login.html")


# 로그인
@app.route("/sign")
def login():
    return render_template("signup.html")


@app.route("/sign", methods=["POST"])  # 회원가입
def join():
    # 사용자 정보 받아오기
    id_recieve = request.form["id_give"]
    name_recieve = request.form["name_give"]
    pw_recieve = request.form["pw_give"]
    room_recieve = request.form["room_give"]
    count_recieve = request.form["count_give"]

    result = db.users.find_one({"id": id_recieve})

    if name_recieve == "":
        return jsonify({"result": "fail", "msg": "이름을 입력하세요"})
    elif id_recieve == "":
        return jsonify({"result": "fail", "msg": "아이디를 입력하세요"})
    elif pw_recieve == "":
        return jsonify({"result": "fail", "msg": "비밀번호를 입력하세요"})
    elif room_recieve == "":
        return jsonify({"result": "fail", "msg": "호수를 입력하세요"})
    elif result is not None:
        return jsonify({"result": "fail", "msg": "이미 사용중인 ID입니다!"})
    else:
        db.users.insert_one(
            {
                "user_id": id_recieve,
                "pwd": pw_recieve,
                "name": name_recieve,
                "room_number": room_recieve,
                "food_count": count_recieve,
            }
        )
        return jsonify({"result": "success"})


@app.route("/", methods=["POST"])
def api_login():
    id_recieve = request.form["id_give"]
    pw_recieve = request.form["pw_give"]

    result = db.users.find_one(
        {"user_id": id_recieve, "pwd": pw_recieve}
    )  # id, 암호화된pw을 가지고 해당 유저를 찾습니다.

    # JWT 토큰 발급
    if result is not None:
        # JWT 토큰 생성
        payload = {
            "user_id": id_recieve,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "fail", "msg": "아이디 또는 비밀번호가 틀렸습니다."})


@app.route("/logout", methods=["POST"])
def logout():
    response = make_response(redirect(url_for("home")))
    response.set_cookie("mytoken", "", expires=0)  # 쿠키 삭제
    return response


@app.route("/index")  # 메인 페이지
def find():
    # foodList = show_foods()
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.refrigerator.find_one({"user_id": payload["user_id"]}, {"_id": 0})
        # print(userinfo)
        floors = [i for i in range(1, 23)]
        roomFloor = int(userinfo.get("room_number", "1")) // 100
        foods = list(
            db.refrigerator.find(
                {"refrigerator_floor": roomFloor, "food_count": {"$ne": 0}}
            )
        )
        # print(foods[0])
        return render_template(
            "index.html",
            user_info=userinfo,
            floors=floors,
            roomFloor=roomFloor,
            foods=foods,
        )

    except jwt.ExpiredSignatureError:
        flash("로그인 시간이 만료되었습니다.")
        return redirect(url_for("home"))
    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("home"))


# db에서 음식 정보 불러오기
# @app.route("/index/list", methods=["GET"])
# def show_foods():
#     print(1)
#     sortMode = request.args.get("sortMode", "expiration")

#     if sortMode == "expiration":
#         foods_cursor = db.refrigerator.find(
#             {"food_count": {"$ne": 0}}, {"_id": 0}
#         ).sort(
#             [("expiration_year", -1), ("expiration_month", -1), ("expiration_day", -1)]
#         )
#         foods = list(foods_cursor)
#         print(foods)
#     else:
#         return jsonify({"result": "failure"})

#     return jsonify({"result": "success", "foods-list": foods})


@app.route("/index/list", methods=["GET"])
def show_foods():
    floor = request.args.get("floor")  # 클라이언트에서 요청한 층수
    print(floor)

    try:
        # 해당 층의 음식 정보만 필터링
        foods_cursor = db.refrigerator.find(
            {"food_count": {"$ne": 0}, "refrigerator_floor": int(floor)}
        ).sort(
            [("expiration_year", -1), ("expiration_month", -1), ("expiration_day", -1)]
        )
        foods = list(foods_cursor)
        return jsonify({"result": "success", "foods-list": foods})
    except Exception as e:
        return jsonify({"result": "failure", "msg": str(e)})


@app.route("/registration")
def registration():
    return render_template("registration.html")


# 음식 신청하기 api (html카드 생성에서만 작동)
@app.route("/api/apply", methods=["POST"])
def apply():
    apply_foodid_receive = request.form["apply_foodid_give"]
    food = db.refrigerator.find_one({"_id": ObjectId(apply_foodid_receive)})
    print("현재 음식 개수", food["food_count"])

    new_food_count = food["food_count"] - 1
    result = db.refrigerator.update_one(
        {"_id": food["_id"]}, {"$set": {"food_count": new_food_count}}
    )

    if result.modified_count == 1:
        return jsonify({"result": "success"})
    else:
        return jsonify({"result": "failure"})


# # 음식 등록하기 api
# @app.route("/registration", methods=["POST"])
# def post_foods():
#     # 클라이언트로부터 데이터를 받기
#     userId_receive = request.form["userId_give"]
#     foodImage_receive = request.form["foodImage_give"]
#     foodName_receive = request.form["food_give"]
#     registrationDate_receive = request.form["registrationDate_give"]
#     expirationDate_receive = request.form["expirationDate_give"]
#     memo_receive = request.form["memo_give"]

#     user = db.refrigerator.find_one({"user_id": userId_receive})

#     food = {
#         "user_id": userId_receive,
#         "pwd": user["pwd"],
#         "name": user["name"],
#         "room_number": user["room_number"],
#         "refrigerator_floor": user["refrigerator_floor"],
#         "registration_year": registrationDate_receive["year"],
#         "registration_month": registrationDate_receive["month"],
#         "registration_day": registrationDate_receive["day"],
#         "expiration_year": expirationDate_receive["year"],
#         "expiration_month": expirationDate_receive["month"],
#         "expiration_day": expirationDate_receive["day"],
#         "food_name": "우유",
#         "food_image": "우유 사진",
#         "food_count": 1,
#     }


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
