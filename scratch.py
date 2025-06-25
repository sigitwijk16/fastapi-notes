import random
from typing import Union, Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel, AfterValidator, HttpUrl

app = FastAPI()

fake_items_db = [
    {"item_name": "Sampo"},
    {"item_name": "Sampo Kaki"},
    {"item_name": "Sabun Muka"},
    {"item_name": "Sabun Badan"},
    {"item_name": "Mesin Cuci"},
]

data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}

class Image(BaseModel):
    url: HttpUrl = HttpUrl(url="http://www.example.com")
    name: str = "SSSS"

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
    images: list[Image] | None = None

    model_config = {
        "json_schema_extra" : {
            "examples" : [
                {
                    "name" : "Foo",
                    "description" : "The best one",
                    "price" : 35.4,
                    "tax" : 3.2
                }
            ]
        }
    }

class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]

class User(BaseModel):
    username: str
    password: str

@app.get("/")
async def hello_world():
    return "Hello World"


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}

# @app.get("/items")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip: skip + limit]

def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('ID must start with either "isbn-" or "imdb-"')
    return id


@app.get("/items")
async def read_item(
    q: Annotated[
        str | None,
        Query(
            min_length=3,
            max_length=10,
            alias="item-query",
            title="Query String",
            description="Query string to do something with something",
            pattern="^fixedquery$",
            deprecated=True
            )
        ] = None,
    id: Annotated[str | None, AfterValidator(check_valid_id)] = None,
    ):
    result = {
        "items": [
            {"item_id": "Foo"},
            {"item_id": "Bar"}
        ]}
    if id:
        item = data.get(id)
        result.update({"item": item})
    else:
        id, item = random.choice(list(data.items()))
        print(item)
        result.update({"item":item})
    if q:
        result.update({"q": q})
    return result


@app.post("/items")
async def create_item(item: Item):
    item.name = item.name.capitalize()
    item_dict = item.dict()
    if item.tax is not None:
        item_dict.update({"price_with_tax": item.price + item.tax})
    return item_dict


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}


@app.get("/items/{item_id}")
async def read_item(item_id: str, needy: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update({
            "description": "This is the item long description"
        })
    return item


@app.get("/user/{user_id}/items/{item_id}")
async def read_user_item(user_id: int,  needy: str, item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id, "owner_id": user_id, "needy": needy}
    if q:
        item.update({"q": q})
    if not short:
        item.update({
            "description": "This is the item long description"
        })
    return item

@app.post("/offers")
async def create_offer(offer: Offer):
    return offer

@app.post("/images/multiple")
async def create_multiple_images(images: list[Image]):
    for image in images:
        print(image.url)
    return images

weights = {3 : 6.4, 4 : 4.22}

@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float] = weights):
    return weights

# @app.post("/login")
# async def login_user(user: User):
#     # user = db.find(user)
#     # if (!user) {
#     #     raise ValueError("User not found")
#     # }
#     return user