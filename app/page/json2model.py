import json

obj = {
    "name": "张三",
    "age": 18,
    "gender": "男",
    "hobbies": [
        "阅读",
        "编程",
        "旅行"
    ],
    "address": {
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "street": "科技园路"
    }
}

with open('../../assets/json/test.json', "w", encoding="utf-8") as f:
    json.dump(obj, f, ensure_ascii=False, indent=4)

with open('../../assets/json/test.json', "r", encoding="utf-8") as f:
    obj = json.load(f)
    print(obj)


