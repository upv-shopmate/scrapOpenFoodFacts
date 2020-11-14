from app import MercadonaScrapper
import json

res = MercadonaScrapper().get_products()
class MyDecoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__
with open("products.json", "w") as f:
    json.dump(res, f, cls=MyDecoder)
