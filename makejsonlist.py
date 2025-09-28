import pandas as pd
import json

excel_dex = pd.read_excel('Pokemon Stats.xlsx', sheet_name='Stats') #import the book and sheet

pokedex_df = excel_dex[['name','pokedex number','Catch Rate', 'Experience Type']]

pokedex_dic = pokedex_df.to_dict(orient='records')

pokedex = {
    "Pokedex":pokedex_dic
}
with open('pokedex.json', 'w', encoding='utf-8') as f:
    json.dump(pokedex, f, indent=4)
    print("/pokedex.json has been created")
