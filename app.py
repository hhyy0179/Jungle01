from flask import Flask, flash, render_template, jsonify, request, redirect, url_for
import jwt
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
SECRET_KEY = "REDSEVEN"
app.secret_key = "your_very_secret_and_complex_key_here"

from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.dbrefrigerator


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
                "id": id_recieve,
                "pw": pw_recieve,
                "name_give": name_recieve,
                "room": room_recieve,
                "count": count_recieve,
            }
        )
        return jsonify({"result": "success"})


@app.route("/", methods=["POST"])
def api_login():
    id_recieve = request.form["id_give"]
    pw_recieve = request.form["pw_give"]

    result = db.users.find_one(
        {"id": id_recieve, "pw": pw_recieve}
    )  # id, 암호화된pw을 가지고 해당 유저를 찾습니다.

    # JWT 토큰 발급
    if result is not None:
        # JWT 토큰 생성
        payload = {
            "id": id_recieve, 
            "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "fail", "msg": "아이디 또는 비밀번호가 틀렸습니다."})


@app.route("/index")  # 메인 페이지
def find():
    foodList = show_foods()
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.users.find_one({"id": payload["id"]}, {"_id": 0})
        #print(userinfo)
        floors = [i for i in range(1, 23)]
        roomnumber = int(userinfo.get("room", "1")) // 100
        #print(roomnumber)
        return render_template(
            "index.html",
            user_info=userinfo,
            floors=floors,
            roomnumber=roomnumber,
            foodList=foodList,
        )

    except jwt.ExpiredSignatureError:
        flash("로그인 시간이 만료되었습니다.")
        return redirect(url_for("home"))
    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("home"))

# db에서 음식 정보 불러오기
# @app.route("/list", methods=["GET"])
def show_foods():
    # client 에서 요청한 정렬 방식이 있는지를 확인합니다. 없다면 기본으로 최신 순으로 정렬합니다.
    sortMode = request.args.get("sortMode", "latest")

    # db에 있는 음식 주어진 정렬 방식으로 정렬
    # 최신 순
    if sortMode == "latest":
        foods = list(db.refrigerator.find({}))
        print(foods)
        foods = sorted(
            foods,
            key=lambda x: (
                x["registration_year"],
                x["registration_month"],
                x["registration_day"],
            ),
            reverse=True,
        )
    # 유통기한 낮은 순
    elif sortMode == "expiration_date":
        foods = list(db.refrigerator.find({}))
        foods = sorted(
            foods,
            key=lambda x: (
                x["registration_year"],
                x["registration_month"],
                x["registration_day"],
            ),
        )
    # 개수 적은 순
    elif sortMode == "food_count":
        foods = list(db.refrigerator.find({}))
        foods = sorted(foods, key=lambda x: x["food_count"])

    # return render_template("index.html", foodList=foods)
    return foods


#등록하기 페이지 불러오기
@app.route("/registration")
def load_registeration():

    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.users.find_one({"id": payload["id"]}, {"_id": 0})

        yearlist = [i for i in range(2020, 2050)]
        monthlist = [j for j in range(1,13)]
        daylist = [k for k in range(1,32)]
        
    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("index"))

    return render_template("registration.html", user_info = userinfo, yearlist = yearlist, monthlist = monthlist, daylist = daylist)
    


# 음식 등록하기 api
@app.route("/registration", methods=["POST"])
def post_foods():
    # 클라이언트로부터 데이터를 받기

    userId_receive = request.form["userId_give"]
    foodName_receive = request.form["foodname_give"]

    # static 폴더에 저장될 파일 이름 생성하기
    foodImage_receive = request.files["foodimage_give"]
    filename = f'img-{foodName_receive}'

    # 확장자 나누기
    extension = foodImage_receive.filename.split('.')[-1]

    # static 폴더에 저장
    save_to = f'static/{filename}.{extension}'
    foodImage_receive.save(save_to)


    foodCount_receive = request.form["foodcount_give"]
    currentyear_receive = request.form["currentyear_give"]
    currentmonth_receive = request.form["currentmonth_give"]
    currentday_receive = request.form["currentday_give"]
    expirationyear_receive = request.form["expirationyear_give"]
    expirationmonth_receive = request.form["expirationmonth_give"]
    expirationday_receive = request.form["expirationday_give"]
    memo_receive = request.form["memo_give"]

    user = db.users.find_one({'id': userId_receive})


    food = {
        "user_id": user['id'],
        'pwd': user['pw'],
        "name": user["name_give"],
        "room_number": int(user["room"]),
        "refrigerator_floor": int(user["room"][:-2]),
        "registration_year": int(currentyear_receive),
        "registration_month": int(currentmonth_receive),
        "registration_day": int(currentday_receive),
        "expiration_year": int(expirationyear_receive),
        "expiration_month": int(expirationmonth_receive),
        "expiration_day": int(expirationday_receive),
        "food_name": foodName_receive,
        "food_image": f'{filename}.{extension}',
        "food_count": int(foodCount_receive),
        "memo" : memo_receive
    }

    db.refrigerator.insert_one(food)

    return jsonify({'result': 'success'})
    # if int(foodCount_receive) > 0:
    #     #db.refrigerator.insert_one(food)
        
    # else:
    #     return jsonify({'result': 'faliure'})

# # 회원정보수정
# @app.route("/mypage/edit", methods=["POST"])
# def modify():
#     token_receive = request.cookies.get("mytoken")
#     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

#     pw_recieve = request.form["pw_give"]
#     num_recieve = request.form["num_give"]

#     dryingrack_recieve = request.form["dryingrack_give"]
#     curlingiron_recieve = request.form["curlingiron_give"]
#     detergent_recieve = request.form["detergent_give"]
#     fever_recieve = request.form["fever_give"]
#     hanger_recieve = request.form["hanger_give"]
#     painkiller_recieve = request.form["painkiller_give"]

#     db.users.update_many(
#         {"id": payload["id"]}, {"$set": {"pw": pw_recieve, "room": num_recieve}}
#     )
#     db.users.update_many(
#         {"id": payload["id"]},
#         {
#             "$set": {
#                 "dryingrack": dryingrack_recieve,
#                 "curlingiron": curlingiron_recieve,
#                 "detergent": detergent_recieve,
#                 "fever": fever_recieve,
#                 "hanger": hanger_recieve,
#                 "painkiller": painkiller_recieve,
#             }
#         },
#     )

#     return jsonify({"result": "success", "msg": "회원정보가 수정되었습니다."})


# # 회원탈퇴
# @app.route("/mypage/delete", methods=["POST"])
# def delete():
#     token_receive = request.cookies.get("mytoken")
#     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
#     db.users.delete_one({"id": payload["id"]})
#     return jsonify({"result": "success"})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
