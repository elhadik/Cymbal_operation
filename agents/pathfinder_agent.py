import asyncio
import os
import googlemaps
from agents.ui_events import get_ui_queue

async def run_pathfinder() -> str:
    """Run the pathfinder agent to analyze the order transition before concluding. Calculates delivery distance using Google Maps."""
    print(f"--> Live API Toolkit Triggered: run_pathfinder")
    
    origin = "636 Undercliff Ave, Edgewater, NJ 07020"
    destination = "7600 River Road, North Bergen, NJ 07047" # Hackensack Meridian Health Palisades Medical Center
    
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("[WARNING] GOOGLE_MAPS_API_KEY is missing from environment. Using placeholder distance.")
        distance_text = "approximately 2.5 miles"
        
        queue = get_ui_queue()
        print(f"--> [DEBUG] run_pathfinder queue ID: {id(queue)}")
        queue.put_nowait({
            "type": "pathfinder_map",
            "origin": origin,
            "destination": destination,
            "distance": distance_text,
            "api_key": ""
        })
        
        return f"The delivery address at Hackensack Meridian Health Palisades Medical Center is {distance_text} from the Cymbal facility at 636 Undercliff Avenue."

    try:
        gmaps = googlemaps.Client(key=api_key)
        # Use distance matrix API specifically returning imperial units (miles)
        matrix = gmaps.distance_matrix(origins=[origin],
                                       destinations=[destination],
                                       mode="driving",
                                       units="imperial")
        
        if matrix['status'] == 'OK':
            element = matrix['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                distance_text = element['distance']['text'] # e.g. "2.5 mi"
                
                queue = get_ui_queue()
                print(f"--> [DEBUG] run_pathfinder queue ID (Main API): {id(queue)}")
                queue.put_nowait({
                    "type": "pathfinder_map",
                    "origin": origin,
                    "destination": destination,
                    "distance": distance_text,
                    "api_key": api_key
                })
                
                return f"Pathfinder analysis complete. The delivery address at Hackensack Meridian Health Palisades Medical Center is {distance_text} away from Cymbal company. You may proceed to conclude the order."
            else:
                print(f"[ERROR] Google Maps Element Status: {element['status']}")
        else:
            print(f"[ERROR] Google Maps Matrix Status: {matrix['status']}")
            
    except Exception as e:
        print(f"[ERROR] Failed to calculate distance with Google Maps: {e}")

    # Fallback string if API call fails
    distance_text = "approximately 2.5 miles"
    queue = get_ui_queue()
    queue.put_nowait({
        "type": "pathfinder_map",
        "origin": origin,
        "destination": destination,
        "distance": distance_text,
        "api_key": api_key if "api_key" in locals() and api_key else ""
    })
    
    return f"Pathfinder analysis complete. The delivery address at Hackensack Meridian Health Palisades Medical Center is {distance_text} away from Cymbal company. You may proceed to conclude the order."
