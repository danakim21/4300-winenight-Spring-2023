def mood_filter(results, mood):
    """
    Filters wine recommendation results based on mood according to:
    https://bettertastingwine.com/wine_moods.html

    results : list of dicts
    mood : list of str
        A list of moods that the user has selected. The moods can be any
        combination of "Chill", "Sexy", "Restless", "Sad", "Angry", or
        "Low Energy".

    Returns filtered wine recommendations as a list of dicts.
    This method filters by wine varietal.
    """
    wine_types = set()
    if "Chill" in mood:
        # 'Pinot Gris' only appears in reviews
        # 'Beaujolais' only appears in wine names
        wine_types.update(['Sauvignon Blanc', 'Riesling', 'Chardonnay', 'Pinot Gris', 'Pinot Grigio', 'Beaujolais', 'Pinot Noir', 'Tempranillo'])
    elif "Sexy" in mood:
        # 'Cote du Rhone' does not appear in the database, but "Rhone-style" wines are mentioned in wine reviews
        # 'Chateauneuf-du-Pape' only appears in reviews
        # 'Chambolle-Musigny' appears in wine names and appellations, but not varietals
        # 'Barbaresco' appears in wine names and appellations, but not varietals
        wine_types.update(['Cote du Rhone', 'Chateauneuf-du-Pape', 'Pinot Noir', 'Chambolle-Musigny', 'Barbaresco'])
    elif "Restless" in mood:
        # There is only one wine with a varietal of 'Greco di Tufo'
        # 'Nero d\'Avola' appears in wine names as well as in part of a larger varietal (e.g. 'Nero d\'Avola, Italian Red')
        # 'Aglianico' appears as part of a larger varietal: 'Aglianico, Italian Red'
        wine_types.update(['Syrah', 'Zinfandel', 'Greco di Tufo', 'Nero d\'Avola', 'Aglianico'])
    elif "Sad" in mood:
        # 'Rioja' appears in wine names and appellations, but not varietals
        # 'Valpolicella' appears in wine names and appellations, but not varietals
        wine_types.update(['Pinot Noir', 'Rioja', 'Valpolicella'])
    elif "Angry" in mood:
        # 'Albarino' only appears in reviews
        # 'Verdelho' appears in wine names as well as part of a larger varietal: 'Verdelho, Spanish White'
        # 'Champagne' appears in wine names, appellations, and as part of a larger varietal (e.g. 'Champagne Blend, Sparkling')
        # 'Chassagne' appears in wine names and appellations as 'Chassagne-Montrachet', but not varietals
        # 'Puligny-Montrachet' appears in wine names and appellations, but not varietals
        # 'Meursault' appears in wine names, appellations, and reviews, but not varietals
        wine_types.update(['Sauvignon Blanc', 'Albarino', 'Verdelho', 'Champagne', 'Moscato', 'Chassagne', 'Puligny-Montrachet', 'Meursault'])
    elif "Low Energy" in mood:
        # 'Valpolicella' appears in wine names and appellation, but not varietals
        # 'Vosne-Romanée' appears in wine names, appellations, and reviews, but not varietals
        # 'New Zealand Pinot' appears in reviews, but not varietals
        wine_types.update(['Sauvignon Blanc', 'Zinfandel', 'Valpolicella', 'Pinot Noir', 'Vosne-Romanée', 'New Zealand Pinot'])

    filtered_results = []
    for wine_dict in results:
        for type in wine_types:
            if type in wine_dict['varietal']:
                # see if the mood varietals are contained in the wine varietal
                # instead of the other way around because sometimes the wine
                # varietal will contain the mood varietal
                # (e.g. the wine varietal is 'Champagne Blend, Sparkling',
                # but the mood varietal is 'Champange')
                filtered_results.append(wine_dict)
                break
    results.sort(key=lambda x: x['num_matches'], reverse=True)
    return filtered_results