# file: server/travel_time_tool.py

import logging
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

import httpx
import math

def register(mcp):

    GEO_API = "https://geocoding-api.open-meteo.com/v1/search"

    async def get_city_coords(city: str):
        """Return (lat, lon, name, country) using free Open-Meteo geocoding API."""
        params = {"name": city, "count": 1, "language": "en"}

        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(GEO_API, params=params, timeout=10)
                data = r.json()

                if "results" in data and data["results"]:
                    info = data["results"][0]
                    return {
                        "name": info["name"],
                        "lat": info["latitude"],
                        "lon": info["longitude"],
                        "country": info.get("country", "")
                    }
                return None
            except Exception:
                return None

    def haversine(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates (km)."""
        R = 6371  # Earth radius in km

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2)**2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # km

    def format_hours(hours: float) -> str:
        """Convert decimal hours to H hours M minutes."""
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m"

    @mcp.tool()
    async def travel_time(city1: str, city2: str) -> str:
        """
        Calculate travel times between two cities:
        ✈ Airplane
        🚗 Car
        🚶 Walking
        🚂 Train (estimated)
        """
        c1 = await get_city_coords(city1)
        if not c1:
            return f"❌ Could not find coordinates for `{city1}`."

        c2 = await get_city_coords(city2)
        if not c2:
            return f"❌ Could not find coordinates for `{city2}`."

        dist_km = haversine(c1["lat"], c1["lon"], c2["lat"], c2["lon"])

        # Travel speeds (typical averages)
        SPEED_AIRPLANE = 850      # km/h (commercial jet)
        SPEED_CAR = 80            # km/h (highway avg)
        SPEED_TRAIN = 100         # km/h (average fast train)
        SPEED_WALK = 5            # km/h (human walking)

        # Calculations
        t_plane  = format_hours(dist_km / SPEED_AIRPLANE)
        t_car    = format_hours(dist_km / SPEED_CAR)
        t_train  = format_hours(dist_km / SPEED_TRAIN)
        t_walk   = format_hours(dist_km / SPEED_WALK)

        return (
            f"🧭 **Travel Time Between Cities**\n"
            f"----------------------------------------------\n"
            f"🌆 **From:** {c1['name']}, {c1['country']}\n"
            f"🌆 **To:** {c2['name']}, {c2['country']}\n"
            f"🗺 **Distance:** {dist_km:,.2f} km\n\n"
            f"✈ **Airplane:** {t_plane}\n"
            f"🚗 **Car:** {t_car}\n"
            f"🚂 **Train (estimated):** {t_train}\n"
            f"🚶 **Walking:** {t_walk}\n"
        )

    return travel_time


# ---------------------- MANUAL TEST ----------------------
if __name__ == "__main__":
    import asyncio
    from mcp.server import FastMCP #type:ignore

    test = FastMCP("test_travel_tool")
    register(test)
    tool = test._tool_manager.list_tools()[0]

    print("--- 🧭 RUNNING TRAVEL TIME TEST ---")
    print(asyncio.run(tool.fn("Chennai", "Trichy")))
