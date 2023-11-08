import pipe


def get_asset_menu():
    asset_names = pipe.server.get_asset_list()
    menu_items = []

    for name in asset_names:
        menu_items.append(name)
        menu_items.append(name)

    return sorted(menu_items)
