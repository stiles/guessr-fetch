import json
import pandas as pd
import os
from tqdm import tqdm

RAW_DATA_DIR = f"./data/leaderboard/raw_player_data"
STATS_OUTPUT = f"./data/leaderboard/geoguessr_players_statistics.json"

# List raw data files
raw_files = [os.path.join(RAW_DATA_DIR, f) for f in os.listdir(RAW_DATA_DIR) if f.endswith(".json")]

user_stats_list = []

# Parse the raw JSON files
for raw_file in tqdm(raw_files):
    try:
        with open(raw_file, "r") as f:
            json_data = json.loads(f.read())
        page_props = json_data.get("props", {}).get("pageProps", {})
        user_info = page_props.get("user", {})
        user_stats = page_props.get("userStats", {})
        user_extended = page_props.get("userExtendedStats", {})
        ratings = page_props.get("peakRatings", {})

        # Extended stats
        moving = user_extended.get("duels", {})
        no_moving = user_extended.get("duelsNoMove", {})
        nmpz = user_extended.get("duelsNmpz", {})
        all_duels = user_extended.get("duelsTotal", {})

        # Append stats
        user_stats_list.append(
            {
                "id": user_info.get("userId"),
                "nickname": user_info.get("nick"),
                "rating_overall": ratings.get("peakOverallRating"),
                "rating_nm_duels": ratings.get("peakGameModeRatings", {}).get("noMoveDuels"),
                "rating_nmpz_duels": ratings.get("peakGameModeRatings", {}).get("nmpzDuels"),
                "rating_standard_duels": ratings.get("peakGameModeRatings", {}).get("standardDuels"),
                "account_created": user_info.get("created"),
                "country": user_info.get("countryCode"),
                "verified": user_info.get("isVerified"),
                "games_played": user_stats.get("gamesPlayed"),
                "rounds_played": user_stats.get("roundsPlayed"),
                "avg_game_score": user_stats.get("averageGameScore"),
                "duels_games_played": user_stats.get("gamesPlayed"),
                "duels_moving_wins_pct": round(moving.get("winRatio", 0), 2),
                "duels_nm_wins_pct": round(no_moving.get("winRatio", 0), 2),
                "duels_nmpz_wins_pct": round(nmpz.get("winRatio", 0), 2),
                "duels_all_num_gamesPlayed": all_duels.get("numGamesPlayed"),
                "duels_all_avg_position": all_duels.get("avgPosition"),
                "duels_all_num_wins": all_duels.get("numWins"),
                "duels_all_win_ratio": round(all_duels.get("winRatio", 0), 2),
                "duels_all_avg_guess_distance": all_duels.get("avgGuessDistance"),
                "duels_all_num_guesses": all_duels.get("numGuesses"),
                "duels_all_num_flawlessWins": all_duels.get("numFlawlessWins"),
            }
        )
    except Exception as e:
        print(f"Error processing file {raw_file}: {e}")

# Save parsed stats to JSON
users_stats_df = pd.DataFrame(user_stats_list).sort_values('rating_overall', ascending=False)
users_stats_df.to_json(STATS_OUTPUT, indent=4, orient="records")
print(f"Player statistics saved to {STATS_OUTPUT}")
