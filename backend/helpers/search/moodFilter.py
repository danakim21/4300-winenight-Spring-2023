def mood_filter(results, mood, flavorSearch=None, similar=None, both=None):
    """
    Filters wine recommendation results based on mood according to:
    https://bettertastingwine.com/wine_moods.html

    results : list of dicts
    mood : list of str
        A list of moods that the user has selected. These moods correspond
        to the text inside the mood buttons on the recommendation engine.

    Returns filtered wine recommendations as a list of dicts.
    This method filters by wine varietal.
    """
    mood_str = ", ".join(mood)
    wine_types = set()
    if "Chill" in mood_str:
        # 'Pinot Gris' only appears in reviews
        # 'Beaujolais' only appears in wine names
        wine_types.update(['Sauvignon Blanc', 'Riesling', 'Chardonnay', 'Pinot Gris', 'Pinot Grigio', 'Beaujolais', 'Pinot Noir', 'Tempranillo'])
    if "Sexy" in mood_str:
        # 'Cote du Rhone' does not appear in the database, but "Rhone-style" wines are mentioned in wine reviews
        # 'Chateauneuf-du-Pape' only appears in reviews
        # 'Chambolle-Musigny' appears in wine names and appellations, but not varietals
        # 'Barbaresco' appears in wine names and appellations, but not varietals
        wine_types.update(['Cote du Rhone', 'Chateauneuf-du-Pape', 'Pinot Noir', 'Chambolle-Musigny', 'Barbaresco'])
    if "Wild" in mood_str:
        # There is only one wine with a varietal of 'Greco di Tufo'
        # 'Nero d\'Avola' appears in wine names as well as in part of a larger varietal (e.g. 'Nero d\'Avola, Italian Red')
        # 'Aglianico' appears as part of a larger varietal: 'Aglianico, Italian Red'
        wine_types.update(['Syrah', 'Zinfandel', 'Greco di Tufo', 'Nero d\'Avola', 'Aglianico'])
    if "Sad" in mood_str:
        # 'Rioja' appears in wine names and appellations, but not varietals
        # 'Valpolicella' appears in wine names and appellations, but not varietals
        wine_types.update(['Pinot Noir', 'Rioja', 'Valpolicella'])
    if "Angry" in mood_str:
        # 'Albarino' only appears in reviews
        # 'Verdelho' appears in wine names as well as part of a larger varietal: 'Verdelho, Spanish White'
        # 'Champagne' appears in wine names, appellations, and as part of a larger varietal (e.g. 'Champagne Blend, Sparkling')
        # 'Chassagne' appears in wine names and appellations as 'Chassagne-Montrachet', but not varietals
        # 'Puligny-Montrachet' appears in wine names and appellations, but not varietals
        # 'Meursault' appears in wine names, appellations, and reviews, but not varietals
        wine_types.update(['Sauvignon Blanc', 'Albarino', 'Verdelho', 'Champagne', 'Moscato', 'Chassagne', 'Puligny-Montrachet', 'Meursault'])
    if "Low Energy" in mood_str:
        # 'Valpolicella' appears in wine names and appellation, but not varietals
        # 'Vosne-Romanée' appears in wine names, appellations, and reviews, but not varietals
        # 'New Zealand Pinot' appears in reviews, but not varietals
        wine_types.update(['Sauvignon Blanc', 'Zinfandel', 'Valpolicella', 'Pinot Noir', 'Vosne-Romanée', 'New Zealand Pinot'])


    mood_wine_types = {
        "Chill": ['Sauvignon Blanc', 'Riesling', 'Chardonnay', 'Pinot Gris', 'Pinot Grigio', 'Beaujolais', 'Pinot Noir', 'Tempranillo'],
        "Sexy": ['Cote du Rhone', 'Chateauneuf-du-Pape', 'Pinot Noir', 'Chambolle-Musigny', 'Barbaresco'],
        "Wild": ['Syrah', 'Zinfandel', 'Greco di Tufo', 'Nero d\'Avola', 'Aglianico'],
        "Sad": ['Pinot Noir', 'Rioja', 'Valpolicella'],
        "Angry": ['Sauvignon Blanc', 'Albarino', 'Verdelho', 'Champagne', 'Moscato', 'Chassagne', 'Puligny-Montrachet', 'Meursault'],
        "Low Energy": ['Sauvignon Blanc', 'Zinfandel', 'Valpolicella', 'Pinot Noir', 'Vosne-Romanée', 'New Zealand Pinot']
    }

    wine_type_to_mood = {}
    for m in mood:
        m_keyword = m.split('\n', 1)[0] 
        if m_keyword == "Sad & Melancholy":
            m_keyword = "Sad"

        if m_keyword == "Go Wild":
            m_keyword = "Wild"

        if m_keyword == "Sexy & Playful":
            m_keyword = "Sexy"

        if m_keyword in mood_wine_types:
            for wine_type in mood_wine_types[m_keyword]:
                if wine_type not in wine_type_to_mood:
                    wine_type_to_mood[wine_type] = [m_keyword]
                else:
                    wine_type_to_mood[wine_type].append(m_keyword)

    filtered_results = []
    for wine_dict in results:
        matching_moods = []
        for type in wine_types:
            if type in wine_dict['varietal']:
                if type in wine_type_to_mood:
                    matching_moods.extend(wine_type_to_mood[type])
                    
        if matching_moods:
            filtered_wine_dict = wine_dict.copy()  # Create a copy to avoid modifying the original wine_dict
            filtered_wine_dict['mood'] = ", ".join(set(matching_moods))  # Add the responsible moods to the wine dictionary
            filtered_results.append(filtered_wine_dict)
   

    if flavorSearch:
        filtered_results.sort(key=lambda x: x['term_score'], reverse=True)
    
    if similar:
        filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)

    if both:
        filtered_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

    return filtered_results