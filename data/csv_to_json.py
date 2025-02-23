import csv
import json

csv_file = 'ingredients.csv'
json_file = 'ingredients.json'

ingredients = []
with open(csv_file, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for i, row in enumerate(reader, start=1):
        name, measurement_unit = row
        ingredient = {
            "model": "recipes.ingredient",
            "pk": i,
            "fields": {
                "name": name,
                "measurement_unit": measurement_unit
            }
        }
        ingredients.append(ingredient)

with open(json_file, mode='w', encoding='utf-8') as file:
    json.dump(ingredients, file, ensure_ascii=False, indent=4)

print(f"Данные сохранены в {json_file}")
