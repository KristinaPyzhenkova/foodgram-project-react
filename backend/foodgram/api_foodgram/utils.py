def shopping(ingredients):
    shopping_list = {}
    for ingredient in ingredients:
        amount = ingredient.get('amount__sum')
        name = ingredient.get('ingredients__name')
        measurement_unit = ingredient.get(
            'ingredients__measurement_unit'
        )
        shopping_list[name] = {
            'measurement_unit': measurement_unit,
            'amount': amount
        }
    main_list = ([f"{item}: {value['amount']}"
                  f" {value['measurement_unit']}\n"
                  for item, value in shopping_list.items()])
    return main_list
