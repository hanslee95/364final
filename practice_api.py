import requests
import simplejson as json


#determining a pokemon using my favorite number. One of the ways every trainer will add a pokemon to their roster.
def find_pokemon():
	number = 71
	result = requests.get('https://pokeapi.co/api/v2/pokemon/{}/?limit=151&offset=0'.format(number))
	
	poke_dict = json.loads(result.text)
	#getting access to the pokemon name
	poke_name = poke_dict['name']
	print(poke_name)

	#getting the hp (strength) of the pokemon
	print(poke_dict['stats'][5]['base_stat'])


find_pokemon()