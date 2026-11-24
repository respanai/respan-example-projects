import os
import dotenv
import json

dotenv.load_dotenv(override=True)
from openai import OpenAI
from pathlib import Path
from example_workflows.multi_modal_tool_evals.constants import (
    EVAL_RUN_ID,
    EVAL_RUN_METADATA_KEY,
)

resource_path = Path(__file__).parent / "assets"

client = OpenAI(
    base_url=os.getenv("RESPAN_BASE_URL"),
    api_key=os.getenv("RESPAN_API_KEY"),
)

# Travel Assistant Agent with 3 Tools


def search_places(category):
    """Search for places based on landscape category"""
    place_options = {
        "mountain": [
            "Lake Tahoe, California",
            "Banff National Park, Canada",
            "Zermatt, Switzerland",
        ],
        "lake": ["Lake Como, Italy", "Lake Bled, Slovenia", "Crater Lake, Oregon"],
        "beach": ["Maldives", "Santorini, Greece", "Maui, Hawaii"],
        "forest": [
            "Olympic National Park, Washington",
            "Black Forest, Germany",
            "Redwood National Park, California",
        ],
    }

    if category.lower() in place_options:
        locations = place_options[category.lower()]
        return f"Found {len(locations)} {category} destinations: {', '.join(locations)}"

    return "No destinations found for this category. Available categories: mountain, lake, beach, forest"


def check_weather(location):
    """Check weather for specific locations"""
    weather_data = {
        "Lake Tahoe": "Lake Tahoe: 12°C, partly cloudy, 15% chance of rain. Great for hiking and lake activities.",
        "Banff": "Banff: 8°C, clear skies, perfect mountain weather for outdoor adventures.",
        "Zermatt": "Zermatt: 5°C, sunny, ideal conditions for alpine activities and sightseeing.",
        "Lake Como": "Lake Como: 18°C, mild and sunny, perfect for boat tours and lakeside dining.",
        "Santorini": "Santorini: 24°C, sunny with light breeze, ideal beach and sunset viewing weather.",
        "Maldives": "Maldives: 29°C, tropical paradise conditions, perfect for water sports and relaxation.",
        "Olympic National Park": "Olympic National Park: 16°C, misty with occasional showers, great for forest hiking.",
    }

    # Find matching location
    for place, weather in weather_data.items():
        if place.lower() in location.lower():
            return weather

    return f"{location}: Weather data available. Conditions are suitable for travel and outdoor activities."


def find_hotels(location, preferences="mid-range"):
    """Find hotels for specific locations"""
    hotel_data = {
        "Lake Tahoe": "Edgewood Tahoe - $320/night, luxury lakefront resort, spa, golf course. Rating: 4.8/5",
        "Banff": "Fairmont Banff Springs - $280/night, castle-style hotel, mountain views, spa. Rating: 4.6/5",
        "Zermatt": "The Omnia - $450/night, luxury mountain hotel, Matterhorn views, spa. Rating: 4.9/5",
        "Lake Como": "Grand Hotel Tremezzo - $380/night, historic luxury, lake views, gardens. Rating: 4.7/5",
        "Santorini": "Canaves Oia Hotel - $520/night, infinity pool, caldera views, luxury suites. Rating: 4.8/5",
        "Maldives": "Conrad Maldives - $680/night, overwater villas, private beach, spa. Rating: 4.9/5",
        "Olympic National Park": "Lake Crescent Lodge - $180/night, historic lodge, forest setting, lakefront. Rating: 4.3/5",
    }

    # Find matching location
    for place, hotel in hotel_data.items():
        if place.lower() in location.lower():
            return hotel

    return f"{location}: Quality accommodations available. Prices range from $150-400/night depending on season."


def recommend_activities(location):
    """Recommend activities for specific locations"""
    activity_data = {
        "Lake Tahoe": "Hiking, boating, lake activities, and winter sports.",
        "Banff": "Hiking, wildlife watching, and winter sports.",
        "Zermatt": "Alpine hiking, skiing, and paragliding.",
        "Lake Como": "Boating, hiking, and Italian cuisine.",
        "Santorini": "Sunset sailing, wine tasting, and Greek cuisine.",
        "Maldives": "Snorkeling, sunset cruises, and Maldivian cuisine.",
        "Olympic National Park": "Hiking, camping, and river rafting.",
    }

    # Find matching location
    for place, activities in activity_data.items():
        if place.lower() in location.lower():
            return activities

    return f"{location}: Wide range of activities available. Ideal for outdoor enthusiasts."

def create_demo_variables(
    category: str,
    has_image: bool,
    is_booking_hotel: bool,
    is_checking_weather: bool,
    name: str,
    **kwargs,
):
    """Create variables for Respan prompt management"""

    # Variables for Respan prompt template
    variables = {
        "category": category,
        "is_booking_hotel": is_booking_hotel,
        "is_checking_weather": is_checking_weather,
        "name": name,
    }

    if has_image:
        # Load image as base64 for the variable
        import base64

        with open(resource_path / f"{category.lower()}.jpeg", "rb") as image:
            base64_image = base64.b64encode(image.read()).decode("utf-8")
            variables["image"] = {
                "_type": "image_url",
                "value": f"data:image/jpeg;base64,{base64_image}",
            }

    return variables


def get_user_location_choice() -> str:
    """Get user's choice from search results"""
    user_choice = input("\nPlease choose your preferred destination: ").strip()
    print(f"✓ User selected: {user_choice}")
    return user_choice


def _run_interactive_loop(assistant_response, conversation_history, respan_args):
    """Handle the interactive conversation loop"""
    print(f"\nAssistant: {assistant_response}")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["done", "exit"]:
            print("✓ Session ended")
            break

        conversation_history.append({"role": "user", "content": user_input})

        # Update conversation history in prompt args
        respan_args["prompt"]["override_params"]["messages"] = conversation_history

        # Get agent response
        continue_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[],
            extra_body=respan_args,
        )

        # Handle any new tool calls
        new_tool_calls = continue_response.choices[0].message.tool_calls
        if new_tool_calls:
            conversation_history.append(continue_response.choices[0].message.model_dump())
            print("Calling tools...")
            for tool_call in new_tool_calls:
                tool_call_id = tool_call.id
                tool_call_result = None

                if tool_call.function.name == "search_places":
                    category = tool_call.function.arguments
                    search_result = search_places(**json.loads(category))
                    tool_call_result = search_result
                    print(f"Place Search: {search_result}")

                elif tool_call.function.name == "check_weather":
                    location = tool_call.function.arguments
                    weather_check = check_weather(**json.loads(location))
                    tool_call_result = weather_check
                    print(f"Weather Check: {weather_check}")

                elif tool_call.function.name == "find_hotels":
                    location = tool_call.function.arguments
                    hotel_finder = find_hotels(**json.loads(location))
                    tool_call_result = hotel_finder
                    print(f"Hotel Finder: {hotel_finder}")

                elif tool_call.function.name == "recommend_activities":
                    location = tool_call.function.arguments
                    activities = recommend_activities(**json.loads(location))
                    tool_call_result = activities
                    print(f"Activities: {activities}")

                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(tool_call_result),
                })

            # Update conversation history and get final response
            respan_args["prompt"]["override_params"]["messages"] = conversation_history

            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[],
                extra_body=respan_args,
            )
            agent_reply = final_response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": agent_reply})
            print(f"Assistant: {agent_reply}")
        else:
            agent_reply = continue_response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": agent_reply})
            print(f"Assistant: {agent_reply}")


def run_demo_agent(variables: dict, customer_id: str, interactive: bool = True):
    """Run the travel agent demo with Respan prompt management"""

    prompt_id = os.getenv("TRAVELING_AGENT_PROMPT_ID")  # Replace with actual prompt ID
    conversation_history = []

    # Respan prompt management configuration
    respan_args = {
        "prompt": {
            "prompt_id": prompt_id,
            "variables": variables,
            "override": True,
            "override_config": {"messages_override_mode": "append"},
            "override_params": (
                {"messages": conversation_history} if conversation_history else {}
            ),
        },
        "customer_identifier": customer_id,
        "metadata": {EVAL_RUN_METADATA_KEY: EVAL_RUN_ID},
    }

    response = client.chat.completions.create(
        model="gpt-4o",  # This will be overridden by prompt if override=True
        messages=[],  # Empty since we're using prompt management
        extra_body=respan_args,
    )

    # Track conversation history for multi-turn
    conversation_history.append(response.choices[0].message.model_dump())

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        print(f"Calling {len(tool_calls)} tools...")
        for tool_call in tool_calls:
            tool_call_id = tool_call.id
            tool_call_result = None

            if tool_call.function.name == "search_places":
                category = tool_call.function.arguments
                search_result = search_places(**json.loads(category))
                tool_call_result = search_result
                print(f"Place Search: {search_result}")

            elif tool_call.function.name == "check_weather":
                location = tool_call.function.arguments
                weather_check = check_weather(**json.loads(location))
                tool_call_result = weather_check
                print(f"Weather Check: {weather_check}")

            elif tool_call.function.name == "find_hotels":
                location = tool_call.function.arguments
                hotel_finder = find_hotels(**json.loads(location))
                tool_call_result = hotel_finder
                print(f"Hotel Finder: {hotel_finder}")

            elif tool_call.function.name == "recommend_activities":
                location = tool_call.function.arguments
                activities = recommend_activities(**json.loads(location))
                tool_call_result = activities
                print(f"Activities: {activities}")

            conversation_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(tool_call_result),
                }
            )

        # Get user input after showing search results
        if interactive and any(
            tc.function.name == "search_places" for tc in tool_calls
        ):
            user_choice = get_user_location_choice()
            conversation_history.append(
                {"role": "user", "content": f"I choose: {user_choice}"}
            )

        # Make follow-up request with updated conversation history
        respan_args["prompt"]["override_params"]["messages"] = conversation_history

        follow_up_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[],
            extra_body=respan_args,
        )
        assistant_response = follow_up_response.choices[0].message.content
        conversation_history.append(
            {"role": "assistant", "content": assistant_response}
        )

        # Continue conversation if interactive
        if interactive:
            _run_interactive_loop(assistant_response, conversation_history, respan_args)

    else:
        assistant_response = response.choices[0].message.content
        conversation_history.append(
            {"role": "assistant", "content": assistant_response}
        )

        # Continue conversation if interactive
        if interactive:
            _run_interactive_loop(assistant_response, conversation_history, respan_args)

    return assistant_response


def run_interactive_demo():
    """Run interactive demo with multiple customers"""
    print("=== Respan Multi-Modal Tool Evaluation Demo ===\n")

    # Demo customers with different scenarios
    customers = [
        {
            "id": "customer_001_sarah",
            "name": "Sarah (Adventure Seeker)",
            "category": "mountain",
            "has_image": True,
            "is_booking_hotel": True,
            "is_checking_weather": True,
        },
        {
            "id": "customer_002_mike",
            "name": "Mike (Beach Lover)",
            "category": "beach",
            "has_image": True,
            "is_booking_hotel": False,
            "is_checking_weather": False,
        },
    ]

    for i, customer in enumerate(customers, 1):
        print(f"\n{'='*60}")
        print(f"CUSTOMER {i}: {customer['name']}")
        print(f"Customer ID: {customer['id']}")
        print(
            f"Preferences: {customer['category']} trip, image: {customer['has_image']}, hotel: {customer['is_booking_hotel']}, weather: {customer['is_checking_weather']}"
        )
        print(f"{'='*60}")

        input(f"\nPress Enter to start {customer['name']}'s session...")

        try:
            # Create variables for prompt management
            variables = create_demo_variables(**customer)

            print(f"\nVariables: {list(variables.keys())}")
            print("\n" + "-" * 50)

            # Run the agent with this customer's ID
            response = run_demo_agent(variables, customer["id"], interactive=True)

            print(f"\n🎉 {customer['name']}'s trip planning complete!")
            print(f"Final response: {response}")

            if i < len(customers):
                input(f"\nPress Enter to continue to next customer...")

        except FileNotFoundError:
            print(f"Warning: Image file for {customer['category']} not found.")
        except Exception as e:
            print(f"Error for {customer['name']}: {e}")


# Demo usage
if __name__ == "__main__":
    run_interactive_demo()
