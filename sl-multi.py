import random
import numpy as np
from typing import List, Dict, Optional, Tuple
import copy

from site_location import SiteLocationPlayer, Store, SiteLocationMap, euclidian_distances, attractiveness_allocation

class AllocSamplePlayer(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function. 
    """
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        num_rand = 100

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x,y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        return

class AdaptedAllocMultiSamplePlayer(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function but:
    - uses highest population squares first
    """
    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        num_rand = 100

        #Array of all stores
        all_stores_pos = []
        for player, player_stores in store_locations.items():
            for player_store in player_stores:
                all_stores_pos.append(player_store.pos)

#instead of randomly choosing, choose locations with largest population
        sample_pos = []

        #count number of stores to track round and increase min_dist
        num_stores = len(store_locations[self.player_id])
        min_dist = 50 
        our_stores = store_locations[self.player_id]

        #sorted population density from highest to lowest
        sorted_indices = tuple(map(tuple, np.dstack(np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))

        counter = 0
        for max_pos in sorted_indices:
            if counter >= num_rand:
                break
            too_close = False
            for store in our_stores:
                dist = np.sqrt(np.square(max_pos[0] - store.pos[0]) + np.square(max_pos[1] - store.pos[1]))
                if store.store_type == 'small':
                    min_dist = 25
                elif store.store_type == 'medium':
                    min_dist = 50
                else:
                    min_dist = 100

                if dist < min_dist:
                    too_close = True
            if not too_close:
                counter = counter + 1
                sample_pos.append((max_pos[0],max_pos[1]))

        # Choose largest store type possible:
        
        if current_funds >= store_conf['large']['capital_cost']:
            remaining_funds = current_funds - 100000
            store_type = 'large'
            min_dist = 100
        elif current_funds >= store_conf['medium']['capital_cost']:
            remaining_funds = current_funds - 50000
            store_type = 'medium'
            min_dist = 50
        else:
            remaining_funds = current_funds - 10000
            store_type = 'small'
            min_dist = 25

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        first_store = Store(best_pos[0], store_type)
        self.stores_to_place = [first_store]
        
        for next_best_pos in best_pos:
            dist = np.sqrt(np.square(next_best_pos[0] - first_store.pos[0]) + np.square(next_best_pos[1] - first_store.pos[1]))
            if dist > min_dist:
                if current_funds >= remaining_funds + 10000:
                    second_store_type = 'small'
                    second_store = Store(next_best_pos, second_store_type)
                    self.stores_to_place.append(second_store)
                    return
        
        for pos in sample_pos:
            dist = np.sqrt(np.square(pos[0] - first_store.pos[0]) + np.square(pos[1] - first_store.pos[1]))
            if dist > min_dist:
                if current_funds >= remaining_funds + 10000:
                    second_store_type = 'small'
                    second_store = Store(pos, second_store_type)
                    self.stores_to_place.append(second_store)
                    return

        return



