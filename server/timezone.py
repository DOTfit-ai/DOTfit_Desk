# file: server/timezone.py
import logging
logging.getLogger("httpx").setLevel(logging.CRITICAL)
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

def register(mcp):

    GEO_API = "https://geocoding-api.open-meteo.com/v1/search"

    async def city_to_timezone(city: str) -> str | None:
        params = {"name": city, "count": 1, "language": "en"}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(GEO_API, params=params, timeout=10)
                data = r.json()
                if "results" in data and data["results"]:
                    return data["results"][0]["timezone"]
                return None
            except Exception:
                return None

    def parse_user_time(t: str) -> datetime | None:
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
        for f in formats:
            try:
                return datetime.strptime(t, f)
            except:
                continue
        return None

    def get_local_current_time(tz: str) -> datetime:
        """Get current time in any timezone WITHOUT external API."""
        return datetime.now(ZoneInfo(tz))

    async def resolve_timezone(input_str: str) -> str | None:
        zones = available_timezones()

        if input_str in zones:  # valid timezone
            return input_str

        return await city_to_timezone(input_str)

    @mcp.tool()
    async def timezone_convert(query: str) -> str:
        """
        Accepts input like:
        - "chennai to new york"
        - "tokyo to london 2025-05-01 12:30"
        - "mumbai to toronto"
        """

        if not query or " to " not in query.lower():
            return "❌ Format error.\nUse: timezone <from> to <to> [optional datetime]"

        # Split "from" and "to"
        from_part, rest = query.split(" to ", 1)

        tokens = rest.split()

        # If user included datetime → last tokens form time
        if len(tokens) > 2:
            to_part = " ".join(tokens[:2])  # allows two-word cities like "new york"
            time_str = " ".join(tokens[2:])
        else:
            to_part = rest.strip()
            time_str = None
        return await timezone_convert_internal(from_part, to_part, time_str)
    # Now call your original logic EXACTLY as-is
    async def timezone_convert_internal(from_place: str, to_place: str, time_str: str = None) -> str:
        from_tz = await resolve_timezone(from_place)
        to_tz = await resolve_timezone(to_place)

        if not from_tz:
            return f"❌ Could not detect timezone for `{from_place}`"
        if not to_tz:
            return f"❌ Could not detect timezone for `{to_place}`"

        # CASE 1: No time provided → use current local time
        if not time_str:
            dt = get_local_current_time(from_tz)

        # CASE 2: User provided datetime
        else:
            dt = parse_user_time(time_str)
            if not dt:
                return (
                    "❌ Invalid time format.\n"
                    "Use:\n"
                    "• YYYY-MM-DD\n"
                    "• YYYY-MM-DD HH:MM\n"
                    "• YYYY-MM-DD HH:MM:SS"
                )
            dt = dt.replace(tzinfo=ZoneInfo(from_tz))

        converted = dt.astimezone(ZoneInfo(to_tz))

        return (
            f"🕒 Time Zone Conversion\n"
            f"────────────────────────────\n"
            f"🌍 From           : `{from_place}` → `{from_tz}`\n"
            f"🎯 To             : `{to_place}` → `{to_tz}`\n"
            f"⏳ Original Time  : {dt.strftime('%Y-%m-%d %H:%M')}\n"
            f"➡️ Converted Time : {converted.strftime('%Y-%m-%d %H:%M')}"
        )

    



# # MANUAL TEST
# if __name__ == "__main__":
#     import asyncio
#     from mcp.server import FastMCP #type:ignore

#     test = FastMCP("test_timezone")
#     register(test)
#     tool = test._tool_manager.list_tools()[0]

#     print("--- ⏱ TEST NOW TIME ---")
#     print(asyncio.run(tool.fn("Chennai", "new york","2025-01-15")))