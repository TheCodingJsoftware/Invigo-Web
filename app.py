import contextlib
import json
import time
import os

from flask import Flask, Response, render_template, send_from_directory

app = Flask(__name__)

last_exchange_rate = 1.3608673726676752

def write_log(log: str) -> None:
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/log.txt", 'a', encoding="utf-8") as f:
        f.write(log +'\n')


@app.route('/download')
def download():
    return send_from_directory(
        "static",
        "Invigo.zip",
        mimetype='application/zip',
        as_attachment=True,
    )


@app.route('/version')
def version():
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/static/version.txt", "r", encoding="utf-8") as f:
        version_code = f.read()
    return Response(version_code, mimetype='text/plain')


@app.route('/update_message')
def update_message():
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/static/update_message.txt", "r", encoding="utf-8") as f:
        message = f.read()
    return Response(message, mimetype='text/plain')


@app.route("/")
def index() -> None:
    try:
        return render_template(
            "index.html",
            parts_in_inventory=get_parts_in_inventory_data(),
            inventory=sort_groups(get_inventory_data()),
            part_names=get_all_part_names(),
            part_numbers=get_all_part_numbers(),
            unit_costs=get_all_unit_cost(),
            last_updated=str(time.strftime('Database last updated on %A %B %d %Y at %I:%M:%S %p',time.localtime(os.path.getmtime(f"{os.path.dirname(os.path.realpath(__file__))}/inventory.json")))),
            price_of_steel=get_price_of_steel(),
        )
    except Exception as e:
        write_log(f"<span style='color:red'>{e}</span>")
        return f"<span style='color:red'>{e}</span>"


def get_price_of_steel() -> dict:
    with open(f"{os.path.dirname(os.path.realpath(__file__))}/inventory - Price of Steel.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["Price Per Pound"]


def sort_groups(category: dict) -> dict:
    grouped_category: dict = {}
    for category_name in list(category.keys()):
        grouped_category[category_name] = {}
        for item in category[category_name].items():
            with contextlib.suppress(KeyError):
                if item[1]["group"] and item[1]["group"] != "":
                    grouped_category[category_name][item[1]["group"]] = {}
        grouped_category[category_name]["Everything else"] = {}

    for category_name in list(category.keys()):
        for item in category[category_name].items():
            try:
                if item[1]["group"] and item[1]["group"] != "":
                    grouped_category[category_name][item[1]["group"]][item[0]] = item[1]
            except Exception:
                grouped_category[category_name]["Everything else"][item[0]] = item[1]

    return grouped_category


def get_all_unit_cost() -> dict:
    global last_exchange_rate
    data = get_inventory_data()
    unit_costs = {}
    for category in list(data.keys()):
        total_cost: float = 0
        unit_costs[category] = {}
        with contextlib.suppress(KeyError):
            for item in data[category]:
                use_exchange_rate: bool = data[category][item]["use_exchange_rate"]
                exchange_rate: float = last_exchange_rate if use_exchange_rate else 1
                price: float = data[category][item]["price"]
                unit_quantity: int = data[category][item]["unit_quantity"]
                total_cost += price * unit_quantity * exchange_rate
            unit_costs[category] = round(total_cost, 2)
    return unit_costs


def get_all_part_names() -> list[str]:
    data = get_inventory_data()
    part_names = []
    for category in list(data.keys()):
        part_names.extend(
            item.replace(" ", "_").replace("/", "⁄")
            for item in list(data[category].keys())
        )
    return list(set(part_names))


def get_all_part_numbers() -> list[str]:
    data = get_inventory_data()
    part_numbers = []
    for category in list(data.keys()):
        try:
            part_numbers.extend(
                data[category][item]["part_number"].replace(" ", "_").replace("/", "⁄")
                for item in list(data[category].keys())
            )
        except KeyError:
            continue

    return list(set(part_numbers))


def get_inventory_data() -> dict:
    try:
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/inventory.json", "r", encoding="utf-8") as inventory_file:
            data = json.load(inventory_file)
        return data
    except Exception as e:
        write_log(f'Failed to load inventory.json - {e}')
        return {}

def get_parts_in_inventory_data() -> dict:
    try:
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/inventory - Parts in Inventory.json", "r", encoding="utf-8") as inventory_file:
            data = json.load(inventory_file)
        return data
    except Exception as e:
        write_log(f'Failed to load inventory.json - {e}')
        return {}
