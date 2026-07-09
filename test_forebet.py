import asyncio
from parsers.forebet import forebet_parser

async def test():
    predictions = await forebet_parser.get_predictions()
    print(f"Found {len(predictions)} predictions")
    for p in predictions[:5]:
        print(f"{p['team_home']} vs {p['team_away']}: {p['prediction_home']}% - {p['prediction_draw']}% - {p['prediction_away']}%")

asyncio.run(test())
