from flask import Flask, flash, render_template, jsonify, request, redirect, url_for
import jwt
import hashlib
from datetime import datetime, timezone, timedelta

from flask import Flask, flash, render_template, jsonify, request, redirect, url_for
import jwt
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
SECRET_KEY = "REDSEVEN"
app.secret_key = "your_very_secret_and_complex_key_here"
SECRET_KEY = "REDSEVEN"
app.secret_key = "your_very_secret_and_complex_key_here"

from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.dbweek0test


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
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY, algorithms=["HS256"]
        )  # token디코딩합니다.
        userinfo = db.users.find_one({"id": payload["id"]}, {"_id": 0})
        print(userinfo)
        floors = [i for i in range(1, 23)]
        roomnumber = int(userinfo.get("room", "1")) // 100
        print(roomnumber)
        return render_template(
            "index.html", user_info=userinfo, floors=floors, roomnumber=roomnumber
        )

    except jwt.ExpiredSignatureError:
        flash("로그인 시간이 만료되었습니다.")
        return redirect(url_for("home"))
    except jwt.exceptions.DecodeError:
        flash("로그인 정보가 존재하지 않습니다.")
        return redirect(url_for("home"))


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
    app.run("0.0.0.0", port=5000, debug=True)
