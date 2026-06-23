"""
=============================================================
TAG GENERATION SERVICE
=============================================================
Automatically extracts and assigns semantic tags to food items
based on their details and review content.
=============================================================
"""

import re
from typing import List, Optional

TAG_RULES = {
    "spicy": [r"spicy", r"chili", r"chilli", r"pepperoni", r"hot", r"masala", r"jalapeño", r"mirchi", r"schezwan", r"curry"],
    "crispy": [r"crispy", r"crunchy", r"fried", r"fritter", r"vada", r"spring roll", r"dry", r"toast", r"baked"],
    "comfort food": [r"biryani", r"pizza", r"burger", r"pasta", r"alfredo", r"dumpling", r"shake", r"fries", r"comfort", r"creamy"],
    "breakfast": [r"dosa", r"vada", r"idli", r"sambar", r"breakfast", r"coffee", r"morning", r"chutney"],
    "dinner": [r"biryani", r"curry", r"roti", r"naan", r"rice", r"noodle", r"pasta", r"manchurian", r"dinner", r"meal"],
    "healthy": [r"healthy", r"salad", r"soup", r"tofu", r"vegetables", r"steamed", r"low calorie", r"fresh", r"lentil"],
    "high protein": [r"chicken", r"paneer", r"tofu", r"protein", r"egg", r"mutton", r"fish", r"meat"],
    "vegetarian": [r"veg", r"vegetarian", r"paneer", r"cheese", r"dal", r"dosa", r"sambar", r"chutney", "aloo"],
    "street food": [r"vada", r"roll", r"momos", r"chaat", r"street", r"manchurian", r"fries", r"onion rings", r"spring roll"],
    "cheesy": [r"cheesy", r"cheese", r"mozzarella", r"cheddar", r"parmesan", r"alfredo", r"pizza"],
    "dessert": [r"sweet", r"dessert", r"syrup", r"jamun", r"cake", r"pastry", r"chocolate", r"milkshake", r"ice cream", r"brownie", r"dumplings"],
    "beverage": [r"coffee", r"tea", r"coke", r"drink", r"beverage", r"shake", r"milkshake", r"lassi", r"juice", r"soda", r"filter coffee"]
}


def generate_tags(
    item_name: str, 
    description: str, 
    category_id: str, 
    reviews: Optional[List[str]] = None
) -> List[str]:
    """
    Generate semantic tags for a menu item.
    
    Args:
        item_name: Name of the menu item
        description: Description of the menu item
        category_id: Category identifier
        reviews: Optional list of customer review texts
        
    Returns:
        List[str]: Extracted tags
    """
    combined_text = f"{item_name} {description} {category_id}".lower()
    if reviews:
        combined_text += " " + " ".join(reviews).lower()
        
    tags = []
    
    # Run regular expression matches against defined tag categories
    for tag, patterns in TAG_RULES.items():
        for pattern in patterns:
            if re.search(pattern, combined_text):
                tags.append(tag)
                break
                
    # Veg/Nonveg adjustments
    is_non_veg = (
        "nonveg" in combined_text or 
        "chicken" in combined_text or 
        "pepperoni" in combined_text or 
        "mutton" in combined_text or 
        "fish" in combined_text or
        "meat" in combined_text
    )
    
    if is_non_veg:
        if "vegetarian" in tags:
            tags.remove("vegetarian")
    else:
        # Default to vegetarian if no meat is mentioned and it's not a beverage
        if "vegetarian" not in tags and "beverage" not in tags:
            tags.append("vegetarian")
            
    return tags
