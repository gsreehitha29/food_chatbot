def calculate_total(cart):

    total = 0

    for item in cart:

        total += item["price"] * item["quantity"]

    return total