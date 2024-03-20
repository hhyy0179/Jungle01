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
#client = MongoClient('mongodb://test:test@13.125.17.72',27017)
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
        userinfo = db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
       
        floors = [i for i in range(1, 23)]
        roomFloor = int(userinfo.get("room_number", "1")) // 100
        foods = list(
            db.refrigerator.find(
                {"refrigerator_floor": roomFloor, "food_count": {"$ne": 0}}
            )
        )

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
            {"food_count": {"$ne": 0}, "refrigerator_floor": int(floor)}, {"_id": 0}
        ).sort(
            [("expiration_year", -1), ("expiration_month", -1), ("expiration_day", -1)]
        )
        foods = list(foods_cursor)
        return jsonify({"result": "success", "foods-list": foods})
    except Exception as e:
        return jsonify({"result": "failure", "msg": str(e)})


#등록하기 페이지 불러오기
@app.route("/registration")
def load_registeration():

    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})

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

    user = db.users.find_one({'user_id': userId_receive})


    print("---asasd-")
    print(userId_receive)
    print("--dsasds--")
    
    food = {
        "user_id": user['user_id'],
        'pwd': user['pwd'],
        "name": user["name"],
        "room_number": int(user["room_number"]),
        "refrigerator_floor": int(user["room_number"][:-2]),
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



#마이냉장고 페이지 불러오기
@app.route("/myfridge")
def load_myfridge():
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})

    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("index"))

    return render_template("myfridge.html", user_info = userinfo)


#개인 포스팅 불러오기
@app.route('/myfridge/list')
def show_userpost():
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfos = list(db.refrigerator.find({"user_id": payload["user_id"]}, {"_id": 0}))
       
    
    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("index"))

    return jsonify({'result': 'success', 'user_infos': userinfos})


#개인 포스팅 불러오기
@app.route('/myfridge/delete', methods=['POST'])
def delete_userpost():
    # client 에서 작성한 음식 이름을 가져온다.
    delete_receive = request.form['post_give']

    print("------")
    print(delete_receive)
    print("------")
    
    result = db.refrigerator.delete_one({'food_name' : delete_receive})
    if result.deleted_count == 1:
        return jsonify({'result': 'success'})

    
    




if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
